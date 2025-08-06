# Recreation Prompt for Time of Concentration Calculator

## Overview
This document provides instructions for an LLM to recreate the Time of Concentration (TC) Calculator for QGIS from scratch. It includes all lessons learned, common pitfalls, and critical information needed for successful implementation.

## Initial Prompt

"Create a Time of Concentration calculator for QGIS 3.40+ that:
1. Uses proper SCS/NRCS TR-55 methodology (not simplified formulas)
2. Calculates slope from actual DEM data (not default values)
3. Processes multiple basins in batch mode
4. Works with South Carolina State Plane CRS (EPSG:3361)
5. Reads basin attributes: NAME, CN_Comp (curve number), AREA (acres)
6. Exports results to CSV format
7. Shows real-time progress during processing"

## Critical Technical Requirements

### 1. Processing Tool Chain (MUST USE THESE)
```python
# DEM Preprocessing - Use GDAL fillnodata
processing.run("gdal:fillnodata", {
    'INPUT': dem_layer,
    'BAND': 1,
    'DISTANCE': 10,
    'ITERATIONS': 0,
    'NO_MASK': False,
    'MASK_LAYER': None,
    'OPTIONS': '',
    'EXTRA': '',
    'OUTPUT': 'TEMPORARY_OUTPUT'
})

# Flow Analysis - Use GRASS r.watershed
processing.run("grass7:r.watershed", {
    'elevation': preprocessed_dem,
    'threshold': 1000,
    'max_slope_length': -1,
    'drainage': 'TEMPORARY_OUTPUT',
    'accumulation': 'TEMPORARY_OUTPUT',
    'GRASS_REGION_PARAMETER': None,
    'GRASS_REGION_CELLSIZE_PARAMETER': 0
})

# Slope Calculation - Use GDAL slope
processing.run("gdal:slope", {
    'INPUT': dem_layer,
    'BAND': 1,
    'SCALE': 1.0,
    'AS_PERCENT': True,
    'COMPUTE_EDGES': False,
    'ZEVENBERGEN': False,
    'OUTPUT': 'TEMPORARY_OUTPUT'
})
```

### 2. Correct SCS/NRCS TR-55 Formula
```python
# CRITICAL: Use this exact formula, not simplified versions
def calculate_tc_scs_tr55(length_ft, slope_percent, cn):
    # Retention parameter
    S = (1000.0 / cn) - 10.0
    
    # Lag time in hours (TR-55 equation)
    lag_hours = (length_ft**0.8 * (S + 1)**0.7) / (1900 * slope_percent**0.5)
    
    # Time of concentration
    tc_hours = lag_hours / 0.6
    
    return tc_hours * 60  # Return in minutes
```

### 3. QgsFeature Attribute Access
```python
# WRONG - will cause AttributeError
basin_name = basin_feature.get('NAME')  # QgsFeature has no 'get' method

# CORRECT - use bracket notation with try/except
try:
    basin_name = basin_feature['NAME']
except:
    basin_name = f'Basin_{basin_feature.id()}'
```

### 4. Field Name Variations
```python
# Basin identifier fields (check in order)
name_fields = ['NAME', 'Name', 'name', 'ID', 'Basin_ID']

# Curve number fields (check in order)
cn_fields = ['CN_Comp', 'CN', 'curve_number']

# Area fields (optional - calculate from geometry if missing)
area_fields = ['AREA', 'Area', 'area_acres']
```

## Common Errors and Solutions

### 1. "Processing algorithm not found"
**Cause**: GRASS/SAGA not installed or configured
**Solution**: 
- Check Processing → Options → Providers
- Ensure GRASS is active and path is correct
- Use fallback methods if tools unavailable

### 2. "CRS mismatch between layers"
**Cause**: Basin and DEM in different coordinate systems
**Solution**:
```python
# Validate CRS compatibility
if basin_layer.crs() != dem_layer.crs():
    raise ValueError(f"CRS mismatch: Basin ({basin_layer.crs().authid()}) != DEM ({dem_layer.crs().authid()})")
```

