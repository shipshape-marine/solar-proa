import schemdraw
import schemdraw.elements as elm
from schemdraw.util import Point

from Array_Creator import draw_array
from components.MPPT import MPPT
from configurations.constants import TERMINATING_DISTANCE

drawing = schemdraw.Drawing()
drawing.config(unit=2)  # default .length( units )

drawing, (top, bottom) = draw_array(drawing=drawing, element=elm.Battery, \
    terminateDist=TERMINATING_DISTANCE, series=2, parallel=2, isRight=True)


solar_mppt_point = Point((bottom.end.x, bottom.end.y - TERMINATING_DISTANCE / 2))
mppt = MPPT(pin_gap=TERMINATING_DISTANCE).at(solar_mppt_point).label('MPPT1')
drawing.add(mppt)
drawing.draw()

