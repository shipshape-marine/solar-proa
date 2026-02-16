import Part
import FreeCAD
from FreeCAD import Base


#TODO: Avoid using object names ("panel"), calculate placements directly from parameters

def create_sweep(group, profile, radius, vertices, name="SweepObject", color=(0.0, 0.0, 0.0)):
    """Creates a swept solid given a profile (cross section) and list of vertices representing the bends""" 
    edges: list[tuple[Part.Edge, str]] = []
    for i in range(len(vertices) - 1):
        start = vertices[i]
        end = vertices[i+1]
        line = Part.makeLine(start, end)
        edges.append((line, f"Edge_{i+1}"))
        print(f"Created edge {i} from {start} to {end}")

    path_obj = group.addObject("Part::Feature", f"{name}Path")
    path_obj.Shape = Part.Wire([edge[0] for edge in edges])

    if profile.lower() == "circle":
        # creating a profile for every sweep is inefficient, add functionality for reusing profile?
        direction = edges[0][0].tangentAt(0)
        # print(f"Sweep direction: {direction}")
        profile_shape = Part.makeCircle(radius, edges[0][0].valueAt(0), direction)
        profile_obj = group.addObject("Part::Feature", f"{name}Profile")
        profile_obj.Shape = Part.Wire(profile_shape)
        # print(f"Created circular profile with radius {radius}")
    
    else:
        raise ValueError(f"Profile type '{profile}' is not supported.")

    sweep = group.addObject("Part::Sweep", name)
    sweep.Sections = [profile_obj]
    sweep.Spine = (path_obj, [edge[1] for edge in edges])
    sweep.Solid = True
    sweep.Frenet = True
    sweep.Transition = 'Round corner'

    if hasattr(sweep, "ViewObject"):
        sweep.ViewObject.ShapeColor = color

    return sweep

def generate_panel_matrix(params):
    """
    Generates a matrix of solar panel placements based on parameters from src/design/mirror.py.
    
    Each element in the matrix represents a panel and is a tuple of tuples: 
    ((start_x, end_x), (start_y, end_y), (start_z, end_z)).
    """
    panel_matrix = []
    
    required_params = ['panels_longitudinal', 'panels_transversal', 'pillar_width', 'panel_length', 'crossdeck_width', 'panel_width', 'panel_base_level', 'panel_height']
    if not all(k in params for k in required_params):
        print("Warning: Missing one or more parameters for panel matrix generation. Wiring may be incomplete.")
        return panel_matrix

    rows = params.get('panels_longitudinal', 0) // 2
    cols = params.get('panels_transversal', 0)

    for i in range(rows):
        row_placements = []
        for j in range(cols):
            x_pos = -params['pillar_width'] / 2 + j * params['panel_length']
            y_pos = params['crossdeck_width'] / 2 + i * params['panel_width']
            z_pos = params['panel_base_level']

            start_x = x_pos
            end_x = x_pos + params['panel_length']
            
            start_y = y_pos
            end_y = y_pos + params['panel_width']
            
            start_z = z_pos
            end_z = z_pos + params['panel_height']
            
            placement = ((start_x, end_x), (start_y, end_y), (start_z, end_z))
            row_placements.append(placement)
        panel_matrix.append(row_placements)
        
    return panel_matrix

def get_connection_points(panel_matrix):
    """
    Computes the connection points (positive & negative) for wiring based on the panel matrix.

    """
    if not panel_matrix or not panel_matrix[0]:
        raise ValueError("Panel matrix is empty or malformed.")

    positive_connections = []
    negative_connections = []

    z_level = panel_matrix[0][0][2][0]  # Base z-level of the first panel
    for row in panel_matrix:
        temp_pos = []
        temp_neg = []
        for panel in row:
            (start_x, end_x), (start_y, end_y), _ = panel
            y_pos, y_neg = (end_y - start_y) / 3 + start_y, (end_y - start_y) / 3 * 2 + start_y
            x = (end_x - start_x) / 3 + start_x

            temp_pos.append((x, y_pos, z_level))
            temp_neg.append((x, y_neg, z_level))

        positive_connections.append(temp_pos)
        negative_connections.append(temp_neg)
    return positive_connections, negative_connections

