import FreeCAD
import Part
from FreeCAD import Base
import math

from shapes import *

# rig: masts and sails

def rig(the_rig, params, sail_angle=0, sail_camber=10000, reefing_percentage=0,
        x_offset=0, y_offset=0, z_rotation=0):
    """
    Build a rig with rotatable sail at absolute position.
    sail_angle: rotation angle in degrees around the yard spar axis
    x_offset, y_offset: absolute position of the mast base
    z_rotation: rotation around Z axis in degrees
    """

    effective_sail_height = params['sail_height'] * (100 - reefing_percentage) / 100

    # Base position for this rig
    base_x = x_offset
    base_y = y_offset
    base_z = params['mast_base_level']

    # Rotation around Z axis
    z_rot = FreeCAD.Rotation(Base.Vector(0, 0, 1), z_rotation)

    def place(local_x, local_y, local_z, rotation=None):
        """Convert local coordinates to absolute, applying z_rotation."""
        local_vec = Base.Vector(local_x, local_y, 0)
        rotated = z_rot.multVec(local_vec)
        abs_vec = Base.Vector(base_x + rotated.x, base_y + rotated.y, base_z + local_z)
        if rotation:
            final_rot = z_rot.multiply(rotation)
        else:
            final_rot = z_rot
        return FreeCAD.Placement(abs_vec, final_rot)

    # mast

    mast_lower_section = the_rig.newObject("Part::Feature", "Mast_lower_section (aluminum)")
    mast_lower_section.Shape = pipe(params['mast_diameter'],
                                    params['mast_thickness'],
                                    params['mast_height'] / 2 +
                                    params['mast_section_overlap'] / 2)
    mast_lower_section.Placement = place(0, 0, 0)

    mast_upper_section = the_rig.newObject("Part::Feature", "Mast_upper_section (aluminum)")
    mast_upper_section.Shape = pipe(params['mast_diameter']
                                    - params['mast_thickness'] * 2,
                                    params['mast_thickness'],
                                    params['mast_height'] / 2 +
                                    params['mast_section_overlap'] / 2)
    mast_upper_section.Placement = place(0, 0,
                    params['mast_height'] / 2 -
                    params['mast_section_overlap'] / 2)

    mast_cap = the_rig.newObject("Part::Feature", "Mast Cap (aluminum)")
    mast_cap.Shape = Part.makeCylinder(params['mast_cap_diameter'] / 2,
                                       params['mast_cap_thickness'])
    mast_cap.Placement = place(0, 0, params['mast_height'])

    # yard spar - attachment point for the sail yard
    yard_spar_z = params['yard_spar_height'] - params['mast_base_level']

    yard_spar = the_rig.newObject("Part::Feature",
                                  "Yard Spar (aluminum)")
    yard_spar.Shape = Part.makeBox(params['yard_spar_length'],
                                   params['yard_spar_width'],
                                   params['yard_spar_thickness'])
    yard_spar.Placement = place(params['mast_diameter'] / 2,
                    - params['yard_spar_width'] / 2,
                    yard_spar_z)

    # yard spar brace - 45 degree brace for yard spar
    yard_spar_brace = the_rig.newObject("Part::Feature",
                                        "Yard Spar Brace (aluminum)")
    yard_spar_brace.Shape = Part.makeBox(params['yard_spar_length'] * math.sqrt(2),
                                         params['yard_spar_width'],
                                         params['yard_spar_thickness'])
    yard_spar_brace.Placement = place(params['mast_diameter'] / 2,
                    - params['yard_spar_width'] / 2,
                    params['mast_height'],
                    FreeCAD.Rotation(Base.Vector(0, 1, 0), 45))

    # mast handle
    mast_handle = the_rig.newObject("Part::Feature", "Mast Handle (aluminum)")
    mast_handle.Shape = pipe(params['mast_handle_diameter'],
                             params['mast_handle_thickness'],
                             params['mast_handle_length'])
    mast_handle_z = (params['deck_level'] + params['mast_handle_height_above_deck']
                     - params['mast_base_level'])
    mast_handle.Placement = place(0,
                    params['mast_handle_length'] / 2,
                    mast_handle_z,
                    FreeCAD.Rotation(Base.Vector(1, 0, 0), 90))

    # Pivot point for sail rotation (at the yard centerline, end of yard spar)
    # Local coordinates relative to mast base
    pivot_local_x = params['yard_spar_length'] + params['mast_diameter'] / 2
    pivot_local_y = 0
    pivot_local_z = yard_spar_z + params['yard_spar_thickness'] / 2

    # Yard - rotates around pivot point
    yard = the_rig.newObject("Part::Feature", "Yard (aluminum)")
    yard.Shape = pipe(params['yard_diameter'], params['yard_thickness'], params['yard_length'])

    # Calculate yard position with rotation
    # Yard extends along Y in unrotated position
    angle_rad = math.radians(sail_angle)

    # Yard center in rotated position (local coords)
    yard_offset_y = params['yard_length'] / 2 * math.cos(angle_rad)
    yard_offset_z = params['yard_length'] / 2 * math.sin(angle_rad)

    yard.Placement = place(pivot_local_x, pivot_local_y + yard_offset_y, pivot_local_z + yard_offset_z,
        FreeCAD.Rotation(Base.Vector(1, 0, 0), 90 + sail_angle))

    # Boom - parallel to yard, offset by effective_sail_height VERTICALLY from the pivot
    boom = the_rig.newObject("Part::Feature", "Boom (aluminum)")
    boom.Shape = pipe(params['boom_diameter'],
                      params['boom_thickness'],
                      params['boom_length'])

    # Boom rotates around the SAME pivot point as yard
    # But its unrotated position is effective_sail_height below the pivot
    boom_local_y = params['boom_length'] / 2
    boom_local_z = - effective_sail_height

    # Rotate this point around X axis (pivot is origin)
    boom_offset_y = boom_local_y * math.cos(angle_rad) - boom_local_z * math.sin(angle_rad)
    boom_offset_z = boom_local_y * math.sin(angle_rad) + boom_local_z * math.cos(angle_rad)

    boom.Placement = place(pivot_local_x, pivot_local_y + boom_offset_y, pivot_local_z + boom_offset_z,
        FreeCAD.Rotation(Base.Vector(1, 0, 0), 90 + sail_angle))
    
    # Sail surface - hollow cylinder (thin membrane)

    cylinder_center_z = - effective_sail_height / 2
    vertical_offset = effective_sail_height / 2
    cylinder_center_x = -math.sqrt(sail_camber**2 - vertical_offset**2)

    # hollow cylinder
    outer_cylinder = Part.makeCylinder(sail_camber,
                                       params['yard_length'],
                                       Base.Vector(cylinder_center_x,
                                                   - params['yard_length']/2,
                                                   cylinder_center_z),
                                       Base.Vector(0, 1, 0))
    inner_cylinder = Part.makeCylinder(sail_camber - params['sail_thickness'],
                                       params['yard_length'],
                                       Base.Vector(cylinder_center_x,
                                                   - params['yard_length'] / 2,
                                                   cylinder_center_z),
                                       Base.Vector(0, 1, 0))
    cylinder = outer_cylinder.cut(inner_cylinder)

    box_width = sail_camber * 2
    sail_box = Part.makeBox(box_width, params['yard_length'], effective_sail_height,
                            Base.Vector(0,
                                        - params['yard_length'] / 2,
                                        - effective_sail_height))

    sail_section = cylinder.common(sail_box)

    # Rotate sail around X axis for sail_angle
    sail_section = sail_section.rotate(Base.Vector(0, 0, 0),
                                        Base.Vector(1, 0, 0),
                                        sail_angle)

    # Translate to local pivot position
    sail_section = sail_section.translate(Base.Vector(pivot_local_x, pivot_local_y, pivot_local_z))

    # Apply z_rotation around local origin, then translate to absolute position
    z_rot_rad = math.radians(z_rotation)
    sail_section = sail_section.rotate(Base.Vector(0, 0, 0),
                                        Base.Vector(0, 0, 1),
                                        z_rotation)
    sail_section = sail_section.translate(Base.Vector(base_x, base_y, base_z))

    sail = the_rig.newObject("Part::Feature", "Sail (nylon)")
    sail.Shape = sail_section