### 3. Incorrect area calculations
**Cause**: Geographic CRS or unit confusion
**Solution**:
```python
# Try attribute first, then calculate
try:
    area_acres = float(basin_feature['AREA'])
except:
    area_sq_m = basin_feature.geometry().area()
    area_acres = area_sq_m / 4046.86  # Convert m² to acres
```

### 4. Memory issues with large datasets
**Cause**: Processing entire dataset at once
**Solution**: Use QThread for background processing and process basins individually

## Workflow Example

```python
# 1. Load test data
basin_layer = QgsVectorLayer('path/to/basins.shp', 'Basins', 'ogr')
dem_layer = QgsRasterLayer('path/to/dem.tif', 'DEM')

# 2. Validate inputs
assert basin_layer.isValid() and dem_layer.isValid()
assert basin_layer.crs() == dem_layer.crs()

# 3. Preprocess DEM once
preprocessed_dem = preprocess_dem(dem_layer)

# 4. Calculate flow layers once
flow_layers = calculate_flow_layers(preprocessed_dem)

# 5. Process each basin
for basin in basin_layer.getFeatures():
    # Extract attributes
    basin_name = get_attribute(basin, ['NAME', 'Name'])
    cn = get_attribute(basin, ['CN_Comp', 'CN'], default=75)
    area = get_attribute(basin, ['AREA'], calculate=True)
    
    # Calculate slope for basin
    avg_slope = calculate_basin_slope(basin, preprocessed_dem)
    
    # Estimate hydraulic length
    hydraulic_length = estimate_hydraulic_length(basin)
    
    # Calculate TC
    tc_minutes = calculate_tc_scs_tr55(hydraulic_length, avg_slope, cn)
```

## Lessons Learned

### 1. Start Simple, Test Each Step
- Create single-step tester first to validate each component
- Don't try to build everything at once
- Test with single basin before scaling to multiple

### 2. Tool Availability Varies
- Not all QGIS installations have GRASS/SAGA
- Always provide fallback methods
- Test tool availability before using

### 3. Field Names Are Inconsistent
- Never hardcode field names
- Always provide field selection in GUI
- Use case-insensitive matching where possible

### 4. Performance Considerations
- Use threading for large datasets
- Process DEM once, not per basin
- Create spatial indexes before operations

### 5. User Experience
- Show clear progress during processing
- Provide detailed error messages
- Allow CSV export for further analysis

## Testing Checklist

- [ ] Single basin (0.86 acres) produces TC of 8-20 minutes
- [ ] Multi-basin processing completes without errors
- [ ] CSV export contains all fields
- [ ] Progress bar updates during processing
- [ ] Handles missing CN values (uses default)
- [ ] Handles missing AREA values (calculates from geometry)
- [ ] Works with different CRS (with warning if not EPSG:3361)
- [ ] Minimum slope of 1% enforced for stability

## File Structure
```
TC_NRCS_Stand_Alone/
├── tc_calculator_v6_final.py    # Main script
├── tc_single_step_test.py       # Diagnostic tool
├── README.md                    # User documentation
├── STATUS.md                    # Development status
├── CHANGELOG.md                 # Version history
├── Recreation_Prompt.md         # This file
└── Test_Data/
    └── Single_Basin.shp        # Test data (0.86 acres, CN=92)
```

## Final Notes

1. **Always validate preprocessing steps first** - Most failures occur during DEM preprocessing
2. **Use exact tool parameters shown above** - Small changes can cause failures
3. **Test with provided Single_Basin.shp** - Known good test case
4. **Check QGIS Python Console for errors** - GUI may hide important error messages
5. **Hydraulic length is estimated** - Full flow path tracing is complex and optional

## Success Criteria
- Produces scientifically valid TC values
- Processes 50+ basins efficiently
- No hardcoded paths or values
- Clear error messages for users
- Works "out of the box" in QGIS 3.40+

---
*This recreation guide is based on extensive testing and debugging of the TC Calculator through multiple iterations.*