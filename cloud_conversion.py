import os
import cadmesh
import OCCUtils
import argparse
from Hda5_Converter import *
from pathlib import Path

# Assuming that the methods load_dict_from_yaml and convert_data_to_hdf5 are already defined
# from your_module import load_dict_from_yaml, convert_data_to_hdf5

def process_files(success, models_folder, output_folder):
    successful_conversions = []
    failed_conversions = []
    input_folder = Path(models_folder)
    output_folder_path = Path(output_folder)

    for item in success:
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
        except Exception as e:
            print(f"Conversion failed for model {model_name}. Error: {e}")
            failed_conversions.append(model_name)

    with open('successful_conversions.txt', 'w') as f:
        for item in successful_conversions:
            f.write("%s\n" % item)

    with open('failed_conversions.txt', 'w') as f:
        for item in failed_conversions:
            f.write("%s\n" % item)

if __name__ == '__main__':
    # parser = argparse.ArgumentParser(description="Process STEP files in a directory.")
    # parser.add_argument("--input", help="Path to the directory with STEP files.")
    # parser.add_argument("--output", help="Path to the directory where results will be saved.")
    # parser.add_argument("--log", help="Path to the directory where logs will be saved.")
    # parser.add_argument("--hdf5_file", help="Path to the HDF5 file where results will be saved.")
    # parser.add_argument("--file_pattern", default="*.stp", help="Pattern to match STEP files.")
    # parser.add_argument("--file_range", nargs=2, type=int, default=[0, 200], help="Range of files to process.")
    # args = parser.parse_args()

    #success, failed = cadmesh.utils.processing.process_step_folder(args.input, args.output, args.log, args.file_pattern, args.file_range)

    input_dir = "/Users/chandu/Workspace/GM/cadmesh/step_2"
    output_dir = "/Users/chandu/Workspace/GM/cadmesh/converted_step2"
    log_dir = "/Users/chandu/Workspace/GM/cadmesh/converted_logs2"
    hdf5_output_dir = "/Users/chandu/Workspace/GM/cadmesh/hdf5_step2"

    success, failed = cadmesh.utils.processing.process_step_folder(input_dir, output_dir, log_dir, "*.stp", [0, 200])

    process_files(success, output_dir, hdf5_output_dir)