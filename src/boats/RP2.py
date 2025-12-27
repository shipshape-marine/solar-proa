# sailing parameters: set by the functions in sailing.py
sail_camber = 10000
biru_rig_rotation = 0
biru_sail_angle = 0
kuning_rig_rotation = 0
kuning_sail_angle = 0

# number of solar panels
panels_longitudinal = 6
panels_transversal =  2

# number of deck stringers
deck_stringers = 4

# parameters; all in mm

mm_in_one_inch = 25.4

panel_length = 1762
panel_width = 1134
panel_height = 30

deck_width = 2000
deck_thickness = 9

ama_diameter = 370
ama_thickness = 10
ama_length = 9000
ama_cone_length = 1000

stringer_width = 25
stringer_thickness = 3

aka_width = 76.2
aka_height = 101.6
aka_thickness = 4.5
aka_length = panel_length * panels_transversal + deck_width

aka_cap_thickness = 5
aka_cap_diameter = 170

vaka_length = 9000
vaka_width = 1150
vaka_thickness = 5

overhead_thickness = 3
sole_thickness = 300

crossdeck_width = 900
crossdeck_thickness = deck_thickness
crossdeck_length = (panels_transversal * panel_length +
                  (deck_width - vaka_width) / 2 +
                  stringer_width)

cockpit_length = panel_width + crossdeck_width - aka_width


panel_stringer_offset = panel_length / 4 - stringer_width / 2
panel_stringer_length = crossdeck_width + panels_longitudinal * panel_width

freeboard = 1200
aka_base_level = freeboard + overhead_thickness
stringer_base_level = aka_base_level + aka_height
panel_base_level = stringer_base_level + stringer_width
deck_base_level = panel_base_level
deck_level = deck_base_level + deck_thickness

stanchion_diameter = 20
stanchion_length = 600
stanchion_thickness = 3

# in this design, akas, spine and pillars are all made
# from the same SHS sizes

spine_thickness = aka_thickness
spine_width = aka_width
spine_base_level = aka_base_level - spine_width
spine_length = panel_width * panels_longitudinal + crossdeck_width

pillar_thickness = aka_thickness
pillar_width = aka_width
pillar_height = spine_base_level - ama_thickness

# Cross-bracing between pillars (X-shaped reinforcements)
brace_diameter = 5  # thin aluminum rod/wire
brace_upper_offset = 100  # distance from spine to upper corners of X
brace_lower_offset = 400  # distance from ama to lower corners of X

# Pillar-to-aka diagonal braces (triangulation)
pillar_brace_vertical_offset = 500  # vertical distance down pillar from aka base level

# distance from the center line of ama to center line of vaka
vaka_displacement = (- pillar_width / 2
                     + panel_length * panels_transversal
                     + deck_width / 2)

gunwale_width = 3 * mm_in_one_inch
gunwale_height = 2 * mm_in_one_inch

mast_diameter = 152.4
mast_thickness = 6.35
mast_height = 8500
mast_distance_from_center = vaka_length / 4 + 120 # adjustment to not cut into aka

mast_partner_length = vaka_width - 110
mast_partner_width = mast_diameter + 200
mast_partner_thickness = 50

mast_step_outer_diameter = mast_diameter + 100
mast_step_inner_diameter = mast_diameter
mast_step_thickness = 100

mast_handle_diameter = 25
mast_handle_thickness = 3
mast_handle_length = 600
mast_handle_height_above_deck = 600

mast_cap_thickness = 3
mast_cap_diameter = 150

yard_spar_length = 500
yard_spar_width = 50
yard_spar_thickness = 10
yard_spar_distance_from_top = 500
yard_spar_height = mast_height - yard_spar_distance_from_top

# Sail parameters (tanja sail)
yard_diameter = 63.5
yard_thickness = 2.8
yard_length = 5500

boom_diameter = yard_diameter
boom_thickness = yard_thickness
boom_length = yard_length

sail_height = 5500  # vertical distance between yard and boom
sail_width  = yard_length
sail_thickness = 2  # thin membrane

# Colors (RGB values from 0.0 to 1.0)
color_deck = (0.68, 0.85, 0.90)  # light blue
color_solar_panel = (0.3, 0.3, 0.3)  # dark grey
color_aluminum = (0.75, 0.75, 0.78)  # aluminum
color_hull_interior = (0.5, 0.5, 0.5)  # grey
color_hull_exterior = (1.0, 1.0, 1.0)  # white
color_sole = (0.9, 0.1, 0.1)  # spinnaker red
color_plywood = (0.76, 0.60, 0.42)  # light brown (plywood)
color_bamboo = (0.86, 0.70, 0.52)  # light brown (bamboo)
color_sail = (0.95, 0.95, 0.88)  # off-white/cream for sail
color_ama = (1.0, 1.0, 1.0)  # white

material_colors = {
    'Plywood': (0.76, 0.60, 0.42),
    'Bamboo': (0.86, 0.70, 0.52),
    'Aluminum': (0.75, 0.75, 0.78),
    'PVC': (1.0, 1.0, 1.0)
}

def set_material(obj, material):
    """Set material properties on an object"""
    if not hasattr(obj, 'Material'):
        obj.addProperty("App::PropertyMap", "Material", "Material", "Material properties")
    
    # Convert all values to strings for PropertyMap
    material_str = {k: str(v) for k, v in material.items()}
    obj.Material = material_str

def set_color(obj, color):
    """Set color on a FreeCAD object"""
    obj.ViewObject.ShapeColor = color

# Materials following the Material module
