#!/bin/bash
#SBATCH --time=2:00:00
#SBATCH --account=def-teseo
#SBATCH --job-name=step-process
#SBATCH --mem-per-cpu=32G
#SBATCH --cpus-per-task=4
#SBATCH --array=0-100

# Activate Python environment
echo "Activating Python environment..."
module load python/3.8.10
source ~/scratch/madduri/cad/bin/activate

# Define data path and set other paths relative to it
echo "Defining paths..."
DATA_PATH="/home/madduri/scratch/Fusion360/s2.0.1_extended_step/breps/step"

BASE_PATH=$(dirname "$DATA_PATH")

BATCH_ID=$SLURM_ARRAY_TASK_ID  # BatchID is equal to the task id in the job array
JOB_ID=$SLURM_JOB_ID           # JobID from SLURM

OUTPUT_PATH="$BASE_PATH/yaml/batch_${BATCH_ID}_job_${JOB_ID}"
LOG_PATH="$BASE_PATH/yaml/logs/batch_${BATCH_ID}_job_${JOB_ID}"
HDF5_PATH="$BASE_PATH/hdf5"

mkdir -p "$OUTPUT_PATH"
mkdir -p "$LOG_PATH"
mkdir -p "$HDF5_PATH"

# Define new path for this batch
echo "Defining new path for this batch..."
BATCH_PATH="$DATA_PATH/batch_$BATCH_ID"
mkdir -p "$BATCH_PATH"

# Get the list of files to be copied
echo "Getting the list of files to be copied..."
FILES_TO_COPY=$(find "$DATA_PATH" \( -name "*.stp" -or -name "*.step" \) | sed -n "$((SLURM_ARRAY_TASK_ID*500+1)),$((SLURM_ARRAY_TASK_ID*500+500))p")

# Check if files exist
if [ -z "$FILES_TO_COPY" ]
then
    echo "No files to copy for batch $BATCH_ID."
    exit 1
fi

# Move the files
echo "Moving the files..."
IFS=$'\n'
for file in $FILES_TO_COPY
do
    mv "$file" "$BATCH_PATH"
    if [ $? -ne 0 ]
    then
        echo "File $file was not moved successfully for batch $BATCH_ID."
        exit 1
    fi
done
unset IFS

# Conversion scripts
echo "Running conversion scripts..."
python cloud_conversion.py --input "$BATCH_PATH" --output "$OUTPUT_PATH" --log "$LOG_PATH" --batchId "$BATCH_ID" --jobId "$JOB_ID" --hdf5_file "$HDF5_PATH"

if [ $? -eq 0 ]
then
    echo "Conversion was successful. Deleting batch files and output directory..."
    rm -rf "$BATCH_PATH"
    rm -rf "$OUTPUT_PATH"
else
    echo "Some files were not converted successfully. Not deleting batch files or output directory."
fi

echo "Done!"
