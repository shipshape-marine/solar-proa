"""Extract a complete FreeCAD boat model into a compact triangle-mesh cache.

Run this script with the Python interpreter bundled with FreeCAD, for example:

    "C:\\Users\\you\\AppData\\Local\\Programs\\FreeCAD 1.1\\bin\\python.exe" \
        src/solar/extract_boat_mesh.py \
        artifact/rp2.closehaul.design.FCStd \
        artifact/rp2.closehaul.mesh.npz

The NPZ file contains global vertex positions (metres) and indexed triangles.
A JSON manifest beside it preserves component names, roles, colours, ranges,
and extraction statistics.  The output does not require FreeCAD to view.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import FreeCAD as App
import numpy as np


DEFAULT_TOLERANCE_MM = 25.0


def classify_component(label: str) -> str:
    """Return the initial display/analysis role for a named CAD component."""
    normalised = label.casefold().replace(" ", "_")
    if normalised.startswith("panel_"):
        return "solar_panel"
    if normalised.startswith(("sail", "mast", "boom", "yard")):
        return "shadow_caster"
    return "display_only"


def component_colour(label: str, role: str) -> list[float]:
    """Return a readable fallback RGBA colour when GUI colours are unavailable."""
    name = label.casefold()
    if role == "solar_panel":
        return [0.03, 0.18, 0.30, 1.0]
    if name.startswith("sail"):
        return [0.94, 0.94, 0.88, 0.72]
    if any(word in name for word in ("mast", "boom", "yard")):
        return [0.58, 0.62, 0.66, 1.0]
    if "wood" in name or "plywood" in name:
        return [0.57, 0.36, 0.18, 1.0]
    if "steel" in name:
        return [0.34, 0.37, 0.40, 1.0]
    if "aluminum" in name or "aluminium" in name:
        return [0.67, 0.71, 0.75, 1.0]
    if "fiberglass" in name or "fibreglass" in name:
        return [0.72, 0.78, 0.82, 1.0]
    if "foam" in name:
        return [0.83, 0.71, 0.32, 1.0]
    return [0.55, 0.59, 0.62, 1.0]


def should_extract(obj: Any) -> bool:
    """Select physical leaf shapes and omit construction/display helpers."""
    if obj.TypeId != "Part::Feature":
        return False
    if not hasattr(obj, "Shape") or obj.Shape.isNull():
        return False

    # Air volumes are useful for engineering calculations but obscure the
    # physical boat when rendered as opaque Matplotlib polygons.
    label = str(obj.Label).casefold()
    name = str(obj.Name).casefold()
    if "(air)" in label or "__air_" in name:
        return False

    # The design document contains a vertical series of wind-direction arrows
    # for rigging reference.  They are FreeCAD shapes, but they are annotations
    # rather than physical boat components.
    if label.startswith("wind arrow") or "wind_indicator" in name:
        return False

    return True


def tessellate_world_vertices(
    obj: Any,
    tolerance_mm: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Tessellate one object and return world-space vertices and local faces.

    ``Shape.tessellate`` already applies ``obj.Placement``.  It does not apply
    placements inherited from parent ``App::Part`` containers.  Applying only
    the parent transform therefore produces global coordinates without
    applying the object's own placement twice.
    """
    raw_vertices, raw_faces = obj.Shape.tessellate(tolerance_mm)
    if not raw_vertices or not raw_faces:
        return (
            np.empty((0, 3), dtype=np.float32),
            np.empty((0, 3), dtype=np.uint32),
        )

    parent_placement = obj.getGlobalPlacement().multiply(obj.Placement.inverse())
    world_vertices = [parent_placement.multVec(vertex) for vertex in raw_vertices]

    vertices = np.asarray(
        [(vertex.x, vertex.y, vertex.z) for vertex in world_vertices],
        dtype=np.float64,
    )
    faces = np.asarray(raw_faces, dtype=np.int64)

    # FreeCAD geometry uses millimetres.  The viewer and later solar model use
    # metres, matching the convention expected by common web scene formats.
    vertices /= 1000.0

    if not np.isfinite(vertices).all():
        raise ValueError(f"{obj.Label!r} produced a non-finite vertex")
    if faces.ndim != 2 or faces.shape[1] != 3:
        raise ValueError(f"{obj.Label!r} did not produce triangle indices")
    if faces.min() < 0 or faces.max() >= len(vertices):
        raise ValueError(f"{obj.Label!r} produced an invalid triangle index")

    # Remove zero-area triangles.  They cause unstable normals and provide no
    # useful rendered or ray-intersection surface.
    points = vertices[faces]
    double_area = np.linalg.norm(
        np.cross(points[:, 1] - points[:, 0], points[:, 2] - points[:, 0]),
        axis=1,
    )
    faces = faces[double_area > 1e-12]

    return vertices.astype(np.float32), faces.astype(np.uint32)


