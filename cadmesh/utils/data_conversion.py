from processing import process_step_folder
import os


def main(start_index, end_index):
    # Get the username for the path
    user_name = os.environ['USER']

    # Define paths relative to the scratch directory
    data_path = f"/scratch/{user_name}/Fusion360/segmentation/step/s2.0.1_extended_step/breps/step"
    output_path = f"/scratch/{user_name}/Fusion360/segmentation/yaml/s2.0.1_extended"
    log_path = f"/scratch/{user_name}/Fusion360/segmentation/yaml/logs"

    # Make sure the output and log directories exist
    os.makedirs(output_path, exist_ok=True)
    os.makedirs(log_path, exist_ok=True)

    # Get a sorted list of all files
    all_files = sorted(os.listdir(data_path))

    # Determine which files this job should process based on the start and end index
    my_files = all_files[start_index:end_index]

    # Run the processing function for the selected files
    process_step_folder(data_path=my_files, output_path=output_path, log_path=log_path)


if __name__ == "__main__":
    start_index = int(os.getenv('SLURM_ARRAY_TASK_ID')) * 100
    end_index = start_index + 100
    main(start_index, end_index)