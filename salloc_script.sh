#!/bin/bash

# Set the job and batch IDs
JOB_ID="job_$(date +'%Y%m%d%H%M%S')"
BATCH_ID="batch_$(date +'%Y%m%d%H%M%S')"

# Activate Python environment
echo "Activating Python environment..."
module load python/3.8.10
source ~/scratch/madduri/cad/bin/activate

# Define data path and set other paths relative to it
echo "Defining paths..."
DATA_PATH="/home/madduri/scratch/madduri/Fusion360/reconstruction/r1.0.1/reconstruction"
BASE_PATH=$(dirname "$DATA_PATH")

OUTPUT_PATH="$BASE_PATH/yaml/r1.0.1/${BATCH_ID}_${JOB_ID}"
LOG_PATH="$BASE_PATH/yaml/logs/${BATCH_ID}_${JOB_ID}"
HDF5_PATH="$BASE_PATH/hdf5"

mkdir -p "$OUTPUT_PATH"
mkdir -p "$LOG_PATH"
mkdir -p "$HDF5_PATH"

# Define new path for this batch
echo "Defining new path for this batch..."
BATCH_PATH="$DATA_PATH/$BATCH_ID"
mkdir -p "$BATCH_PATH"

# Get the list of files to be copied
echo "Getting the list of files to be copied..."
FILES_TO_COPY=$(find "$DATA_PATH" \( -name "*.stp" -or -name "*.step" \) | head -n 250)

# Check if files exist
if [ -z "$FILES_TO_COPY" ]
then
    echo "No files to copy for batch $BATCH_ID."
    exit 1
fi

# Move the files
echo "Moving the files..."
mv $FILES_TO_COPY "$BATCH_PATH"

# Conversion scripts
echo "Running conversion scripts..."
python3 cloud_conversion.py --input "$BATCH_PATH" --output "$OUTPUT_PATH" --log "$LOG_PATH" --batchId "$BATCH_ID" --jobId "$JOB_ID" --hdf5_file "$HDF5_PATH"

if [ $? -eq 0 ]
then
    echo "Conversion was successful. Deleting batch files and output directory..."
    rm -rf "$BATCH_PATH"
    rm -rf "$OUTPUT_PATH"
else
    echo "Some files were not converted successfully. Not deleting batch files or output directory."
fi

echo "Done!"
