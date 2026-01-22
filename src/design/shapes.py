import Part
from FreeCAD import Base
import math

# maker functions for common shapes

def horn_cleat(length, width, height, horn_angle=15):
    """Create a horn cleat for mooring/towing lines.

    The cleat is oriented along the X axis, centered at origin,
    with the base at Z=0 and horns extending outward along X.

    Args:
        length: Overall length of the cleat (tip to tip)
        width: Width of the base
        height: Height of the horn tips above base
        horn_angle: Upward angle of horn tips (degrees)

    Returns:
        A horn cleat shape centered at origin
    """
    # Dimensions derived from main parameters
    base_height = height * 0.15
    horn_radius = width * 0.2
    waist_width = width * 0.35  # narrow center
    waist_length = length * 0.2
    horn_extent = (length - waist_length) / 2  # how far horns extend from center

    # Base plate - tapered, wider at ends
    base = Part.makeBox(length * 0.38, width, base_height)
    base.translate(Base.Vector(-length * 0.19, -width / 2, 0))

    # Center waist (narrow raised section connecting the horns)
    waist = Part.makeBox(waist_length, waist_width, height * 0.5)
    waist.translate(Base.Vector(-waist_length / 2, -waist_width / 2, base_height))

    # Horns: cylinders that extend outward from center, angled slightly up
    # Each horn is positioned at the edge of the waist and extends outward
    # Cylinder is created along Z axis, then rotated to point outward and upward

    # Left horn (negative X direction, tilted up)
    # Rotation: (horn_angle - 90) rotates Z axis toward -X with upward tilt
    horn_left = Part.makeCylinder(horn_radius, horn_extent)
    horn_left.rotate(Base.Vector(0, 0, 0), Base.Vector(0, 1, 0), horn_angle - 90)
    horn_left.translate(Base.Vector(-waist_length / 2, 0, base_height + height * 0.35))

    # Right horn (positive X direction, tilted up)
    # Rotation: (90 - horn_angle) rotates Z axis toward +X with upward tilt
    horn_right = Part.makeCylinder(horn_radius, horn_extent)
    horn_right.rotate(Base.Vector(0, 0, 0), Base.Vector(0, 1, 0), 90 - horn_angle)
    horn_right.translate(Base.Vector(waist_length / 2, 0, base_height + height * 0.35))

    # Rounded tips at the end of each horn
    tip_offset_x = horn_extent * math.cos(math.radians(horn_angle))
    tip_offset_z = horn_extent * math.sin(math.radians(horn_angle))

    tip_left = Part.makeSphere(horn_radius)
    tip_left.translate(Base.Vector(
        -waist_length / 2 - tip_offset_x,
        0,
        base_height + height * 0.35 + tip_offset_z))

    tip_right = Part.makeSphere(horn_radius)
    tip_right.translate(Base.Vector(
        waist_length / 2 + tip_offset_x,
        0,
        base_height + height * 0.35 + tip_offset_z))

    # Combine all parts
    cleat = base.fuse(waist).fuse(horn_left).fuse(horn_right).fuse(tip_left).fuse(tip_right)

    return cleat

# SHS: square hollow section: pipe with square profile

def shs(outer, wall, length):
    # Create outer square
    outer_square = Part.makePolygon([
        Base.Vector(0, 0, 0),
        Base.Vector(outer, 0, 0),
        Base.Vector(outer, outer, 0),
        Base.Vector(0, outer, 0),
        Base.Vector(0, 0, 0)
    ])

    # Create inner square (offset inward)
    inner = outer - 2*wall
    offset = wall
    inner_square = Part.makePolygon([
        Base.Vector(offset, offset, 0),
        Base.Vector(outer-offset, offset, 0),
        Base.Vector(outer-offset, outer-offset, 0),
        Base.Vector(offset, outer-offset, 0),
        Base.Vector(offset, offset, 0)
    ])

    # Create faces and extrude
    outer_face = Part.Face(outer_square)
    inner_face = Part.Face(inner_square)
    profile = outer_face.cut(inner_face)
    shs = profile.extrude(Base.Vector(0, 0, length))
    return shs

