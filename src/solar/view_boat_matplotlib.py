"""Display a complete extracted Solar Proa mesh with Matplotlib.

Example:

    python src/solar/view_boat_matplotlib.py \
        artifact/rp2.closehaul.mesh.npz

The mesh cache is produced by ``extract_boat_mesh.py``.  FreeCAD is not needed
to run this viewer.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np


def load_mesh_bundle(
    mesh_path: Path,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """Load and validate an extracted mesh and its adjacent manifest."""
    manifest_path = mesh_path.with_suffix(".json")
    if not mesh_path.is_file():
        raise FileNotFoundError(mesh_path)
    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)

    with np.load(mesh_path, allow_pickle=False) as bundle:
        vertices = np.asarray(bundle["vertices"], dtype=np.float32)
        faces = np.asarray(bundle["faces"], dtype=np.int64)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if vertices.ndim != 2 or vertices.shape[1] != 3:
        raise ValueError("vertices must have shape (N, 3)")
    if faces.ndim != 2 or faces.shape[1] != 3:
        raise ValueError("faces must have shape (M, 3)")
    if not np.isfinite(vertices).all():
        raise ValueError("mesh contains non-finite vertices")
    if len(faces) and (faces.min() < 0 or faces.max() >= len(vertices)):
        raise ValueError("mesh contains invalid triangle indices")

    return vertices, faces, manifest


def colour_key(record: dict) -> tuple[float, float, float, float]:
    """Return a hashable RGBA colour for collection batching."""
    colour = record.get("colour", [0.55, 0.59, 0.62, 1.0])
    return tuple(float(channel) for channel in colour)


def grouped_faces(faces: np.ndarray, manifest: dict) -> dict:
    """Batch object faces by colour while retaining one complete boat scene."""
    groups: dict[tuple[float, float, float, float], list[np.ndarray]] = defaultdict(list)
    for record in manifest["objects"]:
        start = int(record["face_start"])
        stop = start + int(record["face_count"])
        groups[colour_key(record)].append(faces[start:stop])

    return {
        colour: np.concatenate(blocks, axis=0)
        for colour, blocks in groups.items()
        if blocks
    }


def set_equal_view(ax, vertices: np.ndarray) -> None:
    """Fit the complete model with equal physical scale on all axes."""
    minimum = vertices.min(axis=0)
    maximum = vertices.max(axis=0)
    centre = (minimum + maximum) / 2.0
    spans = maximum - minimum
    span = max(float(spans.max()), 1e-6)
    padding = span * 0.04
    half = span / 2.0 + padding

    ax.set_xlim(centre[0] - half, centre[0] + half)
    ax.set_ylim(centre[1] - half, centre[1] + half)
    ax.set_zlim(centre[2] - half, centre[2] + half)
    ax.set_box_aspect((1.0, 1.0, 1.0))


def render_boat(
    mesh_path: Path,
    save_path: Path | None = None,
    show: bool = True,
) -> None:
    """Render the extracted complete boat and optionally save a validation image."""
    vertices, faces, manifest = load_mesh_bundle(mesh_path)
    groups = grouped_faces(faces, manifest)

    figure = plt.figure(figsize=(13, 8))
    ax = figure.add_subplot(111, projection="3d")
    figure.subplots_adjust(left=0.02, right=0.98, bottom=0.04, top=0.91)

    for colour, indices in groups.items():
        triangles = vertices[indices]
        collection = Poly3DCollection(
            triangles,
            facecolors=[colour],
            edgecolors="none",
            linewidths=0.0,
            alpha=colour[3],
            zsort="average",
        )
        ax.add_collection3d(collection)

    set_equal_view(ax, vertices)
    ax.set_xlabel("X: starboard (m)")
    ax.set_ylabel("Y: model forward (m)")
    ax.set_zlabel("Z: up (m)")
    ax.set_proj_type("persp")
    ax.view_init(elev=24.0, azim=-58.0)

    stats = manifest["statistics"]
    source_name = Path(manifest["source"]).name
    ax.set_title(
        f"{source_name}\n"
        f"{stats['objects']} components | "
        f"{stats['triangles']:,} triangles | "
        f"tolerance {manifest['tessellation_tolerance_mm']:g} mm"
    )

    if save_path is not None:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(save_path, dpi=180, bbox_inches="tight")
        print(f"Saved {save_path}")
    if show:
        plt.show()
    else:
        plt.close(figure)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Display a FreeCAD-extracted boat mesh in Matplotlib.",
    )
    parser.add_argument("mesh", type=Path, help="NPZ mesh cache to display")
    parser.add_argument(
        "--save",
        type=Path,
        help="optional PNG path for a non-interactive validation render",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="do not open the interactive Matplotlib window",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    render_boat(args.mesh, save_path=args.save, show=not args.no_show)


if __name__ == "__main__":
    main()
