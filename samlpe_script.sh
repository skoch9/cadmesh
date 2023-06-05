#!/bin/bash
#SBATCH --time=1:00:00
#SBATCH --account=def-teseo
#SBATCH --job-name=step-process-test
#SBATCH --mem-per-cpu=16G
#SBATCH --cpus-per-task=1


# Activate Python environment
source ~/scratch/madduri/cad/bin/activate

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
        echo "Processing $FILE"
        echo "Output path: $OUTPUT_PATH"
        echo "Log path: $LOG_PATH"
        python cloud_conversion.py --input "$FILE" --output "$OUTPUT_PATH" --log "$LOG_PATH"
    fi
done
