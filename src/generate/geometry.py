"""FreeCAD-side helpers for extracting display geometry."""

import numpy as np


def get_material_from_label(label):
    """Extract a material name from a FreeCAD object's label."""
    label_lower = label.lower()

    # Format 1: "Aka_0 (aluminum)" -> "aluminum"
    if "(" in label_lower:
        return label_lower.split("(")[1].rstrip(")").strip()

    # Format 2: "Deck__plywood_001" -> "plywood"
    if "__" in label_lower:
        parts = label_lower.split("__")
        if len(parts) >= 2:
            return parts[1].rstrip("_0123456789").strip()

    return None


def material_color(material_name, color_scheme):
    """Read a material's color data, falling back to neutral grey."""
    fallback = {
        "color": [0.55, 0.59, 0.62],
        "transparency": 0,
    }

    materials = color_scheme.get("materials", {})
    material = materials.get(material_name, fallback)
    rgb = np.asarray(material.get("color", fallback["color"]), dtype=np.float64)
    transparency = float(material.get("transparency", 0))


def _tessellate_object(obj, tolerance_mm):
    """Return one FreeCAD object's world-space triangle mesh in metres."""
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

    # FreeCAD uses millimetres; the GLB and shadow pipeline use metres.
    vertices /= 1000.0

    if not np.isfinite(vertices).all():
        raise ValueError(f"{obj.Label!r} produced a non-finite vertex")
    if faces.ndim != 2 or faces.shape[1] != 3:
        raise ValueError(f"{obj.Label!r} did not produce triangle indices")
    if faces.min() < 0 or faces.max() >= len(vertices):
        raise ValueError(f"{obj.Label!r} produced an invalid triangle index")

    # Degenerate triangles are unsuitable for rendering and ray intersection.
    points = vertices[faces]
    double_area = np.linalg.norm(
        np.cross(points[:, 1] - points[:, 0], points[:, 2] - points[:, 0]),
        axis=1,
    )
    faces = faces[double_area > 1e-12]

    return vertices.astype(np.float32), faces.astype(np.uint32)


def tessellate_objects(obj_list, tolerance_mm):
    vertices: list[list] = []
    faces: list[list] = []

    # 
    vertices_offset = 0
    for obj in obj_list:
        obj_vertices, obj_faces = _tessellate_object(obj, tolerance_mm)
        if len(obj_vertices) == 0 or len(obj_faces) == 0:
            continue
        vertices.append(obj_vertices)
        faces.append(obj_faces + vertices_offset)
        vertices_offset += len(obj_vertices)

    if not vertices:
        raise RuntimeError("Mesh not extracted")

    return {
        "vertices": np.concatenate(vertices, axis=0),
        "faces": np.concatenate(faces, axis=0)
    }


def extract_display_geometry(doc, tolerance_mm):
    objects = [obj for obj in doc.Objects 
                if obj.TypeId == "Part::Feature"
                and hasattr(obj, "Shape")
                and not obj.Shape.isNull()
                and "(air)" not in str(obj.Label).casefold()
                and "__air_" not in str(obj.Name).casefold()]

    return tessellate_objects(objects, tolerance_mm)


def extract_shadow_casters(doc, tolerance_mm):
    expected_labels = ["Rig_Biru", "Rig_Kuning"]
    shadow_casters = []
    for obj in doc.Objects:
        if obj.TypeId == "App::Part" and obj.Label in expected_labels:
            shadow_casters.extend(obj.Group)

    return tessellate_objects(shadow_casters, tolerance_mm)
    

def extract_panel_boundaries(doc):
    # select solar panels
    panels = [obj for obj in doc.Objects 
              if obj.TypeId == "Part::Feature"
              and hasattr(obj, "Shape")
              and not obj.Shape.isNull()
              and str(obj.Name).casefold().startswith("panel_")]

    assert len(panels) == 8

    panel_corners = []
    panel_names = []

    #find upper face of panels
    for panel in panels:
        top_face = max(panel.Shape.Faces, key=lambda f: f.CenterOfMass.z)
        corners = np.asarray(
            [(vertex.Point.x, vertex.Point.y, vertex.Point.z) for vertex in top_face.OuterWire.OrderedVertexes], 
            dtype=np.float32
        )
        # convert from mm to m
        corners /= 1000.0

        panel_corners.append(corners)
        panel_names.append(str(panel.Label))


    return {
        "corners": np.asarray(panel_corners, dtype=np.float32),
        "names": np.asarray(panel_names, dtype=str),
    }
    
