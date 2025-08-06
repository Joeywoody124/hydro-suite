# TC Calculator Plugin Installation Instructions

## Method 1: Manual Installation (Recommended)

### Step 1: Locate QGIS Plugin Directory
Find your QGIS plugins directory:

**Windows:**
```
C:\Users\[your-username]\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\
```

**Linux:**
```
~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/
```

**macOS:**
```
~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/
```

### Step 2: Copy Plugin Files
1. Copy the entire `QGIS_Plugin` folder
2. Rename it to `tc_calculator` 
3. Place it in your QGIS plugins directory

Final structure should be:
```
plugins/
└── tc_calculator/
    ├── __init__.py
    ├── tc_calculator.py
    ├── tc_calculator_dialog.py
    ├── tc_calculator_dialog_base.ui
    ├── metadata.txt
    ├── resources.py
    ├── resources.qrc
    ├── icon.png
    ├── Makefile
    ├── README.md
    └── pb_tool.cfg
```

### Step 3: Enable Plugin in QGIS
1. **Restart QGIS**
2. Go to **Plugins → Manage and Install Plugins...**
3. Click the **Installed** tab
4. Find **"TC Calculator"** in the list
5. **Check the box** to enable it

### Step 4: Access the Plugin
The plugin will be available in:
- **Menu**: Vector → TC Calculator → Time of Concentration Calculator
- **Toolbar**: Look for the green TC icon

## Method 2: ZIP Installation

### Step 1: Create ZIP File
1. Copy the `QGIS_Plugin` folder
2. Rename it to `tc_calculator`
3. Create a ZIP file: `tc_calculator.zip`

### Step 2: Install via QGIS
1. Open QGIS
2. Go to **Plugins → Manage and Install Plugins...**
3. Click **Install from ZIP**
4. Browse to your `tc_calculator.zip` file
5. Click **Install Plugin**

## Troubleshooting

### Plugin Not Appearing in List
- Check the folder name is exactly `tc_calculator`
- Verify all files are present
- Restart QGIS completely
- Check QGIS Python Console for error messages

### "Processing algorithm not found" Errors
1. Go to **Processing → Options → Providers**
2. Ensure **GRASS** is enabled and configured
3. Ensure **GDAL** is enabled
4. Restart QGIS if needed

### Permission Issues (Windows)
- Run QGIS as Administrator when installing
- Check folder permissions in AppData

### Missing Dependencies
The plugin requires:
- QGIS 3.40+
- GRASS GIS (usually included with QGIS)
- GDAL tools (included with QGIS)

## Verification

Once installed successfully, you should see:
1. **Menu Item**: Vector → TC Calculator → Time of Concentration Calculator
2. **Toolbar Icon**: Green icon with "TC" text and calculator
3. **Plugin List**: "TC Calculator" appears in Plugins → Manage and Install Plugins → Installed

## First Use

1. Load a basin polygon layer with NAME, CN_Comp, and AREA fields
2. Load a DEM raster layer
3. Launch the plugin from Vector menu
4. Select your layers and click "Calculate Time of Concentration"

## Support

If you encounter issues:
1. Check QGIS Python Console (Plugins → Python Console) for error messages
2. Verify your data has the required fields: NAME, CN_Comp, AREA
3. Ensure both layers are in the same CRS (preferably EPSG:3361)

---
*Plugin developed with Claude AI assistance for scientific hydrologic analysis*