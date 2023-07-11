import os
import cadmesh
import OCCUtils
import argparse
from Hda5_Converter import *
from pathlib import Path
import os
import glob
import shutil
import tempfile
# import get_files
# import multiprocessing


def process_files(success_files, models_folder, output_folder, batch_id, job_id):
    successful_conversions = []
    failed_conversions = []
    input_folder = Path(models_folder)
    output_folder_path = Path(output_folder)

    for item in success_files:
        try:
            output_folder_path.mkdir(parents=True, exist_ok=True)
            model_name = item[0].stem

            meshPath = input_folder / f"{model_name}_mesh"
            geometry_yaml_file_path = input_folder / f"{model_name}_geo.yaml"
            topology_yaml_file_path = input_folder / f"{model_name}_topo.yaml"
            stat_yaml_file_path = input_folder / f"{model_name}_stat.yaml"
            output_file = output_folder_path / f'{model_name}.hdf5'

            assert meshPath.exists()
            assert geometry_yaml_file_path.exists()
            assert topology_yaml_file_path.exists()
            assert stat_yaml_file_path.exists()

            geometry_data = load_dict_from_yaml(geometry_yaml_file_path)
            topology_data = load_dict_from_yaml(topology_yaml_file_path)
            stat_data = load_dict_from_yaml(stat_yaml_file_path)

            convert_data_to_hdf5(geometry_data, topology_data, stat_data, meshPath, output_file)

            successful_conversions.append(model_name)

            # delete files on success
            for file in [item[0], meshPath, geometry_yaml_file_path, topology_yaml_file_path, stat_yaml_file_path]:
                try:
                    if file.exists():
                        if file.is_dir():
                            shutil.rmtree(str(file))  # for directories
                        else:
                            os.remove(str(file))  # for files
                except OSError as e:
                    print(f"Error: {file} : {e.strerror}")

        except Exception as e:
            print(f"Conversion failed for model {model_name}. Error: {e}")
            failed_conversions.append(model_name)

    with open(f'successful_conversions_{job_id}_{batch_id}.txt', 'w') as f:
        for item in successful_conversions:
            f.write("%s\n" % item)

    with open(f'failed_conversions_{job_id}_{batch_id}.txt', 'w') as f:
        for item in failed_conversions:
            f.write("%s\n" % item)

    if len(failed_conversions) > 0:
        print(f"Some files failed conversion. Check 'failed_conversions_{job_id}_{batch_id}.txt' for details.")
        exit(1)
    else:
        print(f"All files successfully converted. Check 'successful_conversions_{job_id}_{batch_id}.txt' for details.")
        try:
            if input_folder.exists():
                shutil.rmtree(str(input_folder))  # Delete the models folder
        except OSError as e:
            print(f"Error: {input_folder} : {e.strerror}")
        exit(0)

def process_local_test():
    # Define data path and set other paths relative to it
    DATA_PATH="/Users/chandu/Workspace/GM/cadmesh/test_conversion/temp_step"
    BASE_PATH=os.path.dirname(DATA_PATH)

    # Set BatchID and JobID manually for local testing
    BATCH_ID = "0"  # replace with your batch id for testing
    JOB_ID = "1"   # replace with your job id for testing

    OUTPUT_PATH=os.path.join(BASE_PATH, f"yaml/batch_{BATCH_ID}_job_{JOB_ID}")
    LOG_PATH=os.path.join(BASE_PATH, f"yaml/logs/batch_{BATCH_ID}_job_{JOB_ID}")
    HDF5_PATH=os.path.join(BASE_PATH, "hdf5")

    # Create directories
    for dir in [OUTPUT_PATH, LOG_PATH, HDF5_PATH]:
        os.makedirs(dir, exist_ok=True)

    # Define new path for this batch
    BATCH_PATH=os.path.join(DATA_PATH, f"batch_{BATCH_ID}")
    os.makedirs(BATCH_PATH, exist_ok=True)

    # Get the list of files to be processed
    FILES_TO_PROCESS = glob.glob(os.path.join(DATA_PATH, "*.stp"))[:1]  # adjust as needed

    # Check if files exist
    if not FILES_TO_PROCESS:
        print(f"No files to process for batch {BATCH_ID}.")
        return

    # Write the list of files to a temporary text file
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
        for file in FILES_TO_PROCESS:
            temp_file.write(f"{file}\n")

    # Run the conversion scripts
    success, failed = cadmesh.utils.processing.process_step_files(temp_file.name, OUTPUT_PATH, LOG_PATH)
    process_files(success, OUTPUT_PATH, HDF5_PATH, BATCH_ID, JOB_ID)

    # Clean up temporary file
    os.remove(temp_file.name)

    print("Done!")

