# TC Calculator QGIS Plugin

## Installation

1. Copy the entire `tc_calculator` folder to your QGIS plugins directory:
   - **Windows**: `C:\Users\[username]\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\`
   - **Linux**: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - **macOS**: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`

2. Restart QGIS

3. Enable the plugin:
   - Go to **Plugins → Manage and Install Plugins**
   - Click **Installed** tab
   - Find "TC Calculator" and check the box to enable it

## Usage

1. Load your basin polygon layer and DEM raster layer in QGIS
2. Go to **Vector → TC Calculator → Time of Concentration Calculator**
3. Select your basin and DEM layers from the dropdowns
4. Click "Calculate Time of Concentration"
5. Export results to CSV when calculation is complete

## Requirements

- Basin layer with fields: NAME, CN_Comp, AREA (optional)
- DEM raster layer
- Both layers should be in the same CRS (preferably EPSG:3361)

## Features

- SCS/NRCS TR-55 methodology
- Multi-basin batch processing
- Real-time progress tracking
- CSV export functionality
- Comprehensive error handling