# rudder: post and blade

def rudder(the_rudder, params, raised, x_offset=0, y_offset=0, z_rotation=0):
    """
    Build a rudder at absolute position.
    x_offset, y_offset: absolute position of the rudder post
    z_rotation: rotation around Z axis in degrees
    """

    z_offset = params['rudder_vaka_mount_base_level'] if raised else 0

    # Base position for this rudder
    base_x = x_offset
    base_y = y_offset

    # Rotation around Z axis
    z_rot = FreeCAD.Rotation(Base.Vector(0, 0, 1), z_rotation)

    def place(local_x, local_y, local_z, rotation=None):
        """Convert local coordinates to absolute, applying z_rotation."""
        local_vec = Base.Vector(local_x, local_y, 0)
        rotated = z_rot.multVec(local_vec)
        abs_vec = Base.Vector(base_x + rotated.x, base_y + rotated.y, local_z)
        if rotation:
            final_rot = z_rot.multiply(rotation)
        else:
            final_rot = z_rot
        return FreeCAD.Placement(abs_vec, final_rot)

    # post

    post = the_rudder.newObject("Part::Feature", "Rudder_Post (steel)")
    post.Shape = Part.makeCylinder(params['rudder_post_diameter'] / 2,
                                   params['deck_base_level'] + params['rudder_blade_height'])
    post.Placement = place(0, 0, z_offset - params['rudder_blade_height'])

    bearing_block = the_rudder.newObject("Part::Feature", "Rudder_Bearing_Block (plastic)")
    bearing_block.Shape = Part.makeCylinder(params['rudder_bearing_block_diameter'] / 2,
                                            params['rudder_bearing_block_height'])
    bearing_block.Placement = place(0, 0, params['stringer_base_level'] + z_offset)

    aka_mount_pin = the_rudder.newObject("Part::Feature", "Rudder_Mount_Pin (aluminum)")
    aka_mount_pin.Shape = Part.makeCylinder(params['rudder_aka_mount_pin_diameter'] / 2,
                                            params['rudder_aka_mount_pin_length'])
    aka_mount_pin.Placement = place(0,
                    params['rudder_aka_mount_pin_length'] / 2,
                    params['stringer_base_level'] + z_offset + params['stringer_width'] / 2,
                    FreeCAD.Rotation(Base.Vector(1, 0, 0), 90))

    cap = the_rudder.newObject("Part::Feature", "Rudder_Cap (steel)")
    cap.Shape = Part.makeCylinder(params['rudder_aka_mount_pin_length'] / 2 + 10, # 10mm space
                                  params['deck_thickness'])
    cap.Placement = place(0, 0, z_offset + params['deck_base_level'])

    # cutting into tillers - these shapes are used locally for cutting, not placed
    tiller_cutter_cylinder_shape = Part.makeCylinder(
        params['rudder_aka_mount_pin_diameter'] / 2,
        params['rudder_aka_mount_pin_length'])
    tiller_cutter_cylinder_shape.rotate(
        Base.Vector(0,0,0),
        Base.Vector(1, 0, 0), 90)
    tiller_cutter_cylinder_shape.translate(
        Base.Vector(0,
                    params['rudder_aka_mount_pin_length'] / 2,
                    params['stringer_base_level'] + params['stringer_width'] / 2))
    tiller_cutter_box_shape = Part.makeBox(params['rudder_aka_mount_pin_diameter'],
                                           params['rudder_aka_mount_pin_length'],
                                           params['rudder_aka_mount_pin_length'])
    tiller_cutter_box_shape.translate(
        Base.Vector(- params['rudder_aka_mount_pin_diameter'] / 2,
                    - params['rudder_aka_mount_pin_length'] / 2,
                    params['stringer_base_level'] + params['stringer_width'] / 2))

    # tillers (A and B): SHS rods that come from aka mount pin and go to vaka
    tiller_rot1 = FreeCAD.Rotation(Base.Vector(-1, 0, 0), 90)

    tiller_a = the_rudder.newObject("Part::Feature", "Tiller_A (aluminum)")
    tiller_a.Shape = shs(params['tiller_width'],
                         params['tiller_thickness'],
                         params['tiller_length'])
    tiller_a_rot2 = FreeCAD.Rotation(Base.Vector(0, 1, 0), 90 + params['tiller_angle'])
    tiller_a_rotation = tiller_rot1.multiply(tiller_a_rot2)
    tiller_a.Placement = place(- params['tiller_width'],
                    params['rudder_aka_mount_pin_length'] / 2,
                    params['stringer_base_level'] + params['tiller_width'],
                    tiller_a_rotation)
    tiller_a.Shape = tiller_a.Shape.cut(tiller_cutter_cylinder_shape)
    tiller_a.Shape = tiller_a.Shape.cut(tiller_cutter_box_shape)

    tiller_b = the_rudder.newObject("Part::Feature", "Tiller_B (aluminum)")
    tiller_b.Shape = shs(params['tiller_width'],
                         params['tiller_thickness'],
                         params['tiller_length'])
    tiller_b_rot2 = FreeCAD.Rotation(Base.Vector(0, 1, 0), 90 - params['tiller_angle'])
    tiller_b_rotation = tiller_rot1.multiply(tiller_b_rot2)
    tiller_b.Placement = place(- params['tiller_width'],
                    - params['rudder_aka_mount_pin_length'] / 2 + params['tiller_width'],
                    params['stringer_base_level'] + params['tiller_width'],
                    tiller_b_rotation)
    tiller_b.Shape = tiller_b.Shape.cut(tiller_cutter_cylinder_shape)
    tiller_b.Shape = tiller_b.Shape.cut(tiller_cutter_box_shape)

    tiller_brace = the_rudder.newObject("Part::Feature", "Tiller_Brace (aluminum)")
    tiller_brace.Shape = shs(params['tiller_width'],
                             params['tiller_thickness'],
                             params['tiller_length'] / 4)
    tiller_brace.Placement = place(params['tiller_length'] / 6,
                    -params['tiller_length'] / 8,
                    params['stringer_base_level'] + params['tiller_width'],
                    tiller_rot1)

    tiller_rod = the_rudder.newObject("Part::Feature", "Tiller_Rod (aluminum)")
    tiller_rod.Shape = Part.makeCylinder(params['tiller_rod_diameter'] / 2,
                         params['tiller_rod_length'])
    tiller_rod.Placement = place(params['tiller_length'] - params['tiller_width'] * 2,
                    - params['tiller_width'] if "Kuning" in the_rudder.Label
                    else params['tiller_width'] - params['tiller_rod_length'],
                    params['stringer_base_level'] + params['tiller_width'] / 2,
                    tiller_rot1)

    tiller_rod_knob = the_rudder.newObject("Part::Feature", "Tiller_Rod_Knob (aluminum)")
    tiller_rod_knob.Shape = Part.makeSphere(params['tiller_rod_diameter'] * 2)
    tiller_rod_knob.Placement = place(params['tiller_length'] - params['tiller_width'] * 2,
                    - params['tiller_width'] + params['tiller_rod_length'] if "Kuning" in the_rudder.Label
                    else params['tiller_width'] - params['tiller_rod_length'],
                    params['stringer_base_level'] + params['tiller_width'] / 2,
                    tiller_rot1)
    
    # steel ribs (rods) for rudder
    rib_spacing = ((params['rudder_blade_height'] - 2 * params['rudder_rim'])
                   / (params['rudder_ribs'] - 1))
    for i in range(0, params['rudder_ribs']):
        rib = the_rudder.newObject("Part::Feature", f"Rudder_Rib_{i} (steel)")
        rib.Shape = Part.makeCylinder(params['rudder_rib_diameter'] / 2,
                                      params['rudder_rib_length'])
        rib.Placement = place(0,
                        params['rudder_rib_length'] / 2,
                        params['rudder_rim'] + i * rib_spacing
                        + z_offset
                        - params['rudder_blade_height'],
                        FreeCAD.Rotation(Base.Vector(1, 0, 0), 90))

    # blade: thin sheet to indicate the shape of rudder
    blade = the_rudder.newObject("Part::Feature", "Rudder_Blade (plywood)")
    blade.Shape = Part.makeBox(params['rudder_blade_thickness'],
                               params['rudder_blade_length'],
                               params['rudder_blade_height'])
    blade.Placement = place(- params['rudder_blade_thickness'] / 2,
                    - params['rudder_blade_length'] / 2,
                    z_offset - params['rudder_blade_height'])
    