# def process_local_test():
#     # Define data path and set other paths relative to it
#     DATA_PATH="/Users/chandu/Workspace/GM/cadmesh/test_conversion/step_2"
#     BASE_PATH=os.path.dirname(DATA_PATH)
#
#     # Set BatchID and JobID manually for local testing
#     BATCH_ID = "0"  # replace with your batch id for testing
#     JOB_ID = "1"   # replace with your job id for testing
#
#     OUTPUT_PATH=os.path.join(BASE_PATH, f"yaml/batch_{BATCH_ID}_job_{JOB_ID}")
#     LOG_PATH=os.path.join(BASE_PATH, f"yaml/logs/batch_{BATCH_ID}_job_{JOB_ID}")
#     HDF5_PATH=os.path.join(BASE_PATH, "hdf5")
#     PROCESSED_FILES_PATH=os.path.join(BASE_PATH, "processed_files.txt")
#
#     # Create directories
#     for dir in [OUTPUT_PATH, LOG_PATH, HDF5_PATH]:
#         os.makedirs(dir, exist_ok=True)
#
#     # Get the list of files to be processed
#     # Temporary file for storing the list of files to process
#     temp_file_list = f"tmp_file_list_{BATCH_ID}.txt"
#
#     # Call the function to get the list of files
#     get_files(BATCH_ID, DATA_PATH, "*.stp", PROCESSED_FILES_PATH, temp_file_list)
#
#     # Read the list of files to process
#     with open(temp_file_list, 'r') as f:
#         FILES_TO_PROCESS = [line.strip() for line in f]
#
#     # Check if files exist
#     if not FILES_TO_PROCESS:
#         print(f"No files to process for batch {BATCH_ID}.")
#         return
#
#     # Run the conversion scripts
#     success, failed = cadmesh.utils.processing.process_step_files(temp_file_list, OUTPUT_PATH, LOG_PATH)
#     process_files(success, OUTPUT_PATH, HDF5_PATH, BATCH_ID, JOB_ID)
#
#     # Clean up temporary file
#     os.remove(temp_file_list)
#
#     print("Done!")
#
#
# def process_files_simultaneously(file_id):
#     DATA_PATH = "/Users/chandu/Workspace/GM/cadmesh/test_conversion/step_2"
#     BASE_PATH = os.path.dirname(DATA_PATH)
#     PROCESSED_FILES_PATH = os.path.join(BASE_PATH, "processed_files.txt")
#     temp_file_list = f"tmp_file_list_{file_id}.txt"
#
#     # call the function to get the list of files
#     get_files(file_id, DATA_PATH, "*.stp", PROCESSED_FILES_PATH, temp_file_list)
#
#     with open(temp_file_list, 'r') as f:
#         FILES_TO_PROCESS = [line.strip() for line in f]
#
#     print(f"Process {file_id} got {len(FILES_TO_PROCESS)} files")
#     os.remove(temp_file_list)
#
# def test_simultaneously_processing():
#     # number of parallel processes
#     num_processes = 10
#     pool = multiprocessing.Pool(processes=num_processes)
#
#     # process id's (0 to 9 in this case)
#     process_ids = range(num_processes)
#
#     # start all processes
#     pool.map(process_files_simultaneously, process_ids)
#
#     pool.close()
#     pool.join()

# if __name__ == '__main__':
#     process_local_test()
#
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Process STEP files in a directory.")
    parser.add_argument("--input", help="Path to the text file with the list of STEP files.")
    parser.add_argument("--output", help="Path to the directory where results will be saved.")
    parser.add_argument("--log", help="Path to the directory where logs will be saved.")
    parser.add_argument("--hdf5_file", help="Path to the HDF5 file where results will be saved.")
    parser.add_argument("--jobId", help="Job ID for this execution")
    parser.add_argument("--batchId", help="Batch ID for this execution")
    args = parser.parse_args()

    success, failed = cadmesh.utils.processing.process_step_files(args.input, args.output, args.log)

    process_files(success, args.output, args.hdf5_file, args.batchId, args.jobId)
#
