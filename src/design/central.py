# all parts that are central (symmetric along the transversal axis)
# vaka, ama spine, sole, overhead, central stanchions

import FreeCAD
import Part
from FreeCAD import Base
import math

from shapes import *

def central(vessel, params):

    # spine (longitudinal beam to support the akas)

    spine = vessel.newObject("Part::Feature", "Spine (aluminum)")
    spine.Shape = shs(params['spine_width'],
                             params['spine_thickness'],
                             params['spine_length'])
                             
    spine.Placement = FreeCAD.Placement(
        Base.Vector(- params['spine_width'] / 2, params['spine_length'] / 2, params['spine_base_level']),
        FreeCAD.Rotation(Base.Vector(1, 0, 0), 90))

    # make a box for the cockpit to cut
    
    cockpit_cutter = Part.makeBox(
        params['vaka_width'] + 1000, 
        params['cockpit_length'],
        params['overhead_thickness'] + 100)
    cockpit_cutter_placement = FreeCAD.Placement(
        Base.Vector(params['vaka_x_offset'] - params['vaka_width'] - 500,
                    - params['cockpit_length'] / 2,
                    params['overhead_base_level'] - 50), 
        FreeCAD.Rotation(Base.Vector(0, 0, 0), 0))
    cockpit_cutter_transformed = cockpit_cutter.transformGeometry(
        cockpit_cutter_placement.toMatrix())
    
    # overhead (ceiling of cabin)
    
    overhead = vessel.newObject("Part::Feature", "Overhead (plywood)")
    overhead.Shape = elliptical_cylinder(params['vaka_length'],
                                         params['vaka_width'],
                                         params['overhead_thickness'])
    overhead.Placement = FreeCAD.Placement(
        Base.Vector(params['vaka_x_offset'], 0, params['overhead_base_level']),
        FreeCAD.Rotation(Base.Vector(0, 0, 1), 90))
    overhead.Shape = overhead.Shape.cut(cockpit_cutter_transformed)

    # bottom: part of the hull below the sole
    bottom = vessel.newObject("Part::Feature", "Bottom (fiberglass_bottom)")
    # Create the flat bottom cylinder to cut from bottom
    bottom_cylinder = elliptical_cylinder(params['vaka_length'] + 5,
                                          params['vaka_width'] + 5,
                                          params['bottom_height'] + 5)
    # Create an ellipsoid for bottom, height = 2 * bottom_thickness
    # This will create a curved bottom shape
    bottom_ellipsoid = ellipsoid(params['vaka_length'], 
                                 params['vaka_width'], 
                                 params['bottom_height'] * 2)
    bottom_ellipsoid_inner = ellipsoid(
        params['vaka_length'] - 2 * params['bottom_thickness'], 
        params['vaka_width'] - 2 * params['bottom_thickness'], 
        params['bottom_height'] * 2 - 2 * params['bottom_thickness'])
    # Intersect the cylinder with the ellipsoid to get the curved bottom
    bottom.Shape = (bottom_ellipsoid.cut(bottom_cylinder)
                    .cut(bottom_ellipsoid_inner))
    bottom.Placement = FreeCAD.Placement(
        Base.Vector(params['vaka_x_offset'], 0, params['bottom_height']),
        FreeCAD.Rotation(Base.Vector(0, 0, 1), 90))

    # foam_below_sole 
    foam_below_sole = vessel.newObject("Part::Feature", "Foam_Below_Sole (foam)")
    foam_below_sole.Shape = bottom_ellipsoid_inner.cut(bottom_cylinder)
    foam_below_sole.Placement = FreeCAD.Placement(
        Base.Vector(params['vaka_x_offset'], 0, params['bottom_height']),
        FreeCAD.Rotation(Base.Vector(0, 0, 1), 90))
    
    # sole: floor of cabin
    sole = vessel.newObject("Part::Feature", "Sole (plywood)")
    # Create the flat bottom cylinder to cut from bottom
    sole.Shape = elliptical_cylinder(params['vaka_length'] - 2 * params['vaka_thickness'],
                                     params['vaka_width'] - 2 * params['vaka_thickness'],
                                     params['sole_thickness'])
    sole.Placement = FreeCAD.Placement(
        Base.Vector(params['vaka_x_offset'], 0, params['bottom_height']),
        FreeCAD.Rotation(Base.Vector(0, 0, 1), 90))
    
    # hull: exterior from sole base level (bottom height) upwards
    #       to clamp base level
    hull = vessel.newObject("Part::Feature", "Hull (fiberglass)")
    hull.Shape = elliptical_pipe(params['vaka_length'],
                                 params['vaka_width'],
                                 params['vaka_thickness'],
                                 params['freeboard'])
    hull.Placement = FreeCAD.Placement(
        Base.Vector(params['vaka_x_offset'], 0, params['bottom_height']),
        FreeCAD.Rotation(Base.Vector(0, 0, 1), 90))

    # air_inside_vaka: trapped air volume inside cabin (for buoyancy calculation)
    # This represents the air from sole top to overhead bottom, including cockpit
    air_inside_height = (params['overhead_base_level']
                         - params['bottom_height']
                         - params['sole_thickness'])
    air_inside_vaka = vessel.newObject("Part::Feature", "Air_Inside_Vaka (air)")
    air_inside_vaka.Shape = elliptical_cylinder(
        params['vaka_length'] - 2 * params['vaka_thickness'],
        params['vaka_width'] - 2 * params['vaka_thickness'],
        air_inside_height)
    air_inside_vaka.Placement = FreeCAD.Placement(
        Base.Vector(params['vaka_x_offset'],
                    0,
                    params['bottom_height'] + params['sole_thickness']),
        FreeCAD.Rotation(Base.Vector(0, 0, 1), 90))

    clamp = vessel.newObject("Part::Feature", "Clamp (wood)")
    clamp.Shape = elliptical_pipe(params['vaka_length'] - params['vaka_thickness'],
                                    params['vaka_width'] - params['vaka_thickness'],
                                    params['clamp_width'],
                                    params['clamp_height'])
    clamp.Placement = FreeCAD.Placement(
        Base.Vector(params['vaka_x_offset'],
                    0,
                    params['clamp_base_level']),
        FreeCAD.Rotation(Base.Vector(0, 0, 1), 90))

    vaka_stringer = vessel.newObject("Part::Feature", "Vaka_Stringer (wood)")
    vaka_stringer.Shape = elliptical_pipe(params['vaka_length'] - params['vaka_thickness'],
                                          params['vaka_width'] - params['vaka_thickness'],
                                          params['vaka_stringer_width'],
                                          params['vaka_stringer_height'])
    vaka_stringer.Placement = FreeCAD.Placement(
        Base.Vector(params['vaka_x_offset'],
                    0,
                    params['vaka_stringer_base_level']),
        FreeCAD.Rotation(Base.Vector(0, 0, 1), 90))

    outer_crossdeck_stanchion = vessel.newObject("Part::Feature",
                                              "Outer_Crossdeck_Stanchion (steel)")
    outer_crossdeck_stanchion.Shape = pipe(params['stanchion_diameter'],
                                           params['stanchion_thickness'],
                                           params['stanchion_length'])
    outer_crossdeck_stanchion.Placement = FreeCAD.Placement(
        Base.Vector(0,
                    0,
                    params['aka_base_level']),
        FreeCAD.Rotation(Base.Vector(0, 0, 0), 0))

    center_crossdeck_stanchion = (
        vessel.newObject("Part::Feature",
                         "Center_Crossdeck_Stanchion (aluminum)"))
    center_crossdeck_stanchion.Shape = pipe(params['stanchion_diameter'],
                                            params['stanchion_thickness'],
                                            params['stanchion_length'])
    center_crossdeck_stanchion.Placement = FreeCAD.Placement(
        Base.Vector(params['crossdeck_length'] / 2,
                    0,
                    params['aka_base_level']),
        FreeCAD.Rotation(Base.Vector(0, 0, 0), 0))

    motor_backing_plate = (
        vessel.newObject("Part::Feature",
                         "Motor_Backing_Plate (aluminum)"))
    motor_backing_plate.Shape = Part.makeBox(
        params['motor_backing_plate_thickness'] * 2 +
        params['vaka_thickness'],
        params['motor_backing_plate_length'],
        params['motor_backing_plate_height'])
    motor_backing_plate.Placement = FreeCAD.Placement(
        Base.Vector(params['vaka_x_offset']
                    - params['vaka_width'] / 2
                    - params['motor_backing_plate_thickness'],
                    - params['motor_backing_plate_length'] / 2,
                    params['motor_backing_plate_above_sole']),
        FreeCAD.Rotation(Base.Vector(0, 0, 0), 0))

    side_board_plate = (
        vessel.newObject("Part::Feature",
                         "Side_Board_Plate (aluminum)"))
    side_board_plate.Shape = Part.makeBox(
        params['side_board_plate_thickness'] * 2 +
        params['vaka_thickness'],
        params['side_board_plate_length'],
        params['side_board_plate_height'])
    side_board_plate.Placement = FreeCAD.Placement(
        Base.Vector(params['vaka_x_offset'] + params['vaka_width'] / 2
                    - params['side_board_plate_thickness']
                    - params['vaka_thickness'],
                    - params['side_board_plate_length'] / 2,
                    params['side_board_plate_above_sole']),
        FreeCAD.Rotation(Base.Vector(0, 0, 0), 0))


