"""Interactive sail-shadow model reconstructed from the supplied PDF code."""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from shapely.geometry import Polygon
from shapely.ops import unary_union


MAST_HEIGHT = 2.26 - 0.21
BOOM_HEIGHT = 0.25
BOOM_LENGTH = 2.00
MAST_POSITIONS = [(0, 0), (0, 2.05)]

SOLAR_PANELS = [
    [(0.25, -0.45), (2, -0.45), (2, 0.68), (0.25, 0.68)],
    [(0.25, 1.37), (2, 1.37), (2, 2.5), (0.25, 2.5)],
]

INITIAL_HEADING_BOAT = 30
INITIAL_HEADING_BOOM = 60
INITIAL_SUN_AZIMUTH = 120
INITIAL_SUN_ELEVATION = 45


def set_equal_aspect(ax) -> None:
    """Set the same visual scale on all three axes."""
    limits = np.array([ax.get_xlim3d(), ax.get_ylim3d(), ax.get_zlim3d()])
    centers = np.mean(limits, axis=1)
    max_range = np.max(np.ptp(limits, axis=1)) / 2

    setters = [ax.set_xlim3d, ax.set_ylim3d, ax.set_zlim3d]
    for center, setter in zip(centers, setters):
        setter(center - max_range, center + max_range)


