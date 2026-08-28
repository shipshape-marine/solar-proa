import FreeCAD as App

doc = App.openDocument("C:/Users/phert/OneDrive - National University of Singapore/fyp/solar-proa/artifact/rp2.closehaul.design.FCStd")

sails = []
panels = []
masts = []

# for obj in doc.Objects:
#     if not hasattr(obj, "Shape"):
#         continue

#     if obj.Shape.isNull():
#         continue

#     if obj.Label.startswith("Sail"):
#         sails.append(obj)

#     elif obj.Label.startswith("Panel_"):
#         panels.append(obj)

#     elif obj.Label.startswith("Mast") or obj.Label.contains(""):
#         masts.append(obj)
    

tesselated = []
print(len(doc.Objects))
for obj in doc.Objects:
    if not hasattr(obj, "Shape"):
        continue
    vertices, triangles = obj.Shape.tessellate(5)



print(list(map(lambda x: x.Placement, sails)))
print(list(map(lambda x: x.Placement, panels)))
print(list(map(lambda x: x.Label, masts)))

sail = sails[0]
shape = sail.Shape
tolerance_mm = 5.0

vertices, triangles = sail.Shape.tessellate(tolerance_mm)
print(vertices)

print("Shape type:", shape.ShapeType)
print("Vertices:", len(shape.Vertexes))
print("Edges:", len(shape.Edges))
print("Faces:", len(shape.Faces))
print("Solids:", len(shape.Solids))
print("Area:", shape.Area)
print("Volume:", shape.Volume)
print("Bounding box:", shape.BoundBox)




from datetime import date, datetime, timedelta, timezone
import math

import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.widgets import Slider, TextBox
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np