# SHS: square hollow section: pipe with square profile

def shs_capped(outer, wall, length, cap_diameter, cap_thickness):
    # Create outer square
    outer_square = Part.makePolygon([
        Base.Vector(0, 0, 0),
        Base.Vector(outer, 0, 0),
        Base.Vector(outer, outer, 0),
        Base.Vector(0, outer, 0),
        Base.Vector(0, 0, 0)
    ])

    # Create inner square (offset inward)
    inner = outer - 2*wall
    offset = wall
    inner_square = Part.makePolygon([
        Base.Vector(offset, offset, 0),
        Base.Vector(outer-offset, offset, 0),
        Base.Vector(outer-offset, outer-offset, 0),
        Base.Vector(offset, outer-offset, 0),
        Base.Vector(offset, offset, 0)
    ])

    # Create faces and extrude
    outer_face = Part.Face(outer_square)
    inner_face = Part.Face(inner_square)
    profile = outer_face.cut(inner_face)
    shs = profile.extrude(Base.Vector(0, 0, length))

    cap_radius = cap_diameter / 2
    cap1 = Part.makeCylinder(cap_radius, cap_thickness)
    cap1.translate(Base.Vector(outer/2, outer/2, - cap_thickness))
    cap2 = Part.makeCylinder(cap_radius, cap_thickness)
    cap2.translate(Base.Vector(outer/2, outer/2, length))
    
    return shs.fuse(cap1).fuse(cap2)

# Rectangular tube with caps

def rectangular_tube_capped(outer1, outer2, wall, length, cap_diameter, cap_thickness):
    # Create outer square
    outer_square = Part.makePolygon([
        Base.Vector(0, 0, 0),
        Base.Vector(outer1, 0, 0),
        Base.Vector(outer1, outer2, 0),
        Base.Vector(0, outer2, 0),
        Base.Vector(0, 0, 0)
    ])

    # Create inner square (offset inward)
    inner1 = outer1 - 2*wall
    inner2 = outer2 - 2*wall
    offset = wall
    inner_square = Part.makePolygon([
        Base.Vector(offset, offset, 0),
        Base.Vector(outer1-offset, offset, 0),
        Base.Vector(outer1-offset, outer2-offset, 0),
        Base.Vector(offset, outer2-offset, 0),
        Base.Vector(offset, offset, 0)
    ])

    # Create faces and extrude
    outer_face = Part.Face(outer_square)
    inner_face = Part.Face(inner_square)
    profile = outer_face.cut(inner_face)
    shs = profile.extrude(Base.Vector(0, 0, length))

    cap_radius = cap_diameter / 2
    cap1 = Part.makeCylinder(cap_radius, cap_thickness)
    cap1.translate(Base.Vector(outer1/2, outer2/2, - cap_thickness))
    cap2 = Part.makeCylinder(cap_radius, cap_thickness)
    cap2.translate(Base.Vector(outer1/2, outer2/2, length))
    
    return shs.fuse(cap1).fuse(cap2)

# circular pipe

def pipe(diameter, thickness, length):
    """Create a hollow cylinder (pipe)"""
    outer_radius = diameter / 2
    inner_radius = outer_radius - thickness
    
    # Create outer cylinder
    outer_cylinder = Part.makeCylinder(outer_radius, length)
    
    # Create inner cylinder (to subtract)
    inner_cylinder = Part.makeCylinder(inner_radius, length)
    
    # Subtract to make hollow
    pipe = outer_cylinder.cut(inner_cylinder)
    
    return pipe

# circular cone

def hollow_cone(diameter, thickness, length):
    radius_outer = diameter / 2
    radius_inner = radius_outer - thickness
    outer_cone = Part.makeCone(radius_outer, 0, length)
    inner_length = length * radius_inner / radius_outer
    inner_cone = Part.makeCone(radius_inner, 0, inner_length)
    hollow_cone = outer_cone.cut(inner_cone)
    return hollow_cone

