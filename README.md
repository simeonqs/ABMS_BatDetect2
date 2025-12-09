# README associated with the BatDetect2 pipeline for ABMS

The pipeline was set-up on UCloud using an Ubuntu Virtual Machine with CUDA 
(using uc-a10-h). BatDetect will run on most systems, including ones without
GPU. Most steps will be exactly the same, although commands assume a Linux
system.

There are three scripts:

1) `setup_ucloud.txt` contains all steps to set up the pipeline
2) `process_all.py` contains the full pipeline and can be called using the 
notes in `setup_ucloud.txt`
3) `summarise_files_per_directory.sh` can be run as bash script to create a 
directory tree of all files on ERDA

For questions contact `simeonqs@hotmail.com`
