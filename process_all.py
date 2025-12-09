# Import modules

import os
import zipfile
import subprocess
import soundfile as sf
import paramiko
from pathlib import Path
from stat import S_ISDIR
import sys

# Paths
HOST_ALIAS = 'io.erda.au.dk'       # must match Host in ~/.ssh/config
REMOTE_ROOT = '/Acoustics/storage/abms/2025/slovakia'
DATA_DIR = Path.home() / 'data'
RESULTS_DIR = Path.home() / 'results'


print("Starting...")

# Determine batdetect2 path
LOCAL_BIN = Path.home() / '.local/bin/batdetect2'
if not LOCAL_BIN.exists():
    print(f"❌ Cannot find batdetect2 at {LOCAL_BIN}")
    sys.exit(1)
BATDETECT2 = str(LOCAL_BIN)

# Make sure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Function to check if wav file can be opened
def is_valid_wav(path):
    """Check if wav file can be opened."""
    try:
        with sf.SoundFile(path) as f:
            _ = len(f)
        return True
    except Exception:
        return False

# Function to download wav files using sftp
def download_wavs(sftp, remote_dir, local_dir):
    """Recursively download wav files from remote_dir into local_dir."""
    for item in sftp.listdir_attr(remote_dir):
        rpath = f"{remote_dir}/{item.filename}"
        lpath = local_dir / item.filename
        if S_ISDIR(item.st_mode):
            lpath.mkdir(exist_ok=True)
            download_wavs(sftp, rpath, lpath)
        elif item.filename.lower().endswith('.wav'):
            sftp.get(rpath, str(lpath))

# Function to list all subdirectories with wav files
def walk_remote(sftp, remote_dir):
    """Yield (root, dirs) like os.walk but for remote SFTP."""
    dirs = []
    for item in sftp.listdir_attr(remote_dir):
        if S_ISDIR(item.st_mode):
            dirs.append(item.filename)
    yield remote_dir, dirs
    for d in dirs:
        new_path = f"{remote_dir}/{d}"
        yield from walk_remote(sftp, new_path)

# Connect using sftp
ssh_config = paramiko.SSHConfig()
with open(os.path.expanduser("~/.ssh/config")) as f:
    ssh_config.parse(f)

cfg = ssh_config.lookup(HOST_ALIAS)
hostname = cfg.get("hostname", HOST_ALIAS)
username = cfg.get("user", os.getenv("USER"))
port = int(cfg.get("port", 22))
key_filename = cfg.get("identityfile",
                       [str(Path.home() / ".ssh/id_ed25519")])[0]

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(
    hostname=hostname,
    port=port,
    username=username,
    key_filename=key_filename,
)
sftp = client.open_sftp()
print("✅ Connected via ssh_config")

# Walk through remote directories (only focus on ones with MU in the name, 
## these are the ones with ultrasonic files)
for root, dirs in walk_remote(sftp, REMOTE_ROOT):
    for d in dirs:
        if 'MU' not in d:
            continue

        # Take the last four parts of the path and make a new folder name
        remote_folder = f"{root}/{d}"
        parts = Path(remote_folder).parts
        if len(parts) < 4:
            continue
        deployment_name = '_'.join(parts[-3:])

        # Skip if it already exists in the data directory
        local_data_folder = DATA_DIR / deployment_name
        if local_data_folder.exists():
            print(f"⏭️  Skipping {deployment_name}, already exists.")
            continue

        # Otherwise, make the folder and download all wavs
        local_data_folder.mkdir(parents=True, exist_ok=True)

        print(f"⬇️  Downloading wavs for {deployment_name}...")
        download_wavs(sftp, remote_folder, local_data_folder)

        for wav in local_data_folder.rglob('*.wav'):
            if not is_valid_wav(wav):
                print(f"⚠️ Invalid wav removed: {wav}")
                wav.unlink()
  
        # When finished, make a results folder and run BatDetect2
        local_results_folder = RESULTS_DIR / deployment_name
        local_results_folder.mkdir(parents=True, exist_ok=True)

        print(f"🎧 Running batdetect2 for {deployment_name}...")
        subprocess.run([
            BATDETECT2,
            'detect',
            str(local_data_folder),
            str(local_results_folder),
            '0.1'
        ], check=True)

        # When finished, zip the results and delete the unzipped folder
        zip_path = RESULTS_DIR / f"{deployment_name}.zip"
        print(f"📦 Zipping results: {zip_path}")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in local_results_folder.rglob('*'):
                zf.write(f, f.relative_to(local_results_folder))

        for wav in local_data_folder.rglob('*.wav'):
            wav.unlink()
        print(f"🧹 Cleaned wavs for {deployment_name}")

# When no more folders are to be done, close everything and report
sftp.close()
client.close()

print("Finished!")

