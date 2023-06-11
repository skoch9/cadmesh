#!/bin/bash
#SBATCH --time=2:00:00
#SBATCH --account=def-teseo
#SBATCH --job-name=step-process
#SBATCH --mem-per-cpu=32G
#SBATCH --cpus-per-task=2
#SBATCH --array=0-99


# Activate Python environment
echo "Activating Python environment..."
module load python/3.8.10
source ~/scratch/madduri/cad/bin/activate

# Define paths relative to the scratch directory
echo "Defining paths..."
DATA_PATH="/home/madduri/scratch/madduri/Fusion360/segmentation/step/s2.0.1_extended_step/breps/step"
OUTPUT_PATH="/home/madduri/scratch/madduri/Fusion360/segmentation/yaml/s2.0.1_extended"
LOG_PATH="/home/madduri/scratch/madduri/Fusion360/segmentation/yaml/logs"
HDF5_PATH="/home/madduri/scratch/madduri/Fusion360/segmentation/hdf5"

BATCH_ID=$SLURM_ARRAY_TASK_ID  # BatchID is equal to the task id in the job array
JOB_ID=$SLURM_JOB_ID           # JobID from SLURM

# Define new path for this batch
echo "Defining new path for this batch..."
BATCH_PATH="$DATA_PATH/batch_$BATCH_ID"
mkdir -p "$BATCH_PATH"

# Get the list of files to be copied
echo "Getting the list of files to be copied..."
FILES_TO_COPY=$(ls -1 "$DATA_PATH"/*.stp | sed -n "$((SLURM_ARRAY_TASK_ID*500+1)),$((SLURM_ARRAY_TASK_ID*500+500))p")

# Check if files exist
if [ -z "$FILES_TO_COPY" ]
then
    echo "No files to copy for batch $BATCH_ID."
    exit 1
fi

# Copy the files
echo "Moving the files..."
mv $FILES_TO_COPY "$BATCH_PATH"


# Conversion scripts
echo "Running conversion scripts..."
python cloud_conversion.py --input "$BATCH_PATH" --output "$OUTPUT_PATH" --log "$LOG_PATH" --batchId "$BATCH_ID" --jobId "$JOB_ID" --hdf5_file "$HDF5_PATH"

if [ $? -eq 0 ]
then
    echo "Deleting batch files..."
    rm -rf "$BATCH_PATH"
else
    echo "Some files were not converted successfully. Not deleting batch files."
fi

echo "Done!"