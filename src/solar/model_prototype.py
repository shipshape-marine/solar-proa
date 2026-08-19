"""Interactive prototype for sail shadows on solar panels.

The Sun position is calculated from latitude, longitude, local date/time, and
UTC offset. Geometry is deliberately simple; it can later be replaced by the
panel surfaces and triangular sail meshes extracted from FreeCAD.
"""

from datetime import date, datetime, timedelta, timezone
import math

import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.widgets import Slider, TextBox
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np


# Simplified boat dimensions in metres.
MAST_HEIGHT = 2.26 - 0.21
BOOM_HEIGHT = 0.25
BOOM_LENGTH = 2.00
MAST_POSITIONS = [(0.0, 0.0), (0.0, 2.05)]

SOLAR_PANELS = [
    [(0.25, -0.45), (2.00, -0.45), (2.00, 0.68), (0.25, 0.68)],
    [(0.25, 1.37), (2.00, 1.37), (2.00, 2.50), (0.25, 2.50)],
]

SHADOW_SAMPLE_RESOLUTION = 45


def calculate_fractional_year(timestamp: datetime) -> float:
    """Return NOAA's fractional-year angle in radians."""
    day_of_year = timestamp.timetuple().tm_yday
    decimal_hour = (
        timestamp.hour
        + timestamp.minute / 60
        + timestamp.second / 3600
        + timestamp.microsecond / 3_600_000_000
    )
    days_in_year = 366 if _is_leap_year(timestamp.year) else 365
    return (
        2.0
        * math.pi
        / days_in_year
        * (day_of_year - 1 + (decimal_hour - 12.0) / 24.0)
    )


