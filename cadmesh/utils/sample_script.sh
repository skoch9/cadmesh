#!/bin/bash
#SBATCH --time=00:10:00
#SBATCH --account=def-teseo
#SBATCH --job-name=step-process
#SBATCH --mem-per-cpu=4G
#SBATCH --cpus-per-task=4
#SBATCH --array=0-4%5

module load python/3.9
module load mpi4py/3.0.3

DATA_PATH="$SCRATCH/madduri/Fusion360/segmentation/step/s2.0.1_extended_step/breps/step"
OUTPUT_PATH="$SCRATCH/madduri/Fusion360/segmentation/yaml/s2.0.1_extended"
LOG_PATH="$SCRATCH/madduri/Fusion360/segmentation/yaml/logs"

# Get the batch of files this task should process
FILES=($(ls -1 "$DATA_PATH" | sed -n "$((SLURM_ARRAY_TASK_ID*100+1)),$((SLURM_ARRAY_TASK_ID*100+100))p"))

# Activate your Python environment
source ~/envs/cad/bin/activate

for FILE in "${FILES[@]}"; do
    FILE_PATH="$DATA_PATH/$FILE"
    mpiexec --oversubscribe -np $SLURM_CPUS_PER_TASK python data_conversion.py --input "$FILE_PATH" --output "$OUTPUT_PATH" --log "$LOG_PATH"
done

