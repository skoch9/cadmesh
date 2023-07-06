#!/bin/bash
#SBATCH --time=2:00:00
#SBATCH --account=def-teseo
#SBATCH --job-name=step-process
#SBATCH --mem-per-cpu=32G
#SBATCH --cpus-per-task=4
#SBATCH --array=0-87

# Activate Python environment
echo "Activating Python environment..."
module load python/3.8.10
source ~/scratch/madduri/cad/bin/activate

if [ $? -ne 0 ]
then
    echo "Python environment could not be activated."
    exit 1
fi

# Define data path and set other paths relative to it
echo "Defining paths..."
DATA_PATH="/home/madduri/scratch/Fusion360/s2.0.1_extended_step/breps/step"

BASE_PATH=$(dirname "$DATA_PATH")

BATCH_ID=$SLURM_ARRAY_TASK_ID  # BatchID is equal to the task id in the job array
JOB_ID=$SLURM_JOB_ID           # JobID from SLURM

OUTPUT_PATH="$BASE_PATH/yaml/batch_${BATCH_ID}_job_${JOB_ID}"
LOG_PATH="$BASE_PATH/yaml/logs/batch_${BATCH_ID}_job_${JOB_ID}"
HDF5_PATH="$BASE_PATH/hdf5"

# Create directories
for dir in "$OUTPUT_PATH" "$LOG_PATH" "$HDF5_PATH"
do
    mkdir -p "$dir"
    if [ ! -d "$dir" ]
    then
        echo "Directory $dir could not be created."
        exit 1
    fi
done

# Define new path for this batch
echo "Defining new path for this batch..."
BATCH_PATH="$DATA_PATH/batch_$BATCH_ID"
mkdir -p "$BATCH_PATH"

if [ ! -d "$BATCH_PATH" ]
then
    echo "Batch directory could not be created."
    exit 1
fi

# Get the list of files to be processed
echo "Getting the list of files to be processed..."
FILES_TO_PROCESS=$(ls -1 "$DATA_PATH"/*.stp | sed -n "$((SLURM_ARRAY_TASK_ID*500+1)),$((SLURM_ARRAY_TASK_ID*500+500))p")

# Check if files exist
if [ -z "$FILES_TO_PROCESS" ]
then
    echo "No files to process for batch $BATCH_ID."
    exit 1
fi

# Conversion scripts
echo "Running conversion scripts..."
# Assuming your python script can take a list of files
python cloud_conversion.py --input "$FILES_TO_PROCESS" --output "$OUTPUT_PATH" --log "$LOG_PATH" --batchId "$BATCH_ID" --jobId "$JOB_ID" --hdf5_file "$HDF5_PATH"


echo "Done!"