def _is_leap_year(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def calculate_equation_of_time(fractional_year: float) -> float:
    """Return the equation-of-time correction in minutes."""
    gamma = fractional_year
    return 229.18 * (
        0.000075
        + 0.001868 * math.cos(gamma)
        - 0.032077 * math.sin(gamma)
        - 0.014615 * math.cos(2.0 * gamma)
        - 0.040849 * math.sin(2.0 * gamma)
    )


def calculate_solar_declination(fractional_year: float) -> float:
    """Return solar declination in radians."""
    gamma = fractional_year
    return (
        0.006918
        - 0.399912 * math.cos(gamma)
        + 0.070257 * math.sin(gamma)
        - 0.006758 * math.cos(2.0 * gamma)
        + 0.000907 * math.sin(2.0 * gamma)
        - 0.002697 * math.cos(3.0 * gamma)
        + 0.001480 * math.sin(3.0 * gamma)
    )


def calculate_solar_time_minutes(
    longitude_deg: float,
    timestamp: datetime,
    equation_of_time_minutes: float,
) -> float:
    """Convert timezone-aware civil time to true solar time in minutes."""
    utc_offset = timestamp.utcoffset()
    if utc_offset is None:
        raise ValueError("timestamp must be timezone-aware")

    civil_minutes = (
        timestamp.hour
        * 60.0
        + timestamp.minute
        + timestamp.second / 60.0
        + timestamp.microsecond / 60_000_000.0
    )
    utc_offset_hours = utc_offset.total_seconds() / 3600.0
    time_correction = (
        equation_of_time_minutes
        + 4.0 * longitude_deg
        - 60.0 * utc_offset_hours
    )
    return (civil_minutes + time_correction) % 1440.0


def calculate_solar_hour_angle(solar_time_minutes: float) -> float:
    """Return solar hour angle in radians, negative before solar noon."""
    return math.radians(solar_time_minutes / 4.0 - 180.0)


def calculate_sun_vector_enu(
    latitude_deg: float,
    declination_rad: float,
    hour_angle_rad: float,
) -> np.ndarray:
    """Return a unit vector from the observer to the Sun in ENU coordinates."""
    latitude = math.radians(latitude_deg)
    declination = declination_rad
    hour_angle = hour_angle_rad

    east = -math.cos(declination) * math.sin(hour_angle)
    north = (
        math.cos(latitude) * math.sin(declination)
        - math.sin(latitude)
        * math.cos(declination)
        * math.cos(hour_angle)
    )
    up = (
        math.sin(latitude) * math.sin(declination)
        + math.cos(latitude)
        * math.cos(declination)
        * math.cos(hour_angle)
    )

    vector = np.array([east, north, up], dtype=float)
    return vector / np.linalg.norm(vector)


def get_sun_vector(
    latitude_deg: float,
    longitude_deg: float,
    timestamp: datetime,
) -> np.ndarray:
    """Return the observer-to-Sun unit vector in East-North-Up coordinates."""
    if not -90.0 <= latitude_deg <= 90.0:
        raise ValueError("latitude must be between -90 and 90 degrees")
    if not -180.0 <= longitude_deg <= 180.0:
        raise ValueError("longitude must be between -180 and 180 degrees")
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")

    fractional_year = calculate_fractional_year(timestamp)
    equation_of_time = calculate_equation_of_time(fractional_year)
    declination = calculate_solar_declination(fractional_year)
    solar_time = calculate_solar_time_minutes(
        longitude_deg,
        timestamp,
        equation_of_time,
    )
    hour_angle = calculate_solar_hour_angle(solar_time)
    return calculate_sun_vector_enu(latitude_deg, declination, hour_angle)


def sun_azimuth_elevation(sun_vector_enu: np.ndarray) -> tuple[float, float]:
    """Return azimuth clockwise from true north and elevation, in degrees."""
    east, north, up = sun_vector_enu
    azimuth = math.degrees(math.atan2(east, north)) % 360.0
    elevation = math.degrees(math.asin(float(np.clip(up, -1.0, 1.0))))
    return azimuth, elevation


def enu_to_boat_frame(
    vector_enu: np.ndarray,
    boat_heading_deg: float,
) -> np.ndarray:
    """Convert ENU to boat coordinates: +x starboard, +y forward, +z up."""
    heading = math.radians(boat_heading_deg)
    east, north, up = vector_enu
    starboard = east * math.cos(heading) - north * math.sin(heading)
    forward = east * math.sin(heading) + north * math.cos(heading)
    return np.array([starboard, forward, up], dtype=float)


def build_sail_polygon(
    mast_x: float,
    mast_y: float,
    boom_heading_deg: float,
) -> np.ndarray:
    """Create the simplified five-point sail used by this prototype."""
    boom_heading = math.radians(boom_heading_deg)

    def offset(distance: float) -> tuple[float, float]:
        return (
            distance * math.cos(boom_heading),
            distance * math.sin(boom_heading),
        )

    boom_dx, boom_dy = offset(BOOM_LENGTH)
    top_dx, top_dy = offset(1.0)
    leach_dx, leach_dy = offset(1.5)

    return np.array(
        [
            (mast_x, mast_y, MAST_HEIGHT),
            (mast_x + top_dx, mast_y + top_dy, 2.8),
            (mast_x + leach_dx, mast_y + leach_dy, 2.1),
            (mast_x + boom_dx, mast_y + boom_dy, BOOM_HEIGHT),
            (mast_x, mast_y, BOOM_HEIGHT),
        ],
        dtype=float,
    )


def project_to_horizontal_plane(
    polygon: np.ndarray,
    light_direction: np.ndarray,
    plane_z: float = 0.0,
) -> np.ndarray:
    """Project a 3D polygon along incoming sunlight onto a horizontal plane."""
    if light_direction[2] >= 0.0:
        raise ValueError("light direction must point downwards")

    projected = []
    for point in polygon:
        distance = (plane_z - point[2]) / light_direction[2]
        shadow_point = point + distance * light_direction
        shadow_point[2] = plane_z
        projected.append(shadow_point)
    return np.asarray(projected)


def polygon_area_xy(polygon: np.ndarray) -> float:
    """Return the area of a polygon from its x/y coordinates."""
    x = polygon[:, 0]
    y = polygon[:, 1]
    return 0.5 * abs(float(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1))))


