import sys
import glob

# Get the task id, directory and file pattern as command line arguments
task_id = int(sys.argv[1])
directory = sys.argv[2]
pattern = sys.argv[3]

# Get all files matching the pattern
all_files = sorted(glob.glob(f"{directory}/{pattern}"))

# Calculate start and end indices based on task id
start = task_id * 500
end = min((start + 500), len(all_files)) # ensures 'end' doesn't exceed length of 'all_files'

# Select the files for this task
files_to_process = all_files[start:end]

# Print the files to standard output, one per line
for file in files_to_process:
    print(file)
