# Plan: Solar-Shadow Digital Model


## Week 1

> This week, I investigated how to calculate the Sun's position from geographic and time inputs. I adapted Loick's visualization so users enter latitude, longitude, date, and time instead of manually choosing azimuth and elevation. I am now exploring how to replace the simplified hardcoded boat with geometry extracted from the actual CAD model. My proposed next stage is an interactive React digital model that calculates panel shadow coverage using the real sail and panel shapes.

## Work completed this week

- **Investigated solar-position calculations.**
  - Studied how latitude, longitude, date, local time, and UTC offset determine the Sun's position.
  - Calculated the Sun's azimuth, elevation, and three-dimensional direction.
  - Represented the direction using East-North-Up coordinates.
  - Added validation for invalid coordinates and timestamps without timezone information.

- **Adapted Loick's Matplotlib visualization.**
  - Loick's original version required users to enter azimuth and elevation directly.
  - Replaced those controls with latitude, longitude, local date, local time, and UTC offset.
  - Retained boat-heading and boom-heading controls.
  - Made the plot update when the user changes an input.
  - Displayed the calculated Sun angles and estimated illuminated panel percentage.

- **Connected geographic Sun direction to boat orientation.**
  - Geographic calculations describe direction using east, north, and up.
  - The boat model describes direction using starboard, forward, and up.
  - Used the boat heading to translate between these systems.
  - For example, an easterly Sun is to starboard when the boat points north, but directly ahead when the boat points east.
  - This conversion determines where the sail shadow falls relative to the boat.

- **Created an initial shadow-coverage estimate.**
  - Represented each sail as a simplified flat polygon.
  - Projected that polygon in the direction of incoming sunlight.
  - Placed a grid of sample points over each simplified panel.
  - Marked samples inside a projected shadow as blocked.
  - Combined the results without counting overlapping sail shadows twice.
  - Reported zero direct sunlight when the Sun is below the horizon.

- **Started exploring CAD extraction.**
  - Examined FCStd and STEP versions of the RP2 model.
  - Started identifying sails, panels, and masts using object labels.
  - Tested reading placements, bounding boxes, surface area, volume, vertices, faces, and solids.
  - Tested FreeCAD tessellation, which converts an exact CAD surface into triangles.
  - Added preliminary Windows FreeCAD command discovery to support local processing.

## Current limitations

- The prototype uses hardcoded dimensions.
- It contains two simplified panels, while the RP2 model contains eight.
- Each sail is represented by one flat five-point polygon.
- The real sails are curved.
- All panels are assumed to lie on one horizontal plane.
- Masts, booms, yards, and the hull are not included as shadow casters.
- Coverage uses a fixed `45 x 45` sample grid.
- Boat heel and pitch are not modelled.
- The Sun calculation still needs comparison against an independent reference.
- The shadow result is suitable for demonstrating the concept, but not yet for engineering conclusions.

## Current technical objective

Replace the hardcoded geometry with the real CAD geometry while preserving component meaning.

The target data flow is:

```text
FCStd or STEP
-> FreeCAD CAD extraction
-> vertices and triangle indices
-> GLB model plus metadata
-> React Three Fiber
-> Sun calculation
-> shadow coverage
```

## Proposed CAD-conversion process

- **Use FCStd as the primary source.**
  - FCStd retains FreeCAD object names, hierarchy, and placements.
  - Names such as `Sail`, `Panel`, and `Mast` make automatic classification easier.
  - STEP remains a fallback for models from other CAD programs.

- **Extract each component separately.**
  - Do not merge the entire boat into one anonymous mesh.
  - Preserve sails, panels, masts, hulls, and structural components as named objects.
  - Assign roles such as `shadow_caster`, `solar_panel`, and `display_only`.

- **Tessellate the CAD surfaces.**
  - FreeCAD converts each exact surface into vertex positions and indexed triangles.
  - Apply every component's global position and rotation.
  - Convert FreeCAD millimetres into metres.
  - Use higher detail for sails and panels than for display-only parts.

- **Export an intermediate geometry bundle.**
  - Store large vertex and triangle arrays in NPZ.
  - Store names, roles, units, colours, and exact panel areas in JSON.
  - Keep this intermediate format for Python validation and debugging.

- **Create the GLB outside FreeCAD.**
  - FreeCAD is responsible for understanding CAD geometry.
  - A normal Python library such as Trimesh can package the extracted meshes into GLB.
  - Preserve every component as a named GLB node.
  - React can recover the vertices and triangle indices from each loaded node.

- **Treat original CAD edges as optional metadata.**
  - Shadow blocking depends on complete surfaces, not only boundary lines.
  - Triangle faces provide the surfaces required for ray intersection.
  - Shadow boundaries change with the Sun direction and are therefore generated dynamically.
  - Keep exact panel outlines or CAD-edge polylines for display, measurement, and validation when useful.

## Proposed React digital model

- **Use React for the application interface.**
  - Manage location, time, orientation, results, and model-selection controls.
  - Present per-panel and total shadow coverage.

- **Use React Three Fiber for the 3D scene.**
  - Load the GLB boat.
  - Allow users to rotate, zoom, and inspect it.
  - Preserve named sails, panels, and other components.
  - Colour or highlight shaded panel regions.

- **Reuse the existing Sun calculation.**
  - Port the Python calculation into TypeScript or expose it through a Python API.
  - Use shared test cases to ensure both versions return the same Sun vector.
  - Retain latitude, longitude, date, time, UTC offset, and boat heading as inputs.