def panel_sample_points(panel: np.ndarray) -> np.ndarray:
    """Return evenly spaced sample points inside an axis-aligned panel."""
    x_min, y_min = panel.min(axis=0)
    x_max, y_max = panel.max(axis=0)
    count = SHADOW_SAMPLE_RESOLUTION

    x_step = (x_max - x_min) / count
    y_step = (y_max - y_min) / count
    x_values = np.linspace(x_min + x_step / 2.0, x_max - x_step / 2.0, count)
    y_values = np.linspace(y_min + y_step / 2.0, y_max - y_step / 2.0, count)
    x_grid, y_grid = np.meshgrid(x_values, y_values)
    return np.column_stack((x_grid.ravel(), y_grid.ravel()))


def calculate_shadowed_panel_area(
    panels: list[np.ndarray],
    shadow_polygons: list[np.ndarray],
) -> tuple[float, float]:
    """Estimate total and shadowed panel area without double-counting shadows."""
    shadow_paths = [Path(shadow[:, :2]) for shadow in shadow_polygons]
    total_area = 0.0
    shadowed_area = 0.0

    for panel in panels:
        panel_area = polygon_area_xy(panel)
        samples = panel_sample_points(panel)
        blocked = np.zeros(len(samples), dtype=bool)

        for shadow_path in shadow_paths:
            blocked |= shadow_path.contains_points(samples)

        total_area += panel_area
        shadowed_area += panel_area * float(np.mean(blocked))

    return total_area, shadowed_area


def decimal_hour_to_datetime(
    selected_date: date,
    decimal_hour: float,
    utc_offset_hours: float,
) -> datetime:
    """Build a fixed-offset, timezone-aware datetime from plot controls."""
    total_minutes = int(round(decimal_hour * 60.0)) % (24 * 60)
    hour, minute = divmod(total_minutes, 60)
    tz = timezone(timedelta(hours=utc_offset_hours))
    return datetime(
        selected_date.year,
        selected_date.month,
        selected_date.day,
        hour,
        minute,
        tzinfo=tz,
    )


def set_equal_aspect(ax) -> None:
    """Give all three plot dimensions an equal visual scale."""
    limits = np.array([ax.get_xlim3d(), ax.get_ylim3d(), ax.get_zlim3d()])
    centres = np.mean(limits, axis=1)
    half_range = np.max(np.ptp(limits, axis=1)) / 2.0
    for centre, setter in zip(
        centres,
        (ax.set_xlim3d, ax.set_ylim3d, ax.set_zlim3d),
    ):
        setter(centre - half_range, centre + half_range)


