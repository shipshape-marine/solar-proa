import sys
import os

# FreeCAD puts its own arguments first, macro arguments come after the macro filename
# Find where the macro name is and take arguments after that
macro_args = []
for i, arg in enumerate(sys.argv):
    if arg.endswith('.FCMacro'):
        macro_args = sys.argv[i+1:]
        break

# Get parameter file from command line, default to RP2
param_file = macro_args[0] if macro_args else 'boats.RP2'

# Import the specified parameters
if param_file in sys.modules:
    del sys.modules[param_file]

# Create an alias so other modules can import 'parameters'
import importlib
try:
    params_module = importlib.import_module(param_file)
    sys.modules['parameters'] = params_module
    print(f"DEBUG: Successfully imported {param_file}")
except Exception as e:
    print(f"ERROR importing {param_file}: {e}")
    raise

# Now import into global namespace
exec(f"from {param_file} import *")
