from datetime import datetime
import math

# def calculate_fractional_year(timestamp: datetime) -> float:
#     """Return the fractional year in radians.

#     Args:
#         timestamp (datetime): _description_

#     Returns:
#         float: _description_
#     """

#     day_of_year = timestamp.timetuple().tm_yday

#     decimal_hour = (
#         timestamp.hour
#         + timestamp.minute / 60
#         + timestamp.second / 3600
#         + timestamp.microsecond / 3_600_000_000
#     )

#     is_leap_year = (
#         timestamp.year % 4 == 0
#         and (
#             timestamp.year % 100 != 0
#             or timestamp.year % 400 == 0
#         )
#     )

#     days_in_year = 366 if is_leap_year else 365

#     return (
#         2
#         * math.pi
#         / days_in_year
#         * (day_of_year - 1 + (decimal_hour - 12) / 24)
#     )

# def calculate_equation_of_time(fractional_year: float) -> float:
#     """Return an estimation of the equiation of time correction in minutes

#     Args:
#         fractional_year (float): _description_

#     Returns:
#         float: _description_
#     """
#     return 229.18 * (
#         0.000075
#         + 0.001868 * math.cos(fractional_year)
#         - 0.032077 * math.sin(fractional_year)
#         - 0.014615 * math.cos(2 * fractional_year)
#         - 0.040849 * math.sin(2 * fractional_year)
#     )


# def calculate_solar_declination(fractional_year: float) -> float:
#     """Return the solar declination in radians.

#     Args:
#         fractional_year (float): _description_

#     Returns:
#         float: _description_
#     """
#     return (
#         0.006918
#         - 0.399912 * math.cos(fractional_year)
#         + 0.070257 * math.sin(fractional_year)
#         - 0.006758 * math.cos(2 * fractional_year)
#         + 0.000907 * math.sin(2 * fractional_year)
#         - 0.002697 * math.cos(3 * fractional_year)
#         + 0.001480 * math.sin(3 * fractional_year)
#     )




# def calculate_solar_hour_angle(solar_time_minutes: float) -> float:
#     """_Return the solar hour angle in radians._

#     Negative = before solar noon

#     Zero     = solar noon

#     Positive = after solar noon

#     Args:
#         solar_time_minutes (float): _description_

#     Returns:
#         float: _description_
#     """

#     hour_angle_degrees = solar_time_minutes / 4 - 180

#     return math.radians(hour_angle_degrees)



# def calculate_sun_vector_enu(
#     latitude_deg: float,
#     declination_rad: float,
#     hour_angle_rad: float,
# ) -> tuple[float, float, float]:
#     """
#     _Return the unit vector **pointing from the observer to the Sun**._
    
#     Uses the ENU (East-North-Up) coordinate system.

#     Vector order:
#         east, true north, up



#     Args:
#         latitude_deg (float): _description_
#         declination_rad (float): _description_
#         hour_angle_rad (float): _description_

#     Returns:
#         tuple[float, float, float]: _description_
#     """

#     latitude = math.radians(latitude_deg)
#     declination = declination_rad
#     hour_angle = hour_angle_rad

#     east = (
#         -math.cos(declination)
#         * math.sin(hour_angle)
#     )

#     north = (
#         math.cos(latitude) * math.sin(declination)
#         - math.sin(latitude)
#         * math.cos(declination)
#         * math.cos(hour_angle)
#     )

#     up = (
#         math.sin(latitude) * math.sin(declination)
#         + math.cos(latitude)
#         * math.cos(declination)
#         * math.cos(hour_angle)
#     )

#     length = math.sqrt(
#         east**2 + north**2 + up**2
#     )

#     return (
#         east / length,
#         north / length,
#         up / length,
#     )



# def get_sun_vector(lattitude:float, longitude:float, timestamp:datetime) -> tuple[float, float, float]:
#     """_Calculate the Sun unit vector in East-North-Up coordinates._

#     Args:
#         lattitude (float): Lattitude in degrees
#         longitude (float): Longitude in degrees
#         timestamp (datetime): _description_

#     Raises:
#         ValueError: _description_
#         ValueError: _description_
#         ValueError: _description_

#     Returns:
#         tuple[float, float, float]: _description_
#     """
#     if not -90 <= lattitude <= 90:
#         raise ValueError("latitude must be between -90 and 90 degrees")
#     if not -180 <= longitude <= 180:
#         raise ValueError("longitude must be between -180 and 180 degrees")
#     if timestamp.tzinfo is None or timestamp.utcoffset() is None:
#         raise ValueError("timestamp must be timezone-aware")

#     fractional_year = calculate_fractional_year(timestamp)
    

#     return calculate_sun_vector_enu(
#         lattitude,

#     )