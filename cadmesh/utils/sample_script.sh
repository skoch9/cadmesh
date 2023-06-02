#!/bin/bash
#SBATCH --time=00:30:00
#SBATCH --account=def-teseo
#SBATCH --job-name=step-process
#SBATCH --mem-per-cpu=4G
#SBATCH --cpus-per-task=1
#SBATCH --array=0-4

module load python/3.9.0
module load mpi4py/3.0.3

# Activate Python environment
source projects/def-teseo/madduri/envs/cad/bin/activate

# Get the username for the path
USER_NAME=$USER

# Define paths relative to the scratch directory
DATA_PATH="/home/$USER_NAME/scratch/madduri/Fusion360/segmentation/step/s2.0.1_extended_step/breps/step"
OUTPUT_PATH="/home/$USER_NAME/scratch/madduri/Fusion360/segmentation/yaml/s2.0.1_extended"
LOG_PATH="/home/$USER_NAME/scratch/madduri/Fusion360/segmentation/yaml/logs"

# Get the batch of files this task should process
FILES=($(ls -1 "$DATA_PATH"/*.stp | sed -n "$((SLURM_ARRAY_TASK_ID*100+1)),$((SLURM_ARRAY_TASK_ID*100+100))p"))

for FILE in "${FILES[@]}"; do
    mpiexec -np 4 python data_conversion.py --input "$FILE" --output "$OUTPUT_PATH" --log "$LOG_PATH"
done
