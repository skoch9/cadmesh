#!/bin/bash
#SBATCH --time=1:00:00
#SBATCH --account=def-teseo
#SBATCH --job-name=step-process-test
#SBATCH --mem-per-cpu=16G
#SBATCH --cpus-per-task=1

module load python/3.8.10
module load mpi4py/3.0.3

# Activate Python environment
source ~/scratch/projects/def-teseo/madduri/envs/cad/bin/activate

# Get the username for the path
USER_NAME=$USER

# Define paths relative to the scratch directory
DATA_PATH="/home/$USER_NAME/scratch/madduri/Fusion360/segmentation/step/s2.0.1_extended_step/breps/step"
OUTPUT_PATH="/home/$USER_NAME/scratch/madduri/Fusion360/segmentation/yaml/s2.0.1_extended"
LOG_PATH="/home/$USER_NAME/scratch/madduri/Fusion360/segmentation/yaml/logs"

# Get the batch of files this task should process
FILES=($(ls -1 "$DATA_PATH"/*.stp | sed -n "1,225p"))  # Only process first 225 files

for FILE in "${FILES[@]}"; do
    if [[ -f "$FILE" ]]; then  # Only process if file exists
        python data_conversion.py --input "$FILE" --output "$OUTPUT_PATH" --log "$LOG_PATH"
        # Add conversion too yaml to hdf5 here
    fi
done
