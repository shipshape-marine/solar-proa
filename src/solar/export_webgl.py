# FreeCADCmd — no GUI, no ImportGui, no offscreen tricks
import FreeCAD as App
import Mesh

import Arch


doc = App.openDocument(r"C:/Users/phert/OneDrive - National University of Singapore/fyp/solar-proa/artifact/rp2.closehaul.design.FCStd")
objs = [o for o in doc.Objects if hasattr(o, "Shape") and not o.Shape.isNull()]
Mesh.export(objs, "src/solar/model.obj")