def extract_model(
    source_path: Path,
    mesh_path: Path,
    tolerance_mm: float,
) -> dict[str, Any]:
    """Extract all supported boat shapes and write NPZ plus JSON outputs."""
    if tolerance_mm <= 0:
        raise ValueError("tessellation tolerance must be greater than zero")
    if not source_path.is_file():
        raise FileNotFoundError(source_path)

    mesh_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = mesh_path.with_suffix(".json")

    document = App.openDocument(str(source_path.resolve()))
    vertices_per_object: list[np.ndarray] = []
    faces_per_object: list[np.ndarray] = []
    records: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    vertex_cursor = 0
    face_cursor = 0

    try:
        for obj in document.Objects:
            if not should_extract(obj):
                continue

            try:
                vertices, local_faces = tessellate_world_vertices(
                    obj,
                    tolerance_mm,
                )
            except Exception as error:  # Keep one bad part from hiding the boat.
                skipped.append({"name": str(obj.Name), "error": str(error)})
                continue

            if len(vertices) == 0 or len(local_faces) == 0:
                skipped.append({"name": str(obj.Name), "error": "empty mesh"})
                continue

            label = str(obj.Label)
            role = classify_component(label)
            global_faces = local_faces.astype(np.uint64) + vertex_cursor
            if vertex_cursor + len(vertices) <= np.iinfo(np.uint32).max:
                global_faces = global_faces.astype(np.uint32)

            records.append(
                {
                    "name": str(obj.Name),
                    "label": label,
                    "type_id": str(obj.TypeId),
                    "role": role,
                    "colour": component_colour(label, role),
                    "vertex_start": vertex_cursor,
                    "vertex_count": int(len(vertices)),
                    "face_start": face_cursor,
                    "face_count": int(len(local_faces)),
                }
            )
            vertices_per_object.append(vertices)
            faces_per_object.append(global_faces)
            vertex_cursor += len(vertices)
            face_cursor += len(local_faces)
    finally:
        App.closeDocument(document.Name)

    if not vertices_per_object:
        raise RuntimeError("no Part::Feature geometry was extracted")

    vertices = np.concatenate(vertices_per_object, axis=0)
    faces = np.concatenate(faces_per_object, axis=0)
    np.savez_compressed(mesh_path, vertices=vertices, faces=faces)

    bounds_min = vertices.min(axis=0)
    bounds_max = vertices.max(axis=0)
    role_counts: dict[str, int] = {}
    for record in records:
        role = record["role"]
        role_counts[role] = role_counts.get(role, 0) + 1

    manifest: dict[str, Any] = {
        "format_version": 1,
        "source": str(source_path.resolve()),
        "mesh": mesh_path.name,
        "units": "metres",
        "axes": {"x": "starboard", "y": "model_forward", "z": "up"},
        "tessellation_tolerance_mm": tolerance_mm,
        "bounds": {
            "minimum": bounds_min.astype(float).tolist(),
            "maximum": bounds_max.astype(float).tolist(),
        },
        "statistics": {
            "objects": len(records),
            "vertices": int(len(vertices)),
            "triangles": int(len(faces)),
            "roles": role_counts,
            "skipped_objects": len(skipped),
        },
        "objects": records,
        "skipped": skipped,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tessellate an FCStd boat for the Matplotlib validator.",
    )
    parser.add_argument("source", type=Path, help="input FreeCAD FCStd file")
    parser.add_argument("output", type=Path, help="output NPZ mesh cache")
    parser.add_argument(
        "--tolerance-mm",
        type=float,
        default=DEFAULT_TOLERANCE_MM,
        help=f"linear tessellation tolerance (default: {DEFAULT_TOLERANCE_MM})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = extract_model(args.source, args.output, args.tolerance_mm)
    statistics = manifest["statistics"]
    print(f"Wrote {args.output}")
    print(f"Wrote {args.output.with_suffix('.json')}")
    print(
        "Extracted "
        f"{statistics['objects']} objects, "
        f"{statistics['vertices']} vertices, and "
        f"{statistics['triangles']} triangles"
    )
    print(f"Roles: {statistics['roles']}")
    if statistics["skipped_objects"]:
        print(f"Skipped {statistics['skipped_objects']} objects; see manifest")


if __name__ == "__main__":
    main()
