#!/bin/bash
# Apply power cables to FreeCAD design (macOS - GUI mode required)
#
# macOS requires GUI mode to properly persist ViewObject properties (if needed).
# This script opens the design in FreeCAD GUI, applies cables, saves, and quits.

# Default FreeCAD path
FREECAD="/Applications/FreeCAD.app/Contents/MacOS/FreeCAD"

# Parse named arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --design)
            INPUT_FCSTD="$2"
            shift 2
            ;;
        --params)
            PARAMS_JSON="$2"
            shift 2
            ;;
        --outputdesign)
            OUTPUT_FCSTD="$2"
            shift 2
            ;;
        --freecad)
            FREECAD="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 --design <input.FCStd> --params <params.json> --outputdesign <output.FCStd> [--freecad <path>]"
            exit 1
            ;;
    esac
done

# Validate required arguments
if [ -z "$INPUT_FCSTD" ] || [ -z "$PARAMS_JSON" ] || [ -z "$OUTPUT_FCSTD" ]; then
    echo "Usage: $0 --design <input.FCStd> --params <params.json> --outputdesign <output.FCStd> [--freecad <path>]"
    exit 1
fi
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ ! -f "$INPUT_FCSTD" ]; then
    echo "ERROR: Input file not found: $INPUT_FCSTD"
    exit 1
fi

if [ ! -f "$PARAMS_JSON" ]; then
    echo "ERROR: Params file not found: $PARAMS_JSON"
    exit 1
fi

# Create temporary Python script
TEMP_SCRIPT=$(mktemp /tmp/freecad_cables_XXXXXX.py)

cat > "$TEMP_SCRIPT" << 'EOFPYTHON'
import sys
import os
import json
import FreeCAD as App

# Get arguments
script_dir = sys.argv[-4]
input_fcstd = sys.argv[-3]
params_json = sys.argv[-2]
output_fcstd = sys.argv[-1]

# Add script directory to path to find wiring module
sys.path.append(script_dir)

try:
    from wiring import wire_solar_panels
except ImportError as e:
    print(f"ERROR: Could not import wiring module: {e}")
    # We can't easily exit with error code from GUI mode that propagates to shell,
    # but we can print error and try to exit.
    import os
    os._exit(1)

print(f"Loading params: {params_json}")
with open(params_json, 'r') as f:
    params = json.load(f)

print(f"Opening design: {input_fcstd}")
doc = App.openDocument(input_fcstd)

print("Adding power cables...")
try:
    wire_solar_panels(doc, params=params)
    doc.recompute()
    
    print(f"Saving design: {output_fcstd}")
    doc.saveAs(output_fcstd)
    print("✓ Power cables application complete")

except Exception as e:
    print(f"ERROR: Failed to apply cables: {e}")

App.closeDocument(doc.Name)
import os
os._exit(0)
EOFPYTHON

# Run FreeCAD with the script
echo "Running FreeCAD to apply power cables..."
"$FREECAD" "$TEMP_SCRIPT" "$SCRIPT_DIR" "$INPUT_FCSTD" "$PARAMS_JSON" "$OUTPUT_FCSTD" &
FREECAD_PID=$!

# Wait up to 60 seconds for completion
for i in {1..120}; do
    if ! kill -0 $FREECAD_PID 2>/dev/null; then
        break
    fi
    sleep 0.5
done

# Force kill if still running
if kill -0 $FREECAD_PID 2>/dev/null; then
    echo "Warning: FreeCAD did not exit cleanly, forcing..."
    kill -9 $FREECAD_PID 2>/dev/null
fi

# Clean up
rm -f "$TEMP_SCRIPT"

# Verify output was created
if [ ! -f "$OUTPUT_FCSTD" ]; then
    echo "ERROR: Output design was not created"
    exit 1
fi

echo "✓ Power cables application complete"
