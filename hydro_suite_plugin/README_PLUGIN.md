# Hydro Suite QGIS Plugin

This is the QGIS Plugin version of Hydro Suite. It integrates directly into QGIS as a native plugin.

## Installation

### Method 1: Manual Installation (Development)

1. **Copy plugin folder to QGIS plugins directory:**
   
   **Windows:**
   ```
   C:\Users\[username]\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\hydro_suite_plugin
   ```
   
   **macOS:**
   ```
   ~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/hydro_suite_plugin
   ```
   
   **Linux:**
   ```
   ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/hydro_suite_plugin
   ```

2. **Enable the plugin:**
   - Open QGIS
   - Go to Plugins → Manage and Install Plugins
   - Go to "Installed" tab
   - Find "Hydro Suite" and check the box

3. **Access the plugin:**
   - Look for Hydro Suite icon in toolbar
   - Or go to Plugins → Hydro Suite

### Method 2: ZIP Installation

1. **Create plugin ZIP:**
   ```bash
   cd hydro_suite_plugin
   zip -r hydro_suite_plugin.zip .
   ```

2. **Install ZIP in QGIS:**
   - Plugins → Manage and Install Plugins
   - "Install from ZIP" tab
   - Browse to your ZIP file
   - Install

## Usage

1. Click the Hydro Suite icon in the toolbar
2. The main Hydro Suite window will open
3. Use exactly like the standalone version

## Development

### Adding Custom Icon
- Replace `ICON_TODO.txt` with `icon.png` (24x24 pixels)
- Suggested themes: water droplet, watershed, or "HS" letters

### Plugin Structure
```
hydro_suite_plugin/
├── __init__.py              # Plugin entry point
├── hydro_suite.py           # Main plugin class
├── metadata.txt             # Plugin metadata
├── resources.py             # Qt resources
├── icon.png                 # Plugin icon (24x24 PNG)
├── hydro_suite_main.py      # Main application window
├── hydro_suite_interface.py # Base interfaces
├── shared_widgets.py        # UI components
├── cn_calculator_tool.py    # CN Calculator
├── rational_c_tool.py       # Rational C Calculator
├── tc_calculator_tool.py    # TC Calculator
└── channel_designer_tool.py # Channel Designer
```

## Differences from Standalone

- **Integration**: Runs as native QGIS plugin
- **Menu**: Accessible from Plugins menu
- **Icon**: Appears in QGIS toolbar
- **Lifecycle**: Managed by QGIS plugin system

## Troubleshooting

### Plugin Not Loading
1. Check QGIS Python Console for errors
2. Verify all files are in correct directory
3. Check metadata.txt format
4. Restart QGIS

### Import Errors
1. Ensure all Python files are in plugin directory
2. Check Python Console for specific error messages
3. Verify QGIS version compatibility (3.40+)

### Performance Issues
- Same as standalone version
- Use QGIS native layer loading for better performance

## Publishing

To publish to QGIS Plugin Repository:
1. Test thoroughly
2. Update metadata.txt with proper URLs
3. Create plugin ZIP
4. Submit to https://plugins.qgis.org/

## Support

- Same documentation as standalone version
- GitHub Issues: https://github.com/Jwoody124/hydro-suite/issues
- Use "plugin" tag when reporting plugin-specific issues