# solid elliptical cylinder

def elliptical_cylinder(major_diameter, minor_diameter, length):
    """Create an elliptical cylinder"""
    major_radius = major_diameter / 2
    minor_radius = minor_diameter / 2
    
    # Create ellipse
    ellipse = Part.Ellipse(
        Base.Vector(0, 0, 0),  # center
        major_radius,
        minor_radius)
    wire = Part.Wire(ellipse.toShape())
    face = Part.Face(wire)
    
    # Extrude along Z-axis
    elliptical_cylinder = face.extrude(Base.Vector(0, 0, length))
    
    return elliptical_cylinder

# hollow elliptical cylinder

def elliptical_pipe(major_diameter, minor_diameter, thickness, length):
    """Create a hollow elliptical cylinder"""
    major_radius_outer = major_diameter / 2
    minor_radius_outer = minor_diameter / 2
    major_radius_inner = major_radius_outer - thickness
    minor_radius_inner = minor_radius_outer - thickness
    
    # Create outer ellipse
    outer_ellipse = Part.Ellipse(
        Base.Vector(0, 0, 0),  # center
        major_radius_outer,
        minor_radius_outer)
    outer_wire = Part.Wire(outer_ellipse.toShape())
    outer_face = Part.Face(outer_wire)
    
    # Create inner ellipse
    inner_ellipse = Part.Ellipse(
        Base.Vector(0, 0, 0),  # center
        major_radius_inner,
        minor_radius_inner)
    inner_wire = Part.Wire(inner_ellipse.toShape())
    inner_face = Part.Face(inner_wire)
    
    # Subtract inner from outer to get hollow profile
    profile = outer_face.cut(inner_face)
    
    # Extrude along Z-axis
    elliptical_pipe = profile.extrude(Base.Vector(0, 0, length))
    
    return elliptical_pipe

# 3D arrow (cylinder + cone)

def direction_arrow(length, shaft_radius=None, head_radius=None, head_length=None):
    """Create a 3D arrow pointing along positive Z axis.

    The arrow is centered at origin with the tail at Z=0 and tip at Z=length.

    Args:
        length: Total length of the arrow
        shaft_radius: Radius of the cylindrical shaft (default: length/40)
        head_radius: Radius of the cone head base (default: shaft_radius * 3)
        head_length: Length of the cone head (default: length * 0.2)

    Returns:
        Arrow shape pointing along positive Z
    """
    # Default proportions if not specified
    if shaft_radius is None:
        shaft_radius = length / 40
    if head_radius is None:
        head_radius = shaft_radius * 3
    if head_length is None:
        head_length = length * 0.2

    shaft_length = length - head_length

    # Shaft (cylinder)
    shaft = Part.makeCylinder(shaft_radius, shaft_length)

    # Head (cone) - positioned at the end of the shaft
    head = Part.makeCone(head_radius, 0, head_length)
    head.translate(Base.Vector(0, 0, shaft_length))

    # Combine
    arrow = shaft.fuse(head)

    return arrow


# ellipsoid

def ellipsoid(x_diameter, y_diameter, z_diameter):
    """Create an ellipsoid (3D ellipse)"""
    # Create a sphere and then scale it to make an ellipsoid
    sphere = Part.makeSphere(1.0)
    
    # Scale to the desired dimensions
    # FreeCAD sphere has radius 1, so we scale to get the desired radii
    x_scale = x_diameter / 2
    y_scale = y_diameter / 2
    z_scale = z_diameter / 2
    
    # Create scaling matrix
    matrix = Base.Matrix()
    matrix.scale(Base.Vector(x_scale, y_scale, z_scale))
    
    # Apply scaling
    ellipsoid_shape = sphere.transformGeometry(matrix)
    
    return ellipsoid_shape
