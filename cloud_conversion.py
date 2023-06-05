import cadmesh
import OCCUtils
import argparse


if __name__ == '__main__':
    input_dir = "/Users/chandu/Workspace/GM/cadmesh/step_2"
    output_dir = "/Users/chandu/Workspace/GM/cadmesh/converted_step2"
    log_dir = "/Users/chandu/Workspace/GM/cadmesh/converted_logs2"

    parser = argparse.ArgumentParser(description="Process STEP files in a directory.")
    parser.add_argument("--input", help="Path to the directory with STEP files.")
    parser.add_argument("--output", help="Path to the directory where results will be saved.")
    parser.add_argument("--log", help="Path to the directory where logs will be saved.")
    parser.add_argument("--file_pattern", default="*.step", help="Pattern to match STEP files.")
    parser.add_argument("--file_range", nargs=2, type=int, default=[0, -1], help="Range of files to process.")

    args = parser.parse_args()

    cadmesh.utils.processing.process_step_folder(args.input, args.output, args.log, args.file_pattern, args.file_range)