def run_prototype() -> None:
    """Open the interactive Matplotlib prototype."""
    figure = plt.figure(figsize=(11, 8))
    ax = figure.add_subplot(111, projection="3d")
    figure.subplots_adjust(left=0.18, right=0.96, top=0.93, bottom=0.46)

    slider_colour = "lightgoldenrodyellow"
    slider_specs = [
        ("Boat heading (deg)", 0.0, 360.0, 30.0, 0.38),
        ("Boom heading (deg)", 0.0, 360.0, 60.0, 0.335),
        ("Latitude (deg)", -90.0, 90.0, 1.29, 0.29),
        ("Longitude (deg)", -180.0, 180.0, 103.85, 0.245),
        ("Local time (hour)", 0.0, 23.75, 12.0, 0.20),
        ("UTC offset (hour)", -12.0, 14.0, 8.0, 0.155),
    ]

    sliders = []
    for label, minimum, maximum, initial, bottom in slider_specs:
        slider_axis = figure.add_axes(
            [0.25, bottom, 0.64, 0.025],
            facecolor=slider_colour,
        )
        step = 0.25 if label in {"Local time (hour)", "UTC offset (hour)"} else None
        slider = Slider(
            slider_axis,
            label,
            minimum,
            maximum,
            valinit=initial,
            valstep=step,
        )
        sliders.append(slider)

    (
        boat_heading_slider,
        boom_heading_slider,
        latitude_slider,
        longitude_slider,
        local_time_slider,
        utc_offset_slider,
    ) = sliders

    date_axis = figure.add_axes([0.25, 0.095, 0.20, 0.035])
    date_box = TextBox(date_axis, "Local date (YYYY-MM-DD)", initial="2026-08-14")

    panel_arrays = [np.asarray(panel, dtype=float) for panel in SOLAR_PANELS]

    def update(_value=None) -> None:
        ax.clear()

        try:
            selected_date = date.fromisoformat(date_box.text.strip())
            timestamp = decimal_hour_to_datetime(
                selected_date,
                local_time_slider.val,
                utc_offset_slider.val,
            )
            sun_enu = get_sun_vector(
                latitude_slider.val,
                longitude_slider.val,
                timestamp,
            )
        except ValueError as error:
            ax.set_title(f"Invalid input: {error}")
            figure.canvas.draw_idle()
            return

        azimuth, elevation = sun_azimuth_elevation(sun_enu)
        sun_boat = enu_to_boat_frame(sun_enu, boat_heading_slider.val)
        sunlight_direction = -sun_boat
        shadow_polygons = []

        for mast_x, mast_y in MAST_POSITIONS:
            sail = build_sail_polygon(
                mast_x,
                mast_y,
                boom_heading_slider.val,
            )

            ax.plot(
                [mast_x, mast_x],
                [mast_y, mast_y],
                [0.0, MAST_HEIGHT],
                color="tab:blue",
            )
            ax.plot(
                [sail[-1, 0], sail[-2, 0]],
                [sail[-1, 1], sail[-2, 1]],
                [BOOM_HEIGHT, BOOM_HEIGHT],
                color="tab:red",
                linewidth=2,
            )
            ax.add_collection3d(
                Poly3DCollection(
                    [sail],
                    facecolors="white",
                    edgecolors="black",
                    alpha=0.45,
                )
            )

            if sun_boat[2] > 0.0:
                shadow = project_to_horizontal_plane(sail, sunlight_direction)
                shadow_polygons.append(shadow)
                ax.add_collection3d(
                    Poly3DCollection(
                        [shadow],
                        facecolors="grey",
                        edgecolors="dimgray",
                        alpha=0.35,
                    )
                )

        for panel in panel_arrays:
            panel_3d = np.column_stack((panel, np.zeros(len(panel))))
            ax.add_collection3d(
                Poly3DCollection(
                    [panel_3d],
                    facecolors="tab:green",
                    edgecolors="darkgreen",
                    alpha=0.55,
                )
            )

        total_area, shadowed_area = calculate_shadowed_panel_area(
            panel_arrays,
            shadow_polygons,
        )
        if sun_boat[2] > 0.0 and total_area > 0.0:
            sunlit_percentage = 100.0 * (1.0 - shadowed_area / total_area)
            status = f"Sunlit panel area: {sunlit_percentage:.1f}%"
        else:
            sunlit_percentage = 0.0
            status = "Sun below horizon: direct sunlit area 0.0%"

        if sun_boat[2] > 0.0:
            arrow_length = 1.5
            arrow_end = np.array(
                [MAST_POSITIONS[0][0], MAST_POSITIONS[0][1], MAST_HEIGHT]
            )
            arrow_start = arrow_end + sun_boat * arrow_length
            ax.quiver(
                *arrow_start,
                *sunlight_direction,
                length=arrow_length,
                normalize=True,
                color="orange",
                linewidth=2,
            )

        ax.set_title(
            f"{status}\n"
            f"{timestamp.isoformat(timespec='minutes')} | "
            f"Sun azimuth {azimuth:.1f} deg, elevation {elevation:.1f} deg"
        )
        ax.set_xlabel("X: starboard (m)")
        ax.set_ylabel("Y: forward (m)")
        ax.set_zlabel("Z: up (m)")
        ax.set_xlim(-3.0, 3.0)
        ax.set_ylim(-3.0, 5.0)
        ax.set_zlim(0.0, 4.0)
        set_equal_aspect(ax)
        ax.view_init(elev=20.0, azim=135.0)
        figure.canvas.draw_idle()

    for slider in sliders:
        slider.on_changed(update)
    date_box.on_submit(update)

    update()
    plt.show()


if __name__ == "__main__":
    run_prototype()
