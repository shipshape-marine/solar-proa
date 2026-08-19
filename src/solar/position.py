# Functions to calculate the solar position
# Credit: General Solar Position Calculations -- NOAA Global Monitoring Division


from datetime import datetime
import math

def _calculate_fractional_year(timestamp:datetime) -> float:
    """Return the fractional year in radians.

        Args:
            timestamp (datetime): _Target time and date_

        Returns:
            float: _Timestamp expressed as a fraction of the year_
    """

    day_of_year = timestamp.timetuple().tm_yday

    decimal_hour = (
        timestamp.hour
        + timestamp.minute / 60
        + timestamp.second / 3600
        + timestamp.microsecond / 3_600_000_000
    )

    is_leap_year = (
        timestamp.year % 4 == 0
        and (
            timestamp.year % 100 != 0
            or timestamp.year % 400 == 0
        )
    )

    days_in_year = 366 if is_leap_year else 365

    return (
        2
        * math.pi
        / days_in_year
        * (day_of_year - 1 + (decimal_hour - 12) / 24)
    )


def _calculate_equation_of_time(fractional_year: float) -> float:
    """Return an estimation of the equiation of time correction in minutes

    Args:
        fractional_year (float): _description_

    Returns:
        float: _description_
    """
    return 229.18 * (
        0.000075
        + 0.001868 * math.cos(fractional_year)
        - 0.032077 * math.sin(fractional_year)
        - 0.014615 * math.cos(2 * fractional_year)
        - 0.040849 * math.sin(2 * fractional_year)
    )

def _calculate_solar_declination(fractional_year: float) -> float:
    """Return the solar declination angle in radians.\
    
    Uses the Spencer (1971) Fourier-series declination equation.

    Args:
        fractional_year (float): _description_

    Returns:
        float: _Solar declination angle (radians)_
    """
    return (
        0.006918
        - 0.399912 * math.cos(fractional_year)
        + 0.070257 * math.sin(fractional_year)
        - 0.006758 * math.cos(2 * fractional_year)
        + 0.000907 * math.sin(2 * fractional_year)
        - 0.002697 * math.cos(3 * fractional_year)
        + 0.001480 * math.sin(3 * fractional_year)
    )



def _calculate_solar_time_minutes(timestamp:datetime, longitude:float, eqtime:float) -> float:
    """_Return the true solar time in minutes (from midnight)_

    Args:
        timestamp (datetime): _Target timestamp_
        longitude (float): _Target longitude_
        eqtime (float): _Equation of time in minutes_

    Returns:
        float: _True solar time in minutes_
    """
    utc_offset = timestamp.utcoffset()
    if utc_offset is None:
        raise ValueError("timestamp must be timezone-aware")
    timezone = utc_offset.total_seconds() / 3600
    time_offset = eqtime + 4 * longitude - 60 * timezone
    return (
        timestamp.hour * 60
        + timestamp.minute 
        + timestamp.second / 60 
        + time_offset
    )


def _calculate_solar_hour_angle(solar_time: float) -> float:
    """_Returns the solar hour angle in degrees_

    Args:
        solar_time (float): _Solar time in minutes_

    Returns:
        float: _Solar hour angle in degrees_
    """

    return solar_time / 4 - 180


def _calculate_solar_zenith(hour_angle: float, latitude: float, solar_declination: float) -> float:
    """Returns the solar zenith angle in degrees.\

    Solar zenith angle is the angle between the sun's rays and the normal to the horizon at the target point.

    Args:
        hour_angle (float): _description_
        latitude (float): _description_
        solar_declination (float): _description_

    Returns:
        float: _description_
    """
    zenith_radians = math.acos(
        math.sin(latitude) * math.sin(solar_declination)
        + math.cos(latitude) * math.cos(solar_declination) * math.cos(hour_angle)
    )

    return math.degrees(zenith_radians)


def _calculate_solar_azimuth(hour_angle: float, latitude: float, solar_declination: float) -> float:
    """Return the solar azimuth angle in degrees clockwise from true north.

    Credit: United States Naval Observatory

    Args:
        hour_angle (float): _Solar hour angle (radians)_
        latitude (float): _Target latitude (radians)_
        solar_declination (float): _Solar declination angle (radians)_

    Returns:
        float: _Solar azimuth angle (degrees clockwise from true north)_
    """
    east_component = -math.cos(solar_declination) * math.sin(hour_angle)
    north_component = (
        math.cos(latitude) * math.sin(solar_declination)
        - math.sin(latitude)
        * math.cos(solar_declination)
        * math.cos(hour_angle)
    )

    horizontal_magnitude = math.hypot(east_component, north_component)

    # At the exact zenith, both horizontal components are zero, so azimuth is
    # undefined. Return north (0 degrees) as a stable convention.
    if horizontal_magnitude < 1e-12:
        return 0.0

    return math.degrees(math.atan2(east_component, north_component)) % 360


def _calculate_sun_vector_enu(
    latitude_deg: float,
    longitude_deg: float,
    timestamp: datetime,
) -> tuple[float, float, float]:
    """Return the Sun unit vector in East-North-Up coordinates.

    The vector points from the observer towards the Sun.

    Args:
        latitude_deg (float): _Target latitude (degrees)_
        longitude_deg (float): _Target longitude (degrees east)_
        timestamp (datetime): _Timezone-aware target date and time_

    Returns:
        tuple[float, float, float]: _East, north, and up vector components_
    """
    fractional_year = _calculate_fractional_year(timestamp)
    equation_of_time = _calculate_equation_of_time(fractional_year)
    solar_declination = _calculate_solar_declination(fractional_year)

    solar_time = _calculate_solar_time_minutes(
        timestamp,
        longitude_deg,
        equation_of_time,
    )

    hour_angle_deg = _calculate_solar_hour_angle(solar_time)

    latitude = math.radians(latitude_deg)
    hour_angle = math.radians(hour_angle_deg)

    zenith_deg = _calculate_solar_zenith(
        hour_angle,
        latitude,
        solar_declination,
    )

    azimuth_deg = _calculate_solar_azimuth(
        hour_angle,
        latitude,
        solar_declination,
    )

    zenith = math.radians(zenith_deg)
    azimuth = math.radians(azimuth_deg)

    east_component = math.sin(zenith) * math.sin(azimuth)
    north_component = math.sin(zenith) * math.cos(azimuth)
    up_component = math.cos(zenith)

    return east_component, north_component, up_component


def get_sun_vector(
    latitude_deg: float,
    longitude_deg: float,
    timestamp: datetime,
) -> tuple[float, float, float]:
    """Return the Sun unit vector in East-North-Up coordinates.

    The vector points from the observer towards the Sun.

    Args:
        latitude_deg (float): _Target latitude between -90 and 90 degrees_
        longitude_deg (float): _Target longitude between -180 and 180 degrees_
        timestamp (datetime): _Timezone-aware target date and time_

    Raises:
        ValueError: _If latitude is outside its valid range_
        ValueError: _If longitude is outside its valid range_
        ValueError: _If the timestamp is not timezone-aware_

    Returns:
        tuple[float, float, float]: _East, north, and up vector components_
    """
    if not -90 <= latitude_deg <= 90:
        raise ValueError("latitude must be between -90 and 90 degrees")

    if not -180 <= longitude_deg <= 180:
        raise ValueError("longitude must be between -180 and 180 degrees")

    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")

    return _calculate_sun_vector_enu(
        latitude_deg,
        longitude_deg,
        timestamp,
    )

