# Hydraulic Length Calculation in QGIS

**Author:** J. Bragg Consulting, Inc.  
**Version:** 1.0  
**Tool:** QGIS 3.40.4 (with WhiteboxTools plugin)  
**Script:** `calculate_flow_length.py`

---

## Purpose

This script calculates the **hydraulic length (longest flow path)** for a watershed using a filled DEM. The result is a vector line representing the path from the most distant point in the watershed to the outlet, following the terrain slope.

---

## Required Inputs

- A **filled DEM** raster layer (e.g., hydrologically corrected elevation).
- A **watershed boundary** polygon (used to clip the DEM).

---

## Outputs

- A vector line layer named `longest_flow_path.gpkg` representing the longest flow path.
- Intermediate flow direction and flow length rasters (stored in memory).

---

## Workflow Summary

1. **Clip** the DEM to the watershed boundary.
2. **Breach depressions** using WhiteboxTools.
3. **Compute downslope flow length**.
4. **Extract the longest flow path**.
5. **Output** is saved as a GPKG vector line file.

---

## Prerequisites

- QGIS 3.40+ with **WhiteboxTools Plugin** installed and enabled.
- Both input layers must be loaded in QGIS and named correctly in the script:
  - `filled_dem`
  - `watershed_boundary`

---

## Instructions

1. Open QGIS and load your filled DEM and watershed polygon.
2. Open the Python Console (Plugins > Python Console).
3. Paste the contents of `calculate_flow_length.py` and run.
4. The output vector will appear in the Layers Panel.

---

## Notes

- The script assumes all layers are projected in **feet/meters** depending on the DEM.
- Flow length is derived using surface slope, not hydraulic modeling.
- Results can be used to compute NRCS lag time using:

    ```
    t_lag = (0.8 * L^0.77) / (S^0.385)
    ```

---

## Support

For technical questions, contact:
> support@jbraggconsulting.com

