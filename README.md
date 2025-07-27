# Hydro Suite - QGIS Hydrological Analysis Toolbox

A comprehensive, professional-grade hydrological analysis toolbox for QGIS 3.40+ that consolidates multiple watershed modeling tools into a unified interface.

![QGIS](https://img.shields.io/badge/QGIS-3.40+-green.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-production%20ready-brightgreen.svg)

## 🌊 Overview

Hydro Suite provides engineers and analysts with streamlined workflows for:
- Watershed modeling and analysis
- Stormwater infrastructure design  
- Regulatory compliance calculations
- Hydraulic modeling preparation

## ✨ Features

### 🔧 Integrated Tools

1. **Curve Number (CN) Calculator**
   - Area-weighted composite curve number calculations
   - Split hydrologic soil group handling (A/D, B/D, C/D)
   - SWMM/HEC-HMS compatible outputs
   - Batch processing capabilities

2. **Rational Method C Calculator**
   - Slope-based runoff coefficient calculations
   - Project-wide slope category selection
   - Unrecognized soil group handling
   - Professional reporting formats

3. **Time of Concentration Calculator**
   - Multiple methods: Kirpich, FAA, SCS/NRCS, Kerby
   - Method comparison and validation
   - Parameter customization
   - Statistical analysis

4. **Channel Designer**
   - Interactive trapezoidal channel cross-section design
   - Real-time geometric visualization
   - SWMM-compatible output format
   - Batch processing from CSV

### 🎯 Key Features

- **Professional GUI**: Consistent interface with real-time validation
- **Layer Integration**: Seamless QGIS layer and field selection
- **Batch Processing**: CSV import/export for bulk operations
- **Error Handling**: Comprehensive validation and user feedback
- **Progress Tracking**: Visual progress bars and detailed logging
- **Multiple Outputs**: Shapefiles, CSV reports, SWMM formats

## 🚀 Quick Start

### Prerequisites
- QGIS 3.40 or higher
- Python 3.9+ (included with QGIS)

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/hydro-suite.git
   cd hydro-suite/Hydro_Suite_Data
   ```

2. Launch in QGIS Python Console:
   ```python
   exec(open(r'path/to/hydro-suite/Hydro_Suite_Data/fixed_launch.py').read())
   ```

### Basic Usage

1. Launch the Hydro Suite from QGIS Python Console
2. Select a tool from the left panel
3. Configure input layers and parameters
4. Click "Run" when validation shows ✅
5. Review results and export as needed

## 📖 Documentation

- [Project Overview](PROJECT_README.md) - Detailed project documentation
- [Developer Guide](DEVELOPER_GUIDE.md) - How to extend and modify
- [API Reference](API_REFERENCE.md) - Complete API documentation
- [Changelog](CHANGELOG.md) - Version history and updates

## 🏗️ Architecture

```
Hydro_Suite_Data/
├── hydro_suite_main.py          # Main controller
├── hydro_suite_interface.py     # Base interfaces
├── shared_widgets.py            # Reusable UI components
├── cn_calculator_tool.py        # CN Calculator
├── rational_c_tool.py           # Rational C Calculator
├── tc_calculator_tool.py        # TC Calculator
├── channel_designer_tool.py     # Channel Designer
└── fixed_launch.py              # QGIS launcher
```

## 🤝 Contributing

We welcome contributions! Please see our [Developer Guide](DEVELOPER_GUIDE.md) for:
- Code style guidelines
- How to add new tools
- Testing procedures
- Pull request process

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Developed for QGIS 3.40+ community
- Implements industry-standard hydrological methods
- Built with PyQt5 and QGIS Python API

## 📧 Contact

For questions, issues, or contributions:
- Create an issue in this repository
- Review existing documentation first
- Check closed issues for common problems

## 🎯 Roadmap

### Version 1.1 (Next Release)
- QGIS plugin packaging
- Additional tool integration
- Performance optimizations

### Future Plans
- Cloud processing capabilities
- Advanced reporting features
- Additional hydrological tools

---

**Note**: This is an active project. See [CHANGELOG.md](CHANGELOG.md) for recent updates.