- **Start with one fixed RP2 configuration.**
  - Convert the close-haul FCStd model during the build process.
  - Validate the complete pipeline before supporting arbitrary uploads or every sailing configuration.

## Proposed shadow calculation

- Generate area-weighted sample points over the real panel surfaces.
- Convert the Sun vector into boat coordinates.
- Cast a ray from each panel point toward the Sun.
- Start the ray slightly above the panel to avoid detecting the panel itself.
- Mark the point as shaded when the ray intersects a sail or another enabled shadow caster.
- Calculate coverage per panel and across the complete array.
- Run intensive ray calculations in a Web Worker.
- Add a spatial acceleration structure if the full mesh is too slow.

The numerical flow is:

```text
Panel sample point
-> ray toward Sun
-> intersection with sail?
-> shaded or illuminated
-> area-weighted coverage
```

## Proposed shadow visualization

Use separate systems for engineering results and visual appearance.

- **Quantitative panel shadow**
  - Use the raycasting result as the authoritative coverage calculation.
  - Convert blocked panel samples into a dark or coloured overlay.
  - Derive a clean boundary from the blocked-sample mask if needed.

- **Visual scene shadow**
  - Use a Three.js directional light and shadow map.
  - Let sails, masts, and other components cast shadows.
  - Let panels, deck, hull, and water receive shadows.
  - Do not use shadow-map pixels to calculate the engineering percentage.

- **Water visualization**
  - Add a water plane at the model's waterline because surrounding water is not part of the CAD file.
  - Start with flat or lightly animated water.
  - Allow the boat to cast a continuous visual shadow across panels, deck, hull, and water.
  - Keep water shadows separate from the panel-coverage calculation.

## Validation plan

- Compare the Sun calculation with an independent solar-position reference.
- Test sunrise, midday, sunset, and below-horizon cases.
- Test different boat headings with the same geographic Sun position.
- Confirm that the extracted model contains two sails and eight panels.
- Compare GLB component positions against the FreeCAD model.
- Test simple shadows with manually predictable geometry.
- Increase tessellation and sample resolution until the coverage result stabilises.
- Compare the React result against the Matplotlib reference for identical inputs.
- Record performance for model loading and shadow updates.

## Initial success criteria

The first React version should:

- Display the real close-haul RP2 geometry.
- Preserve identifiable sails, panels, and masts.
- Allow adjustment of latitude, longitude, date, time, UTC offset, and boat heading.
- Display the calculated Sun direction.
- Show realistic visual shadows on the boat and water.
- Show a panel overlay derived from raycasting.
- Report shaded percentage for every panel and the complete array.
- Produce results consistent with the Python reference implementation.

## Digital model versus digital twin

The first React version is technically a digital model because it simulates the boat using user-provided conditions.

It becomes a fuller digital twin when connected to the physical boat through data such as:

- GPS latitude and longitude.
- Actual time.
- Compass heading.
- Heel and pitch.
- Sail angle.
- Solar irradiance.
- Panel voltage and current.
- Battery and motor measurements.

Live sensor integration should follow after the geometry and shadow calculations are validated.

## Questions for the supervisor

- Should the first deliverable focus on one fixed RP2 configuration or support arbitrary CAD uploads?
- Is panel shadow percentage sufficient, or should the project also estimate electrical power loss?
- Should the first calculation include only sails, or also masts, booms, and yards?
- What accuracy threshold is expected for shadow coverage?
- Should heel and pitch be included in the first version?
- Is visual water realism important, or is a simple receiving plane sufficient?
- Is live sensor integration expected within the project, or should the work remain a digital simulation?
- Should FCStd be the required source format, with STEP treated as an optional fallback?

## Recommended defaults

- Use the close-haul RP2 FCStd model first.
- Use FCStd labels to identify components.
- Use GLB plus a JSON manifest in React.
- Use real sail and panel triangles for raycasting.
- Include sails as shadow casters first.
- Add masts and spars after validation.
- Use a flat water plane for the first visual version.
- Calculate geometric shade coverage before modelling electrical power loss.
- Treat live sensor integration as future work.

## Meeting demonstration and preparation

- Open Loick's original visualization and show its direct azimuth/elevation controls.
- Open the adapted prototype and show the geographic and time controls.
- Change time or boat heading and show the Sun and shadow moving.
- Explain that the geometry is still simplified.
- Show the RP2 CAD model and identify the real sails and eight panels.
- Show the current extraction experiment and tessellated sail data if it runs reliably.
- Present the proposed CAD-to-React pipeline.
- Ask the supervisor to confirm the initial scope and accuracy target.
- Commit or clearly stage the solar work before the meeting; the current branch still has uncommitted solar files and Makefile changes.

## Technical references

- [Three.js Mesh documentation](https://threejs.org/docs/pages/Mesh.html): defines `Mesh` as representing triangular polygon mesh objects.
- [Three.js BufferGeometry documentation](https://threejs.org/docs/pages/BufferGeometry.html): explains vertex positions and indexed triangles.
- [Three.js custom BufferGeometry guide](https://threejs.org/manual/en/custom-buffergeometry.html): demonstrates constructing solid geometry from triangles.
- [Three.js WebGLRenderer documentation](https://threejs.org/docs/pages/WebGLRenderer.html): reports rendered triangle, line, and point primitives separately.
