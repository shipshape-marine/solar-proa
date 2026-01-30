import FreeCAD
import Part
from FreeCAD import Base
import math

from shapes import *

# rig: masts and sails

def rig(the_rig, params, sail_angle=0, sail_camber=10000, reefing_percentage=0):
    """
    Build a rig with rotatable sail
    sail_angle: rotation angle in degrees around the yard spar axis
    """

    effective_sail_height = params['sail_height'] * (100 - reefing_percentage) / 100
    
    # mast
    
    mast_lower_section = the_rig.newObject("Part::Feature", "Mast_lower_section (aluminum)")
    mast_lower_section.Shape = pipe(params['mast_diameter'],
                                    params['mast_thickness'],
                                    params['mast_height'] / 2 +
                                    params['mast_section_overlap'] / 2)
    mast_lower_section.Placement = FreeCAD.Placement(
        Base.Vector(0, 0, params['mast_base_level']),
        FreeCAD.Rotation(Base.Vector(0, 0, 0), 0))

    mast_upper_section = the_rig.newObject("Part::Feature", "Mast_upper_section (aluminum)")
    mast_upper_section.Shape = pipe(params['mast_diameter']
                                    - params['mast_thickness'] * 2,
                                    params['mast_thickness'],
                                    params['mast_height'] / 2 +
                                    params['mast_section_overlap'] / 2)
    mast_upper_section.Placement = FreeCAD.Placement(
        Base.Vector(0, 0,
                    params['mast_base_level'] +
                    params['mast_height'] / 2 -
                    params['mast_section_overlap'] / 2),
        FreeCAD.Rotation(Base.Vector(0, 0, 0), 0))

    mast_cap = the_rig.newObject("Part::Feature", "Mast Cap (aluminum)")
    mast_cap.Shape = Part.makeCylinder(params['mast_cap_diameter'] / 2,
                                       params['mast_cap_thickness'])
    mast_cap.Placement = FreeCAD.Placement(
        Base.Vector(0, 0, params['mast_height'] + params['mast_base_level']),
        FreeCAD.Rotation(Base.Vector(0, 0, 0), 0))
    
    # yard spar - attachment point for the sail yard

    yard_spar = the_rig.newObject("Part::Feature",
                                  "Yard Spar (aluminum)")
    yard_spar.Shape = Part.makeBox(params['yard_spar_length'],
                                   params['yard_spar_width'],
                                   params['yard_spar_thickness'])
    yard_spar.Placement = FreeCAD.Placement(
        Base.Vector(params['mast_diameter'] / 2, 
                    - params['yard_spar_width'] / 2,
                    params['yard_spar_height']),
        FreeCAD.Rotation(Base.Vector(0, 0, 0), 0))

    # yard spar brace - 45 degree brace for yard spar
    yard_spar_brace = the_rig.newObject("Part::Feature",
                                        "Yard Spar Brace (aluminum)")
    yard_spar_brace.Shape = Part.makeBox(params['yard_spar_length'] * math.sqrt(2),
                                         params['yard_spar_width'],
                                         params['yard_spar_thickness'])
    yard_spar_brace.Placement = FreeCAD.Placement(
        Base.Vector(params['mast_diameter'] / 2,
                    - params['yard_spar_width'] / 2,
                    params['mast_height']),
        FreeCAD.Rotation(Base.Vector(0, 1, 0), 45))
    
    # mast handle
    mast_handle = the_rig.newObject("Part::Feature", "Mast Handle (aluminum)")
    mast_handle.Shape = pipe(params['mast_handle_diameter'],
                             params['mast_handle_thickness'],
                             params['mast_handle_length'])
    mast_handle.Placement = FreeCAD.Placement(
        Base.Vector(0,
                    params['mast_handle_length'] / 2,
                    params['deck_level'] + params['mast_handle_height_above_deck']),
        FreeCAD.Rotation(Base.Vector(1, 0, 0), 90))
    
    # Pivot point for sail rotation (at the yard centerline, end of yard spar)
    pivot_x = params['yard_spar_length'] + params['mast_diameter'] / 2
    pivot_y = 0
    pivot_z = params['yard_spar_height'] + params['yard_spar_thickness'] / 2
    
    # Yard - rotates around pivot point
    yard = the_rig.newObject("Part::Feature", "Yard (aluminum)")
    yard.Shape = pipe(params['yard_diameter'], params['yard_thickness'], params['yard_length'])
    
    # Calculate yard position with rotation
    # Yard extends along Y in unrotated position
    angle_rad = math.radians(sail_angle)
    
    # Yard center in rotated position
    yard_offset_y = params['yard_length'] / 2 * math.cos(angle_rad)
    yard_offset_z = params['yard_length'] / 2 * math.sin(angle_rad)
    
    yard.Placement = FreeCAD.Placement(
        Base.Vector(pivot_x, pivot_y + yard_offset_y, pivot_z + yard_offset_z),
        FreeCAD.Rotation(Base.Vector(1, 0, 0), 90 + sail_angle))  # Rotate around X axis
    
    # Boom - parallel to yard, offset by effective_sail_height VERTICALLY from the pivot
    boom = the_rig.newObject("Part::Feature", "Boom (aluminum)")
    boom.Shape = pipe(params['boom_diameter'],
                      params['boom_thickness'],
                      params['boom_length'])

    # Boom rotates around the SAME pivot point as yard
    # But its unrotated position is effective_sail_height below the pivot
    # So we need to rotate the point (0, boom_length/2, -effective_sail_height) around the pivot

    # In unrotated position: boom center is at (0, boom_length/2, -effective_sail_height) relative to pivot
    # After rotation by angle around X axis:
    boom_local_y = params['boom_length'] / 2
    boom_local_z = - effective_sail_height
    
    # Rotate this point around X axis (pivot is origin)
    boom_offset_y = boom_local_y * math.cos(angle_rad) - boom_local_z * math.sin(angle_rad)
    boom_offset_z = boom_local_y * math.sin(angle_rad) + boom_local_z * math.cos(angle_rad)
    
    boom.Placement = FreeCAD.Placement(
        Base.Vector(pivot_x, pivot_y + boom_offset_y, pivot_z + boom_offset_z),
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
    
    sail_section = sail_section.rotate(Base.Vector(0, 0, 0), 
                                        Base.Vector(1, 0, 0), 
                                        sail_angle)
    
    sail_section = sail_section.translate(Base.Vector(pivot_x, pivot_y, pivot_z))
    
    sail = the_rig.newObject("Part::Feature", "Sail (nylon)")
    sail.Shape = sail_section

# rudder: post and blade

def rudder(the_rudder, params, raised):

    z_offset = params['rudder_vaka_mount_base_level'] if raised else 0

    # post
    
    post = the_rudder.newObject("Part::Feature", "Rudder_Post (steel)")
    post.Shape = Part.makeCylinder(params['rudder_post_diameter'] / 2,
                                   params['deck_base_level'] + params['rudder_blade_height'])
    post.Placement = FreeCAD.Placement(
        Base.Vector(0, 0, z_offset - params['rudder_blade_height']),
        FreeCAD.Rotation(Base.Vector(0, 0, 0), 0))

    bearing_block = the_rudder.newObject("Part::Feature", "Rudder_Bearing_Block (plastic)")
    bearing_block.Shape = Part.makeCylinder(params['rudder_bearing_block_diameter'] / 2,
                                            params['rudder_bearing_block_height'])
    bearing_block.Placement = FreeCAD.Placement(
        Base.Vector(0, 0, params['stringer_base_level'] + z_offset),
        FreeCAD.Rotation(Base.Vector(0, 0, 0), 0))

    aka_mount_pin = the_rudder.newObject("Part::Feature", "Rudder_Mount_Pin (aluminum)")
    aka_mount_pin.Shape = Part.makeCylinder(params['rudder_aka_mount_pin_diameter'] / 2,
                                            params['rudder_aka_mount_pin_length'])
    aka_mount_pin.Placement = FreeCAD.Placement(
        Base.Vector(0,
                    params['rudder_aka_mount_pin_length'] / 2,
                    params['stringer_base_level'] + z_offset + params['stringer_width'] / 2),
        FreeCAD.Rotation(Base.Vector(1, 0, 0), 90))

    cap = the_rudder.newObject("Part::Feature", "Rudder_Cap (steel)")
    cap.Shape = Part.makeCylinder(params['rudder_aka_mount_pin_length'] / 2 + 10, # 10mm space
                                  params['deck_thickness'])
    cap.Placement = FreeCAD.Placement(
        Base.Vector(0, 0, z_offset + params['deck_base_level']),
        FreeCAD.Rotation(Base.Vector(0, 0, 0), 0))

    # cutting into tillers
    
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
    
    tiller_a = the_rudder.newObject("Part::Feature", "Tiller_A (aluminum)")
    tiller_a.Shape = shs(params['tiller_width'],
                         params['tiller_thickness'],
                         params['tiller_length'])
    tiller_rot1 = FreeCAD.Rotation(Base.Vector(-1, 0, 0), 90)
    tiller_a_rot2 = FreeCAD.Rotation(Base.Vector(0, 1, 0), 90 + params['tiller_angle'])
    tiller_a_rotation = tiller_rot1.multiply(tiller_a_rot2)
    tiller_a.Placement = FreeCAD.Placement(
        Base.Vector(- params['tiller_width'],
                    params['rudder_aka_mount_pin_length'] / 2,
                    params['stringer_base_level'] + params['tiller_width']),
        tiller_a_rotation)
    tiller_a.Shape = tiller_a.Shape.cut(tiller_cutter_cylinder_shape)
    tiller_a.Shape = tiller_a.Shape.cut(tiller_cutter_box_shape)
    
    tiller_b = the_rudder.newObject("Part::Feature", "Tiller_B (aluminum)")
    tiller_b.Shape = shs(params['tiller_width'],
                         params['tiller_thickness'],
                         params['tiller_length'])
    tiller_b_rot2 = FreeCAD.Rotation(Base.Vector(0, 1, 0), 90 - params['tiller_angle'])
    tiller_b_rotation = tiller_rot1.multiply(tiller_b_rot2)    
    tiller_b.Placement = FreeCAD.Placement(
        Base.Vector(- params['tiller_width'],
                    - params['rudder_aka_mount_pin_length'] / 2 + params['tiller_width'],
                    params['stringer_base_level'] + params['tiller_width']),
        tiller_b_rotation)
    tiller_b.Shape = tiller_b.Shape.cut(tiller_cutter_cylinder_shape)
    tiller_b.Shape = tiller_b.Shape.cut(tiller_cutter_box_shape)

    tiller_rod = the_rudder.newObject("Part::Feature", "Tiller_Rod (aluminum)")
    tiller_rod.Shape = Part.makeCylinder(params['tiller_rod_diameter'] / 2,
                         params['tiller_rod_length'])
    tiller_rod_rot2 = FreeCAD.Rotation(Base.Vector(0, 1, 0), 0)
    tiller_rod_rotation = tiller_rot1.multiply(tiller_rod_rot2)
    tiller_rod.Placement = FreeCAD.Placement(
        Base.Vector(params['tiller_length'] - params['tiller_width'] * 2,
                    - params['tiller_width'],
                    params['stringer_base_level'] + params['tiller_width'] / 2),
        tiller_rod_rotation)

    tiller_rod_knob = the_rudder.newObject("Part::Feature", "Tiller_Rod_Knob (aluminum)")
    tiller_rod_knob.Shape = Part.makeSphere(params['tiller_rod_diameter'] * 2)
    tiller_rod_knob.Placement = FreeCAD.Placement(
        Base.Vector(params['tiller_length'] - params['tiller_width'] * 2,
                    - params['tiller_width'] + params['tiller_rod_length'],
                    params['stringer_base_level'] + params['tiller_width'] / 2),
        tiller_rod_rotation)
    
    # steel ribs (rods) for rudder
    rib_spacing = ((params['rudder_blade_height'] - 2 * params['rudder_rim'])
                   / (params['rudder_ribs'] - 1))
    for i in range(0, params['rudder_ribs']):
        rib = the_rudder.newObject("Part::Feature", f"Rudder_Rib_{i} (steel)")
        rib.Shape = Part.makeCylinder(params['rudder_rib_diameter'] / 2,
                                      params['rudder_rib_length'])
        rib.Placement = FreeCAD.Placement(
            Base.Vector(0,
                        params['rudder_rib_length'] / 2,
                        params['rudder_rim'] + i * rib_spacing
                        + z_offset
                        - params['rudder_blade_height']),
            FreeCAD.Rotation(Base.Vector(1, 0, 0), 90))

    # blade: thin sheet to indicate the shape of rudder
    blade = the_rudder.newObject("Part::Feature", "Rudder_Blade (plywood)")
    blade.Shape = Part.makeBox(params['rudder_blade_thickness'],
                               params['rudder_blade_length'],
                               params['rudder_blade_height'])
    blade.Placement = FreeCAD.Placement(
        Base.Vector(- params['rudder_blade_thickness'] / 2,
                    - params['rudder_blade_length'] / 2,
                    z_offset - params['rudder_blade_height']),
        FreeCAD.Rotation(Base.Vector(0, 0, 0), 0))
    
