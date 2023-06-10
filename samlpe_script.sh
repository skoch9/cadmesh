#!/bin/bash
#SBATCH --time=1:00:00
#SBATCH --account=def-teseo
#SBATCH --job-name=step-process
#SBATCH --mem-per-cpu=16G
#SBATCH --cpus-per-task=1
#SBATCH --array=0-99

# Activate Python environment
source ~/scratch/madduri/cad/bin/activate

# Get the username for the path

# Define paths relative to the scratch directory
DATA_PATH="/home/madduri/scratch/madduri/Fusion360/segmentation/step/s2.0.1_extended_step/breps/step"
OUTPUT_PATH="/home/madduri/scratch/madduri/Fusion360/segmentation/yaml/s2.0.1_extended"
LOG_PATH="/home/madduri/scratch/madduri/Fusion360/segmentation/yaml/logs"
HDF5_PATH="/home/madduri/scratch/madduri/Fusion360/segmentation/hdf5"

BATCH_ID=$SLURM_ARRAY_TASK_ID  # BatchID is equal to the task id in the job array
JOB_ID=$SLURM_JOB_ID           # JobID from SLURM

# Define new path for this batch
BATCH_PATH="$DATA_PATH/batch_$BATCH_ID"
mkdir -p "$BATCH_PATH"
mv $(ls -1 "$DATA_PATH"/*.stp | sed -n "$((SLURM_ARRAY_TASK_ID*500+1)),$((SLURM_ARRAY_TASK_ID*500+500))p") "$BATCH_PATH"

# Conversion scripts
python cloud_conversion.py --input "$DATA_PATH" --output "$OUTPUT_PATH" --log "$LOG_PATH" --batchId "$BATCH_ID" --jobId "$JOB_ID" --hdf5_file "$HDF5_PATH"

## Delete processed files after the conversion
#rm -r "$BATCH_PATH"