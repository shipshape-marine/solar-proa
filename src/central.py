# all parts that are mirrored about the transversal axis

import FreeCAD
import Part
from FreeCAD import Base
import math

from parameters import *
from shapes import *
from material import *

def single(boat):

    # spine (longitudinal beam to support the akas)

    spine = boat.addObject("Part::Feature", "Spine (aluminum)")
    spine.Shape = shs_capped(spine_width,
                             spine_thickness,
                             spine_length,
                             aka_cap_diameter,
                             aka_cap_thickness)
                             
    spine.Placement = FreeCAD.Placement(
        Base.Vector(- spine_width / 2, spine_length / 2, spine_base_level),
        FreeCAD.Rotation(Base.Vector(1, 0, 0), 90))
    set_color(spine, color_aluminum)

    # make a box for the cockpit to cut
    
    cockpit_cutter = Part.makeBox(
        vaka_width + 1000, 
        cockpit_length,
        overhead_thickness + 100)
    cockpit_cutter_placement = FreeCAD.Placement(
        Base.Vector(vaka_displacement - vaka_width - 500,
                    - cockpit_length / 2,
                    freeboard - 50), 
        FreeCAD.Rotation(Base.Vector(0, 0, 0), 0))
    cockpit_cutter_transformed = cockpit_cutter.transformGeometry(
        cockpit_cutter_placement.toMatrix())
    
    # overhead (ceiling of cabin)
    
    overhead = boat.addObject("Part::Feature", "Overhead (plywood)")
    overhead.Shape = elliptical_cylinder(vaka_length,
                                         vaka_width,
                                         overhead_thickness)
    overhead.Placement = FreeCAD.Placement(
        Base.Vector(vaka_displacement, 0, freeboard),
        FreeCAD.Rotation(Base.Vector(0, 0, 1), 90))
    overhead.Shape = overhead.Shape.cut(cockpit_cutter_transformed)
    set_color(overhead, color_plywood)

    # sole: floor of boat
    
    sole = boat.addObject("Part::Feature", "Sole")
    # Create the flat sole cylinder
    sole_cylinder = elliptical_cylinder(vaka_length,
                                        vaka_width,
                                        sole_thickness)
    # Create an ellipsoid with same length/width, but height = 2 * sole_thickness
    # This will create a curved bottom shape
    bottom_ellipsoid = ellipsoid(vaka_length, 
                                 vaka_width, 
                                 2 * sole_thickness)
    # Position the ellipsoid so its top half intersects with the sole cylinder
    # The ellipsoid center is at (0,0,0), and its height is 2*sole_thickness
    # So its top is at z = sole_thickness
    # We want the ellipsoid centered so it creates a nice curve
    ellipsoid_placement = Base.Matrix()
    ellipsoid_placement.move(Base.Vector(0, 0, sole_thickness))
    bottom_ellipsoid_positioned = bottom_ellipsoid.transformGeometry(ellipsoid_placement)
    # Intersect the cylinder with the ellipsoid to get the curved bottom
    sole.Shape = sole_cylinder.common(bottom_ellipsoid_positioned)
    sole.Placement = FreeCAD.Placement(
        Base.Vector(vaka_displacement, 0, 0),
        FreeCAD.Rotation(Base.Vector(0, 0, 1), 90))
    set_color(sole, color_sole)

    hull = boat.addObject("Part::Feature", "Hull")
    hull.Shape = elliptical_pipe(vaka_length, vaka_width,
                                 vaka_thickness, freeboard - sole_thickness)
    hull.Placement = FreeCAD.Placement(
        Base.Vector(vaka_displacement, 0, sole_thickness),
        FreeCAD.Rotation(Base.Vector(0, 0, 1), 90))
    set_color(hull, color_hull_exterior)

    gunwale = boat.addObject("Part::Feature", "Gunwale")
    gunwale.Shape = elliptical_pipe(vaka_length, vaka_width,
                                    gunwale_width, gunwale_height)
    gunwale.Placement = FreeCAD.Placement(
        Base.Vector(vaka_displacement, 0, freeboard - gunwale_height),
        FreeCAD.Rotation(Base.Vector(0, 0, 1), 90))
    set_color(gunwale, color_hull_exterior)

    outer_crossdeck_stanchion = boat.addObject("Part::Feature",
                                              f"Outer_Crossdeck_Stanchion (aluminum)")
    outer_crossdeck_stanchion.Shape = pipe(stanchion_diameter,
                                           stanchion_thickness,
                                           stanchion_length)
    outer_crossdeck_stanchion.Placement = FreeCAD.Placement(
        Base.Vector(0,
                    0,
                    aka_base_level),
        FreeCAD.Rotation(Base.Vector(0, 0, 0), 0))
    set_color(outer_crossdeck_stanchion, color_aluminum)

    center_crossdeck_stanchion = boat.addObject("Part::Feature",
                                               f"Center_Crossdeck_Stanchion (aluminum)")
    center_crossdeck_stanchion.Shape = pipe(stanchion_diameter,
                                            stanchion_thickness,
                                            stanchion_length)
    center_crossdeck_stanchion.Placement = FreeCAD.Placement(
        Base.Vector(crossdeck_length / 2,
                    0,
                    aka_base_level),
        FreeCAD.Rotation(Base.Vector(0, 0, 0), 0))
    set_color(center_crossdeck_stanchion, color_aluminum)
