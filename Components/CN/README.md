# Composite Curve Number Calculator for QGIS

A QGIS Python tool for calculating area-weighted composite curve numbers for stormwater modeling applications.

## 📁 File Organization

```
E:\CLAUDE_Workspace\Claude\Report_Files\Codebase\
├── composite_cn_calculator_enhanced.py  # LATEST VERSION (v2.1) - Enhanced UI
├── composite_cn_calculator_fixed.py     # Stable version (v2.0) - Core fixes
├── Enhanced_Features_Guide.md           # Guide for v2.1 enhanced features
├── CN_Calculator_Debug_Guide.md         # Comprehensive debugging guide
├── CN_Calculator_Installation_Guide.md  # Installation and usage instructions
├── cn_calculator_test_suite.py         # Validation and testing tools
├── README.md                           # This file
└── sample_data/                        # (Create this folder for test data)
```

## 🚀 Quick Start

### **Latest Version (v2.1 Enhanced)** - Recommended
```python
# In QGIS Python Console - Enhanced version with project layer selection
exec(open(r'E:\CLAUDE_Workspace\Claude\Report_Files\Codebase\composite_cn_calculator_enhanced.py').read())
main()
```

**New Features in v2.1:**
- 📂 **Choose loaded project layers** OR browse for files
- 🔄 **Refresh button** to update layer lists
- 🎯 **Smart defaults** for lookup tables and output folders
- 🚀 **Auto-load results** back into QGIS project

### **Stable Version (v2.0)** - Core fixes only
```python
# In QGIS Python Console - Fixed version with file browsing only
exec(open(r'E:\CLAUDE_Workspace\Claude\Report_Files\Codebase\composite_cn_calculator_fixed.py').read())
main()
```

### **Verify Installation**
```python
# Run test suite
exec(open(r'E:\CLAUDE_Workspace\Claude\Report_Files\Codebase\cn_calculator_test_suite.py').read())
```

## 🛠️ What Was Fixed

### **Version 2.1 (Enhanced) - NEW**
- **✨ Project Layer Integration**: Select from loaded QGIS layers OR browse files
- **🎯 Smart Workflow**: Radio buttons to choose selection method
- **🔄 Refresh Capability**: Update layer lists without restarting
- **📂 Smart Defaults**: Auto-detects Global References and project folders
- **🚀 Auto-Load Results**: Option to load results back into QGIS project

### **Version 2.0 (Fixed) - Stable**
1. **❌ Field Validation Problems** → **✅ Dynamic field selection with validation**
2. **❌ Memory layer creation issues** → **✅ Proper memory layer handling**  
3. **❌ Intersection logic failures** → **✅ Robust intersection with error checking**
4. **❌ Limited lookup table support** → **✅ Multiple format compatibility**
5. **❌ Poor error handling** → **✅ Comprehensive error reporting**

### **Choose Your Version:**
- **Use v2.1 Enhanced** if you work with layers loaded in QGIS projects
- **Use v2.0 Fixed** if you prefer simple file browsing only
- **Both versions** have the same core calculation reliability

## 📋 Requirements

### Input Data:
- **Subbasin Layer**: Polygon shapefile with unique ID field
- **Land Use Layer**: Polygon shapefile with land use classification codes
- **Soils Layer**: Polygon shapefile with hydrologic soil group codes (A, B, C, D)
- **CN Lookup Table**: CSV/Excel with curve number values by land use and soil type

### Software:
- **QGIS 3.40.4** (primary target) or compatible version
- **Python packages**: pandas, pathlib (typically included with QGIS)

## 🎯 Expected Results

### Outputs:
1. **subbasins_cn.shp**: Shapefile with composite CN values
2. **cn_results.csv**: Summary table for model import

### Performance:
- **Small projects** (< 100 subbasins): 1-2 minutes
- **Medium projects** (100-1000 subbasins): 5-15 minutes
- **Large projects** (1000+ subbasins): 15+ minutes

## 🔧 Debugging Process

### Step 1: Environment Check
```python
# Test QGIS and Python environment
exec(open('cn_calculator_test_suite.py').read())
```

### Step 2: Data Validation
- Verify all layers load correctly
- Check field names match requirements
- Confirm geographic overlap between layers
- Validate lookup table format

### Step 3: Processing Issues
- Monitor QGIS Log Messages panel
- Check for geometry validity issues
- Verify coordinate system compatibility
- Review progress and error messages

### Step 4: Result Validation
- CN values should be 30-98 (typical range)
- Total areas should match expectations
- No NULL values unless expected
- Results should make intuitive sense

## 📊 Integration with Models

### SWMM Integration:
```python
# Use cn_results.csv to populate SWMM subcatchments
# Map Subbasin_ID to subcatchment names
# Import CN_Composite values to CN parameter
```

### HEC-HMS Integration:
```python
# Import subbasins_cn.shp as basin elements
# Use CN_Comp field for SCS Curve Number method
# Verify no missing values before model run
```

## 🚨 Common Issues & Solutions

| Issue | Symptoms | Solution |
|-------|----------|----------|
| Field not found | Error about missing fields | Use field dropdown menus |
| Empty intersection | No features result from intersection | Check layer overlap and geometry validity |
| Lookup format error | Unrecognized table format | Verify column names match expected format |
| Missing CN values | NULL results for some subbasins | Check land use codes match lookup table |

## 📚 Reference Materials

### Stormwater Modeling Standards:
- Located in: `E:\CLAUDE_Workspace\Claude\Report_Files\Templates\Global References\`
- **SWMM User Manual**: `swmm-users-manual-version-5.2.pdf`
- **EPA Storm Reference**: `EPA_Storm_Reference_VII HYD_ZyPDF.pdf`
- **CN Lookup Tables**: `CN_Current.csv`, `LCD_CN_Table.csv`

### Project Examples:
- **Crooked Cove Project**: `E:\CLAUDE_Workspace\Claude\Report_Files\Projects\2025_Project_Crooked\`
- **Template Structure**: `E:\CLAUDE_Workspace\Claude\Report_Files\Templates\File Structure\Project_X\`

## 🔄 Version History

### Version 2.0 (2025-05-31) - FIXED VERSION
- **Fixed**: All major field validation issues
- **Added**: Dynamic field selection interface
- **Improved**: Error handling and logging
- **Enhanced**: Lookup table format support
- **Updated**: Memory layer management

### Version 1.0 (Original)
- **Issues**: Multiple field validation problems
- **Issues**: Memory layer creation failures  
- **Issues**: Limited error handling
- **Status**: Deprecated - use v2.0

## 💡 Best Practices

### Data Preparation:
1. **Validate geometries** before processing
2. **Use consistent coordinate systems** across all layers
3. **Ensure complete coverage** of land use and soils
4. **Test with small datasets** before full runs

### Quality Control:
1. **Review log messages** for warnings
2. **Validate CN ranges** (30-98 typical)
3. **Check area calculations** against expectations
4. **Document data sources** and processing steps

### Model Integration:
1. **Save original data** before modifications
2. **Document field mappings** used
3. **Validate model input** files
4. **Test model runs** with new CN values

## 📞 Support

### Troubleshooting Priority:
1. **Check the Debug Guide** first: `CN_Calculator_Debug_Guide.md`
2. **Run the test suite** to validate setup
3. **Review QGIS log messages** for specific errors
4. **Test with simplified data** to isolate issues

### When Reporting Issues:
- QGIS version and system information
- Complete error messages from log
- Description of input data characteristics
- Steps to reproduce the problem

---

**Note**: This tool was developed for stormwater modeling applications and follows industry standards for curve number calculations. Always validate results against engineering judgment and local standards.
