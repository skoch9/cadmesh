#!/bin/bash
#SBATCH --time=00:30:00
#SBATCH --account=def-someuser
#SBATCH --job-name=step-process
#SBATCH --mem-per-cpu=4G
#SBATCH --cpus-per-task=1
#SBATCH --array=0-4

module load python/3.7.0
module load mpi4py/3.0.3

# Get the username for the path
USER_NAME=$USER

# Define paths relative to the scratch directory
DATA_PATH="/scratch/$USER_NAME/Fusion360/segmentation/step/s2.0.1_extended_step/breps/step"
OUTPUT_PATH="/scratch/$USER_NAME/Fusion360/segmentation/yaml/s2.0.1_extended"
LOG_PATH="/scratch/$USER_NAME/Fusion360/segmentation/yaml/logs"

# Get the batch of files this task should process
FILES=($(ls -1 "$DATA_PATH"/*.stp | sed -n "$((SLURM_ARRAY_TASK_ID*100+1)),$((SLURM_ARRAY_TASK_ID*100+100))p"))

for FILE in "${FILES[@]}"; do
    mpiexec -np 4 python your_script.py --input "$FILE" --output "$OUTPUT_PATH" --log "$LOG_PATH"
done