def wire_solar_panels(group, radius=5, params={}, string_direction='transverse'):
    """
    Generates wiring for all solar panels on both sides of the boat.
    
    Args:
        group: The FreeCAD Document or Group object to add wires to.
        radius: Radius of the wire sweep.
        params: Dictionary of parameters for panel layout.
    """
    
    # Wire colors to be used
    BLUE = (0.0, 0.0, 1.0)
    RED = (1.0, 0.0, 0.0)
    PURPLE  = (1.0, 0.0, 1.0)


    biru_side_matrix = generate_panel_matrix(params)[::-1]

    kuning_side_matrix = []
    for row in biru_side_matrix[::-1]:  # Reverse for proper ordering after reflection
        mirrored_row = []
        for placement in row:
            (start_x, end_x), (start_y, end_y), (start_z, end_z) = placement
            # Reflect across XZ plane (y -> -y)
            mirrored_placement = ((start_x, end_x), (-end_y, -start_y), (start_z, end_z))
            mirrored_row.append(mirrored_placement)
        kuning_side_matrix.append(mirrored_row)
    
    panel_matrix = biru_side_matrix + kuning_side_matrix

    if not panel_matrix:
        print("Panel matrix is empty, no wires to create.")
        return

    print(f"Generated a {len(panel_matrix)}x{len(panel_matrix[0]) if panel_matrix and panel_matrix[0] else 0} panel matrix for wiring both sides.")

    if not panel_matrix[0]:
        return

    # Get positive and negative endpoints for each panel
    positive_connections, negative_connections = get_connection_points(panel_matrix)

    # Draw wires
    dummy_positive_end = Base.Vector(0, 100, -100)
    dummy_negative_end = Base.Vector(0, -100, -100)

    # Draw central wire
    central_x = panel_matrix[0][1][0][1] + params['deck_width'] / 3  # Place in the middle of the deck
    central_y_start = panel_matrix[0][0][1][1]
    central_y_end = panel_matrix[-1][0][1][0]
    central_z = params['deck_level'] / 2

    central_start = Base.Vector(central_x, central_y_start, central_z)
    central_end = Base.Vector(central_x, central_y_end, central_z)

    create_sweep(group, "circle", radius, [central_start, central_end], name="Central_Wire")

    k = params['panels_per_string']
    prev_point = None
    counter = 0

    for i, panel_row in enumerate(panel_matrix):
        for j, panel in enumerate(panel_row):
            if i % 2 == 1:
                j = (len(panel_row) - 1) - j  # Reverse order for every second row

            if counter % k == 0:
                # Start of a new string, connect from central to positive end
                panel_positive = positive_connections[i][j]
                bend = Base.Vector(panel_positive[0], panel_positive[1], central_z)
                central_point = Base.Vector(central_x, panel_positive[1], central_z)
                wire_name = f"Panel_Wire_Pos_{i}_{j}"
                prev_point = negative_connections[i][j]
                color = RED

                create_sweep(group, "circle", radius, [panel_positive, bend, central_point], name=wire_name, color=color) # Blue wire


            else:
                if (counter % k) == (k - 1):
                    # End of a string, connect to negative end in central
                    panel_negative = negative_connections[i][j]
                    bend = Base.Vector(panel_negative[0], panel_negative[1], central_z)
                    central_point = Base.Vector(central_x, panel_negative[1], central_z)
                    wire_name = f"Panel_Wire_Neg_{i}_{j}"
                    color = BLUE

                    create_sweep(group, "circle", radius, [panel_negative, bend, central_point], name=wire_name, color=color) # Blue wire

                # Connnect two panels
                start_point = prev_point
                end_point = positive_connections[i][j]
                wire_name = f"Panel_Wire_Neg_to_Pos{i}_{j}"
                prev_point = negative_connections[i][j]
                color = PURPLE
            
                create_sweep(group, "circle", radius, [start_point, end_point], name=wire_name, color=color)

            counter += 1
