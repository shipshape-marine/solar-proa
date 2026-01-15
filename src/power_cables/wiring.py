import Part


def create_sweep(group, profile, radius, vertices, name="SweepObject"):
    """Creates a swept solid given a profile (cross section) and list of vertices representing the bends""" 
    edges: list[tuple[Part.Edge, str]] = []
    for i in range(len(vertices) - 1):
        start = vertices[i]
        end = vertices[i+1]
        line = Part.makeLine(start, end)
        edges.append((line, f"Edge_{i+1}"))
        print(f"Created edge {i} from {start} to {end}")

    path_obj = group.newObject("Part::Feature", f"{name}Path")
    path_obj.Shape = Part.Wire([edge[0] for edge in edges])

    if profile.lower() == "circle":
        # creating a profile for every sweep is inefficient, add functionality for reusing profile?
        direction = edges[0][0].tangentAt(0)
        print(f"Sweep direction: {direction}")
        profile_shape = Part.makeCircle(radius, edges[0][0].valueAt(0), direction)
        profile_obj = group.newObject("Part::Feature", f"{name}Profile")
        profile_obj.Shape = Part.Wire(profile_shape)
        print(f"Created circular profile with radius {radius}")
    
    else:
        raise ValueError(f"Profile type '{profile}' is not supported.")

    sweep = group.newObject("Part::Sweep", name)
    sweep.Sections = [profile_obj]
    sweep.Spine = (path_obj, [edge[1] for edge in edges])
    sweep.Solid = True
    sweep.Frenet = True
    sweep.Transition = 'Round corner'

    return sweep