def main() -> None:
    """Open the interactive Matplotlib model."""
    figure = plt.figure(figsize=(10, 7))
    ax = figure.add_subplot(111, projection="3d")
    plt.subplots_adjust(left=0.25, bottom=0.35)

    slider_color = "lightgoldenrodyellow"
    ax_heading_boat = plt.axes(
        [0.25, 0.25, 0.65, 0.03],
        facecolor=slider_color,
    )
    ax_heading_boom = plt.axes(
        [0.25, 0.20, 0.65, 0.03],
        facecolor=slider_color,
    )
    ax_sun_azimuth = plt.axes(
        [0.25, 0.15, 0.65, 0.03],
        facecolor=slider_color,
    )
    ax_sun_elevation = plt.axes(
        [0.25, 0.10, 0.65, 0.03],
        facecolor=slider_color,
    )

    heading_boat_slider = Slider(
        ax_heading_boat,
        "Boat Heading (deg)",
        0,
        360,
        valinit=INITIAL_HEADING_BOAT,
    )
    heading_boom_slider = Slider(
        ax_heading_boom,
        "Boom Heading (deg)",
        0,
        360,
        valinit=INITIAL_HEADING_BOOM,
    )
    sun_azimuth_slider = Slider(
        ax_sun_azimuth,
        "Sun Azimuth (deg)",
        0,
        360,
        valinit=INITIAL_SUN_AZIMUTH,
    )
    sun_elevation_slider = Slider(
        ax_sun_elevation,
        "Sun Elevation (deg)",
        0,
        90,
        valinit=INITIAL_SUN_ELEVATION,
    )

    def update(_value=None) -> None:
        ax.clear()

        heading_boat = np.radians(heading_boat_slider.val)
        heading_boom = np.radians(heading_boom_slider.val)
        sun_azimuth = np.radians(sun_azimuth_slider.val)
        sun_elevation = np.radians(sun_elevation_slider.val)

        sun_dx = np.cos(sun_elevation) * np.sin(sun_azimuth)
        sun_dy = np.cos(sun_elevation) * np.cos(sun_azimuth)
        sun_dz = np.sin(sun_elevation)

        # This vector follows the direction in which sunlight travels.
        sun_vector = np.array([sun_dx, sun_dy, -sun_dz])

        rotation_matrix = np.array(
            [
                [
                    np.cos(-heading_boat),
                    -np.sin(-heading_boat),
                    0,
                ],
                [
                    np.sin(-heading_boat),
                    np.cos(-heading_boat),
                    0,
                ],
                [0, 0, 1],
            ]
        )

        sun_boat_frame = rotation_matrix @ sun_vector
        total_panel_area = 0.0
        shadowed_area = 0.0
        all_shadow_polygons = []

        for mast_x, mast_y in MAST_POSITIONS:
            top_mast = (mast_x, mast_y, MAST_HEIGHT)
            boom_attach = (mast_x, mast_y, BOOM_HEIGHT)

            boom_dx = BOOM_LENGTH * np.cos(heading_boom)
            boom_dy = BOOM_LENGTH * np.sin(heading_boom)
            boom_tip = (
                mast_x + boom_dx,
                mast_y + boom_dy,
                BOOM_HEIGHT,
            )

            top_sail_distance = 1.0
            top_sail_height = 2.8
            top_sail_dx = top_sail_distance * np.cos(heading_boom)
            top_sail_dy = top_sail_distance * np.sin(heading_boom)
            top_sail = (
                mast_x + top_sail_dx,
                mast_y + top_sail_dy,
                top_sail_height,
            )

            leach_sail_distance = 1.5
            leach_sail_height = 2.1
            leach_sail_dx = leach_sail_distance * np.cos(heading_boom)
            leach_sail_dy = leach_sail_distance * np.sin(heading_boom)
            leach_sail = (
                mast_x + leach_sail_dx,
                mast_y + leach_sail_dy,
                leach_sail_height,
            )

            ax.plot(
                [mast_x, mast_x],
                [mast_y, mast_y],
                [0, MAST_HEIGHT],
                color="blue",
            )
            ax.plot(
                [mast_x, mast_x + boom_dx],
                [mast_y, mast_y + boom_dy],
                [BOOM_HEIGHT, BOOM_HEIGHT],
                color="red",
                linewidth=2,
            )

            sail_polygon = [
                top_mast,
                top_sail,
                leach_sail,
                boom_tip,
                boom_attach,
            ]
            ax.add_collection3d(
                Poly3DCollection(
                    [sail_polygon],
                    facecolors="white",
                    edgecolors="black",
                    alpha=0.4,
                )
            )

            shadow_polygon_3d = []
            for point in sail_polygon:
                if sun_boat_frame[2] != 0:
                    scale = point[2] / abs(sun_boat_frame[2])
                else:
                    scale = 0

                projected_point = np.array(point) + sun_boat_frame * scale
                projected_point[2] = 0
                shadow_polygon_3d.append(projected_point)

            ax.add_collection3d(
                Poly3DCollection(
                    [shadow_polygon_3d],
                    facecolors="gray",
                    alpha=0.3,
                )
            )

            shadow_polygon_2d = Polygon(
                [(point[0], point[1]) for point in shadow_polygon_3d]
            )
            all_shadow_polygons.append(shadow_polygon_2d)

        if all_shadow_polygons:
            combined_shadow = unary_union(all_shadow_polygons)
        else:
            combined_shadow = None

        for corners in SOLAR_PANELS:
            panel_3d = [(x, y, 0) for x, y in corners]
            ax.add_collection3d(
                Poly3DCollection(
                    [panel_3d],
                    facecolors="green",
                    alpha=0.5,
                )
            )

            panel_polygon = Polygon([(x, y) for x, y, _z in panel_3d])
            total_panel_area += panel_polygon.area

            if combined_shadow is not None:
                intersection = panel_polygon.intersection(combined_shadow)
                shadowed_area += intersection.area

        if total_panel_area > 0:
            unshadowed_percentage = (
                1 - shadowed_area / total_panel_area
            ) * 100
        else:
            unshadowed_percentage = 100

        ax.set_title(
            f"Solar Unshadowed Area: {unshadowed_percentage:.1f}%"
        )

        mast_x, mast_y = MAST_POSITIONS[0]
        ax.quiver(
            mast_x,
            mast_y,
            MAST_HEIGHT,
            -sun_boat_frame[0],
            -sun_boat_frame[1],
            -sun_boat_frame[2],
            length=1.5,
            color="orange",
        )

        ax.set_xlabel("X (Boat Frame)")
        ax.set_ylabel("Y (Boat Frame)")
        ax.set_zlabel("Z (Height)")
        ax.set_xlim([-3, 3])
        ax.set_ylim([-3, 3])
        ax.set_zlim([0, 3])
        set_equal_aspect(ax)
        ax.view_init(elev=20, azim=135)
        figure.canvas.draw_idle()

    update()

    heading_boat_slider.on_changed(update)
    heading_boom_slider.on_changed(update)
    sun_azimuth_slider.on_changed(update)
    sun_elevation_slider.on_changed(update)

    plt.show()


if __name__ == "__main__":
    main()
