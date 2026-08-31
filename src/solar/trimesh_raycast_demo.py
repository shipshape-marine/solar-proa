import numpy as np
import trimesh


# ---------------------------------------------------------
# 1. Create a dummy solar panel
# ---------------------------------------------------------

# 2 m × 2 m horizontal panel centered at the origin.
panel = trimesh.creation.box(extents=[2.0, 2.0, 0.02])

# Put its upper surface approximately at z = 0.
panel.apply_translation([0.0, 0.0, -0.01])


# ---------------------------------------------------------
# 2. Create a dummy shadow caster
# ---------------------------------------------------------

# A thin vertical wall:
#
#       z
#       ↑
#       │   █ wall
#       │   █
#       │   █
#       └────────→ x
#          panel
#
caster = trimesh.creation.box(
    extents=[0.1, 1.0, 1.0]
)

# Wall sits above the panel.
caster.apply_translation([0.3, 0.0, 0.5])


# ---------------------------------------------------------
# 3. Generate sample points on the panel
# ---------------------------------------------------------

grid_size = 20

x = np.linspace(-0.95, 0.95, grid_size)
y = np.linspace(-0.95, 0.95, grid_size)

xx, yy = np.meshgrid(x, y)

ray_origins = np.column_stack([
    xx.ravel(),
    yy.ravel(),
    np.full(xx.size, 0.001),   # slightly above panel
])

print(ray_origins.shape)
# (400, 3)


# ---------------------------------------------------------
# 4. Define direction toward the Sun
# ---------------------------------------------------------

sun_direction = np.array([1.0, 0.0, 1.0])
sun_direction /= np.linalg.norm(sun_direction)

# Every sample point shoots a ray in the same direction.
ray_directions = np.tile(
    sun_direction,
    (len(ray_origins), 1)
)

print(ray_directions.shape)
# (400, 3)


# ---------------------------------------------------------
# 5. Raycast against ONLY the shadow caster
# ---------------------------------------------------------

intersector = trimesh.ray.ray_triangle.RayMeshIntersector(
    caster
)

blocked = intersector.intersects_any(
    ray_origins=ray_origins,
    ray_directions=ray_directions,
)

print(blocked.shape)
# (400,)

print(blocked[:10])
# [False False True ...]


# ---------------------------------------------------------
# 6. Calculate shaded fraction
# ---------------------------------------------------------

shaded_samples = np.count_nonzero(blocked)
total_samples = len(blocked)

shaded_fraction = shaded_samples / total_samples

print("Shaded samples:", shaded_samples)
print("Total samples:", total_samples)
print("Shaded fraction:", shaded_fraction)
print("Shaded percentage:", shaded_fraction * 100)


import matplotlib.pyplot as plt


# ---------------------------------------------------------
# 7. Plot the shadow result from above
# ---------------------------------------------------------

fig, ax = plt.subplots(figsize=(8, 8))

# Panel boundary: x/y = [-1, 1]
panel_outline = plt.Rectangle(
    (-1.0, -1.0),
    2.0,
    2.0,
    fill=False,
    linewidth=2,
    label="Solar panel",
)
ax.add_patch(panel_outline)


# Plot unblocked sample points
ax.scatter(
    ray_origins[~blocked, 0],
    ray_origins[~blocked, 1],
    s=20,
    c="green",
    label="Unblocked",
)

# Plot blocked sample points
ax.scatter(
    ray_origins[blocked, 0],
    ray_origins[blocked, 1],
    s=20,
    c="red",
    label="Blocked",
)


# Show the caster's footprint in the top-down view.
#
# caster is centered at x=0.3
# dimensions are:
#     x = 0.1
#     y = 1.0
caster_outline = plt.Rectangle(
    (0.25, -0.5),
    0.1,
    1.0,
    fill=False,
    linewidth=3,
    label="Caster",
)
ax.add_patch(caster_outline)


# Draw the horizontal component of the Sun direction.
ax.arrow(
    0.0,
    -0.8,
    sun_direction[0] * 0.5,
    sun_direction[1] * 0.5,
    width=0.01,
    head_width=0.08,
    length_includes_head=True,
)

ax.text(
    0.05,
    -0.75,
    "Toward Sun",
)


ax.set_title(
    f"Dummy Panel Raycasting\n"
    f"Shaded = {shaded_fraction * 100:.1f}%"
)

ax.set_xlabel("X (m)")
ax.set_ylabel("Y (m)")

ax.set_aspect("equal")
ax.set_xlim(-1.1, 1.1)
ax.set_ylim(-1.1, 1.1)

ax.grid(True, alpha=0.3)
ax.legend()

plt.show()