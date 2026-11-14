# Research methodology roadmap

## Research question

How can lunar surface topography and time-dependent Sun/Earth ephemerides be combined to compare candidate lunar south-pole sites for illumination and direct-to-Earth geometric visibility?

## Proposed pipeline

1. Acquire LOLA elevation, slope, count, and uncertainty rasters.
2. Validate the raster CRS and transform candidate coordinates into the raster coordinate system.
3. Query Horizons for Sun and Earth apparent azimuth/elevation at a documented cadence.
4. Compute a local terrain horizon angle for each azimuth from the DEM.
5. Mark a target as terrain-visible only when its apparent elevation exceeds the terrain horizon, with a documented angular margin.
6. Aggregate illumination and geometric Earth-visibility fractions over a defined mission interval.
7. Evaluate slope and data-confidence/coverage as separate criteria.
8. Compare sites using Pareto analysis or MCDA; report weights and sensitivity analysis.

## Avoid overclaiming

- Sun above the ellipsoid horizon is not equivalent to terrain-unobstructed sunlight.
- Earth geometrically visible is not equivalent to a working radio link. Antenna pattern, link budget, relay availability, hardware, and interference are separate.
- A composite site score is a decision aid, not a NASA-certified landing recommendation.
- Report uncertainty and missing DEM coverage; do not silently fill missing pixels and treat them as observations.
