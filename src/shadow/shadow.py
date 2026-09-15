from pathlib import Path

import numpy as np
import math
import trimesh


def _load_geometry(npz_path: str | Path) -> dict[str, np.ndarray]:
    with np.load(Path(npz_path), allow_pickle=False) as geometry:
        return {
            "shadow_caster_vertices": geometry["shadow_caster_vertices"],
            "shadow_caster_faces": geometry["shadow_caster_faces"],
            "panel_corners": geometry["panel_corners"],
            "panel_names": geometry["panel_names"],
        }


# actual spacing <= max_spacing, 
def _sample_panel(panel_corners, max_spacing_m=0.1):
    if max_spacing_m <= 0:
        raise ValueError("Spacing must be a positive value")

    # vectors of edges
    edge_a = panel_corners[1] - panel_corners[0]
    edge_b = panel_corners[3] - panel_corners[0]

    length_a = np.linalg.norm(edge_a)
    length_b = np.linalg.norm(edge_b)

    point_count_a = math.ceil(length_a / max_spacing_m)
    point_count_b = math.ceil(length_b / max_spacing_m)

    # amount to increment in a and b direction for each point (spacing vector)
    # basically splitting the panel into point_count_* blocks length- and width-wise
    increment_a = edge_a / point_count_a
    increment_b = edge_b / point_count_b

    sample_points = []
    # after splitting panel into blocks, set the sample points to be in the center of these blocks
    # take reference from the point in panel_corners[0]
    for a in range(point_count_a):
        for b in range(point_count_b):
            # +0.5 to position point in the centre of the block
            point = panel_corners[0] + (a + 0.5) * increment_a + (b + 0.5) * increment_b
            sample_points.append(point)

    return np.asarray(sample_points, dtype=np.float32)


# possible extension: return position of sample points for the shadow coverage to be visualised
def calculate_shadow_percentage(npz_path: Path | str, sun_vector, approx_sample_spacing):
    geometry = _load_geometry(Path(npz_path))
    mesh = trimesh.Trimesh(
        vertices=geometry["shadow_caster_vertices"], 
        faces=geometry["shadow_caster_faces"], 
        process=False
        )

    panel_sample_points = []
    for panel_corners, panel_name in zip(geometry["panel_corners"], geometry["panel_names"]):
        panel_sample_points.append(_sample_panel(panel_corners, approx_sample_spacing))
        sample_points = np.concatenate(panel_sample_points, axis=0)

        sun_direction = np.asarray(sun_vector, dtype=np.float64)
        sun_direction_length = np.linalg.norm(sun_direction)
        if sun_direction_length == 0:
            raise ValueError("Sun vector must not be zero")
        sun_direction /= sun_direction_length

        ray_directions = np.tile(sun_direction, (len(sample_points), 1))
        # returns an array of boolean value per sample point
        blocked = mesh.ray.intersects_any(ray_origins=sample_points, ray_directions=ray_directions)


    return float(100 * np.mean(blocked))


