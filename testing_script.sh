#!/bin/bash

# Activate Python environment
echo "Activating Python environment..."
source ~/scratch/madduri/cad/bin/activate

# Define paths relative to the scratch directory
echo "Defining paths..."
DATA_PATH="/home/madduri/scratch/madduri/Fusion360/segmentation/step/s2.0.1_extended_step/breps/step"
OUTPUT_PATH="/home/madduri/scratch/madduri/Fusion360/segmentation/yaml/s2.0.1_extended"
LOG_PATH="/home/madduri/scratch/madduri/Fusion360/segmentation/yaml/logs"
HDF5_PATH="/home/madduri/scratch/madduri/Fusion360/segmentation/hdf5"

BATCH_ID=0  # For interactive testing, we manually set BatchID
JOB_ID="TestJob"  # Set a test JobID

# Define new path for this batch
echo "Defining new path for this batch..."
BATCH_PATH="$DATA_PATH/batch_$BATCH_ID"
mkdir -p "$BATCH_PATH"

# Get the list of files to be copied (only 50 files)
echo "Getting the list of files to be copied..."
FILES_TO_COPY=$(ls -1 "$DATA_PATH"/*.stp "$DATA_PATH"/*.step 2> /dev/null | sed -n "$((BATCH_ID*50+1)),$((BATCH_ID*50+50))p")

# Check if files exist
if [ -z "$FILES_TO_COPY" ]
then
    echo "No files to copy for batch $BATCH_ID."
    exit 1
fi

# Copy the files
echo "Copying the files..."
cp $FILES_TO_COPY "$BATCH_PATH"

# Conversion scripts
echo "Running conversion scripts..."
python cloud_conversion.py --input "$BATCH_PATH" --output "$OUTPUT_PATH" --log "$LOG_PATH" --batchId "$BATCH_ID" --jobId "$JOB_ID" --hdf5_file "$HDF5_PATH"

echo "Done!"

