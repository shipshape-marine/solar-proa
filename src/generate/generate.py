from pathlib import Path
import sys
import os
import json
import math
import subprocess
import trimesh
import numpy as np
from datetime import datetime, timezone


def generate_model(freecad_executable: Path, config_path: Path, output_dir: Path, color=True) -> dict[str, Path]:
    freecad_executable = Path(freecad_executable)
    config_path = Path(config_path)
    output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    build_script = Path(__file__).with_name("build.py")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_dir = output_dir / timestamp
    run_dir.mkdir(parents=True, exist_ok=False)

    # invoke build script with freecad headless
    # generates fcstd and npz file
    subprocess.run(
        [
            str(freecad_executable),
            str(build_script),
            "--pass",
            str(config_path),
            str(run_dir)
        ],
        check=True
    )

    # verify that the files exist
    with config_path.open("r", encoding="utf-8") as parameter_file:
        parameters = json.load(parameter_file)
    boat = parameters["boat_name"]
    configuration = parameters["configuration_name"]

    fcstd_path = run_dir / f"{boat}.{configuration}.design.FCStd"
    npz_path = run_dir / f"{boat}.{configuration}.npz"
    if not fcstd_path.is_file():
        raise RuntimeError(f"FreeCAD did not create: {fcstd_path}")

    if not npz_path.is_file():
        raise RuntimeError(f"FreeCAD did not create: {npz_path}")

    # create glb file
    glb_path = run_dir / f"{boat}.{configuration}.glb"
    glb_from_npz(npz_path, glb_path)

    if not glb_path.is_file():
        raise RuntimeError(f"Trimesh did not create: {glb_path}")

    return {
        "fcstd": fcstd_path,
        "geometry": npz_path,
        "glb": glb_path,
    }

    




def glb_from_npz(npz_path: str, glb_path: str) -> None:
    npz_path = Path(npz_path)
    glb_path = Path(glb_path)

    with np.load(npz_path, allow_pickle=False) as geometry:
        vertices = geometry["display_vertices"]
        faces = geometry["display_faces"]

    mesh = trimesh.Trimesh(
        vertices=vertices,
        faces=faces,
        process=False,
    )

    # axis correction for glb
    rotation = trimesh.transformations.rotation_matrix(
        np.radians(-90.0),
        [1.0, 0.0, 0.0],
    )

    mesh.apply_transform(rotation)
    mesh.export(glb_path, file_type="glb")


