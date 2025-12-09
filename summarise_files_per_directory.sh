#!/bin/bash

# Output file
outfile=~/Desktop/files_abms.txt

# Target directory
base_dir="/run/user/1426675883/gvfs/sftp:host=io.erda.au.dk,port=2222/Acoustics/storage/abms/2025"

# Function to recursively print tree with file counts per extension
summarise_dir() {
    local dir="$1"
    local indent="$2"

    echo "${indent}$(basename "$dir")/" >> "$outfile"

    # Count files by extension
    find "$dir" -maxdepth 1 -type f | sed -n 's/.*\.//p' | sort | uniq -c | while read count ext; do
        echo "${indent}  $count .$ext files" >> "$outfile"
    done

    # Recurse into subdirectories
    find "$dir" -mindepth 1 -maxdepth 1 -type d | while read subdir; do
        summarise_dir "$subdir" "  $indent"
    done
}

# Start from base directory
echo "Summary of $base_dir" > "$outfile"
summarise_dir "$base_dir" ""
