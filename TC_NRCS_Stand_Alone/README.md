# Time of Concentration (TC) Calculator for QGIS

## Overview
A scientifically accurate Time of Concentration calculator for QGIS 3.40+ using the SCS/NRCS TR-55 methodology. This tool performs proper hydrologic analysis with DEM-based calculations for stormwater and watershed analysis.

**Version:** 6.0.0  
**Target CRS:** EPSG:3361 (NAD83 South Carolina State Plane)  
**Methodology:** SCS/NRCS TR-55  
**QGIS Version:** 3.40.4+  

## Features
- ✅ Multi-basin batch processing
- ✅ DEM-based slope calculation (no default assumptions)
- ✅ Flow accumulation analysis
- ✅ Hydraulic length estimation
- ✅ SCS lag time and TC calculations
- ✅ CSV export functionality
- ✅ Progress tracking with GUI
- ✅ Robust error handling

## Requirements

### Software
- QGIS 3.40+ with Processing Framework
- GRASS GIS 7+ (installed with QGIS)
- GDAL tools (installed with QGIS)

### Data Requirements
- **Basin Layer**: Polygon shapefile with:
  - `NAME` or `Name` field (basin identifier)
  - `CN_Comp` or `CN` field (composite curve number)
  - `AREA` field (optional, acres) - if not present, calculated from geometry
- **DEM Layer**: Raster elevation data covering all basins
- **CRS**: Both layers must be in the same coordinate system (preferably EPSG:3361)

## Installation

1. Clone or download this repository to your local machine
2. No additional installation required - runs directly in QGIS Python Console

## Usage

### Running the Calculator

1. **Open QGIS** and load your data:
   - Basin polygon layer
   - DEM raster layer

2. **Open Python Console** (Ctrl+Alt+P or Plugins → Python Console)

3. **Run the script**:
   ```python
   exec(open('E:/path/to/tc_calculator_v6_final.py').read())
   ```

4. **Use the GUI**:
   - Select your basin layer from the dropdown
   - Select your DEM layer from the dropdown
   - Click "Calculate Time of Concentration"
   - View results in the table
   - Export results to CSV if needed

### Runner Script Examples

For convenience, create these runner scripts in your QGIS Python Console:

**Single Basin Analysis:**
```python
# TC Calculator Runner - Single Basin
import os
script_path = r'E:\CLAUDE_Workspace\Claude\Report_Files\Codebase\Hydro_Suite\TC_NRCS_Stand_Alone\tc_calculator_v6_final.py'
exec(open(script_path).read())
```

**Multi-Basin Batch Processing:**
```python
# TC Calculator Runner - Multi Basin
# Ensure your multi-basin layer is loaded in QGIS first
import os
script_path = r'E:\CLAUDE_Workspace\Claude\Report_Files\Codebase\Hydro_Suite\TC_NRCS_Stand_Alone\tc_calculator_v6_final.py'
exec(open(script_path).read())
```

**Testing with Sample Data:**
```python
# TC Calculator - Test Mode
# First load Test_Data/Single_Basin.shp and your DEM
import os
base_path = r'E:\CLAUDE_Workspace\Claude\Report_Files\Codebase\Hydro_Suite\TC_NRCS_Stand_Alone'
test_basin = os.path.join(base_path, 'Test_Data', 'Single_Basin.shp')

# Load test data
layer = QgsVectorLayer(test_basin, "Single_Basin", "ogr")
QgsProject.instance().addMapLayer(layer)

# Run calculator
script_path = os.path.join(base_path, 'tc_calculator_v6_final.py')
exec(open(script_path).read())
```

## Calculation Methodology

### 1. DEM Preprocessing
- Uses GDAL `fillnodata` to fill voids
- Ensures hydrologically correct DEM

### 2. Flow Analysis
- GRASS `r.watershed` for flow direction and accumulation
- Identifies drainage patterns within each basin

### 3. Slope Calculation
- GDAL `slope` algorithm
- Calculates average slope across basin
- Minimum 1% slope enforced for stability

### 4. Hydraulic Length
- Estimates flow path length based on basin geometry
- Uses 0.7 × diagonal distance as approximation
- Future enhancement: actual flow path tracing

### 5. Time of Concentration
```
SCS Lag Time: tL = (L^0.8 × (S+1)^0.7) / (1900 × Y^0.5)
Where:
- L = Hydraulic length (feet)
- S = Retention parameter = (1000/CN) - 10
- Y = Average basin slope (percent)

Time of Concentration: TC = tL / 0.6
```

## Output Fields

| Field | Description | Units |
|-------|-------------|-------|
| Basin Name | Basin identifier | - |
| Area | Basin drainage area | acres |
| Avg Slope | Average basin slope | percent |
| Hydraulic Length | Estimated flow path | feet |
| Curve Number | Composite CN | - |
| Lag Time | SCS lag time | minutes |
| Tc | Time of concentration | minutes |
| Tc (hours) | Time of concentration | hours |

## Troubleshooting

### Common Issues

**"No module named 'processing'"**
- Ensure QGIS Processing plugin is enabled
- Restart QGIS after enabling

**"GRASS algorithms not found"**
- Install GRASS through QGIS installer
- Check Processing → Options → Providers → GRASS

**"CRS mismatch" error**
- Reproject layers to same CRS
- Use Project → Properties → CRS

**Incorrect area calculations**
- Check CRS units (should be feet/meters)
- Verify AREA field contains correct values
- Check projection (EPSG:3361 recommended)

**Missing attributes**
- Ensure fields exist: NAME, CN_Comp, AREA
- Field names are case-sensitive
- Use Field Calculator to create missing fields

## File Structure
```
TC_NRCS_Stand_Alone/
├── tc_calculator_v6_final.py    # Main calculator script
├── tc_single_step_test.py       # Diagnostic tool
├── README.md                    # This file
├── STATUS.md                    # Development status
├── CHANGELOG.md                 # Version history
├── Recreation_Prompt.md         # LLM recreation guide
├── Test_Data/
│   └── Single_Basin.shp        # Test basin (0.86 acres)
├── Test_Results/
│   └── tc_results.csv          # Example output
└── Archive/
    └── Previous_Versions/      # Old script versions
```

## Version History

- **v6.0.0** (2025-01) - Final production version with validated tool chain
- **v2.0.0** (2025-01) - Comprehensive calculator with GUI
- **v1.0.0** (2025-01) - Single-step tester for troubleshooting
- Previous versions archived for reference

## Contributing

To modify or enhance this tool:
1. Test changes with single basin first
2. Validate with multi-basin dataset
3. Update version number and CHANGELOG.md
4. Document any new field requirements

## License

This tool was developed for stormwater and watershed analysis in South Carolina.
Free to use and modify for engineering analysis purposes.

## Support

For issues or questions:
1. Check troubleshooting section
2. Review Recreation_Prompt.md for technical details
3. Ensure all data requirements are met
4. Verify QGIS processing providers are configured

---
*Developed with Claude AI assistance for scientific hydrologic analysis*