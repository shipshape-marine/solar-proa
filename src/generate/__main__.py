import argparse
from pathlib import Path

from .generate import generate_model


def main():
    parser = argparse.ArgumentParser(description="Generate a Solar Proa model.")
    parser.add_argument("freecad_executable", type=Path, help="Path to the FreeCAD command-line executable.")
    parser.add_argument("config_path", type=Path, help="Path to the boat parameter JSON file.")
    parser.add_argument("output_dir", type=Path, help="Directory in which to create the timestamped output directory.")
    args = parser.parse_args()

    generated_paths = generate_model(args.freecad_executable, args.config_path, args.output_dir)

    for artifact, path in generated_paths.items():
        print(f"{artifact}: {path}")


if __name__ == "__main__":
    main()
