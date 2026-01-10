# colors.py - Legacy stub for backward compatibility
#
# Color management has been moved to the color module (src/color/).
# This file provides no-op functions so existing design generation code
# doesn't break, but actual color application happens in a separate step
# after design generation is complete.
#
# Color application workflow:
#   1. design.py generates uncolored *.design.FCStd
#   2. color module reads color scheme JSON and applies colors
#   3. Produces *.color.FCStd with proper colors
#
# See src/color/README.md for details.

def set_color(obj, color):
    """
    No-op function for backward compatibility.
    
    Colors are now applied by the color module after design generation.
    This function is kept to avoid breaking existing design generation code.
    """
    pass

