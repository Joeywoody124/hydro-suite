# QGIS Plugin Troubleshooting Guide

## 🔧 **Plugin Says "Broken" - Fixed Issues**

The following issues have been **FIXED** in the latest version:

### ✅ **Fixed Issues:**
1. **Duplicate category field** in metadata.txt
2. **Missing icon handling** - Plugin now works without icon.png
3. **QIcon initialization error** - Handles None icon path gracefully

## 🚀 **How to Test the Fixed Plugin**

### **Step 1: Update Plugin Files**
```cmd
# Pull latest fixes
git checkout plugin-version
git pull origin plugin-version

# Reinstall plugin
install_plugin.bat
```

### **Step 2: Enable Plugin in QGIS**
1. Open QGIS
2. Go to **Plugins → Manage and Install Plugins**
3. Click **"Installed"** tab
4. Find **"Hydro Suite"** and check the box
5. If it was already enabled, **uncheck and recheck** to reload

### **Step 3: Check for Success**
✅ **Plugin loads successfully if:**
- No "broken" indicator appears
- Hydro Suite appears in Plugins menu
- Toolbar icon appears (if toolbar is enabled)

## 🔍 **If Plugin Still Shows as Broken**

### **Method 1: Check Python Console**
1. Open QGIS
2. Go to **Plugins → Python Console**
3. Run these commands one by one:

```python
# Test plugin import
import sys
print("Python version:", sys.version)

# Test plugin directory
import os
plugin_dir = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "QGIS", "QGIS3", "profiles", "default", "python", "plugins", "hydro_suite_plugin")
print("Plugin directory exists:", os.path.exists(plugin_dir))
print("Plugin files:", os.listdir(plugin_dir) if os.path.exists(plugin_dir) else "Not found")

# Test basic import
try:
    import hydro_suite_plugin
    print("✅ Plugin import successful")
except Exception as e:
    print("❌ Plugin import failed:", e)

# Test specific modules
try:
    from hydro_suite_plugin.hydro_suite import HydroSuite
    print("✅ Main plugin class import successful")
except Exception as e:
    print("❌ Main plugin class import failed:", e)
```

### **Method 2: Check Plugin Files**
Run the debug batch file:
```cmd
debug_plugin.bat
```

This will check:
- Plugin directory structure
- Required files existence
- Metadata content
- Installation location

### **Method 3: Manual Verification**

1. **Check plugin directory:**
   ```
   C:\Users\[username]\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\hydro_suite_plugin\
   ```

2. **Required files should be present:**
   - `__init__.py`
   - `metadata.txt`
   - `hydro_suite.py`
   - `hydro_suite_main.py`
   - All tool files (`cn_calculator_tool.py`, etc.)

3. **Check metadata.txt format:**
   - No duplicate fields
   - Proper QGIS version (3.40)
   - Valid category

## 🎯 **Common Error Messages and Solutions**

### **"ModuleNotFoundError: No module named 'hydro_suite_plugin'"**
**Solution:**
```cmd
# Reinstall plugin
install_plugin.bat
# Restart QGIS
```

### **"ImportError: cannot import name 'HydroSuite'"**
**Solution:** Check if all files copied correctly
```cmd
debug_plugin.bat
# Look for missing files
```

### **"Plugin appears but doesn't start"**
**Solution:** Check Python Console for errors:
```python
# In QGIS Python Console
import hydro_suite_plugin
# Look for any error messages
```

### **"Icon not found" errors**
**Solution:** This is now fixed - plugin uses default icon

## 🔄 **Complete Reinstall Process**

If plugin still doesn't work, try complete reinstall:

### **Step 1: Remove Old Installation**
```cmd
# Delete plugin directory
rmdir /s /q "%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\hydro_suite_plugin"
```

### **Step 2: Fresh Install**
```cmd
git checkout plugin-version
git pull origin plugin-version
install_plugin.bat
```

### **Step 3: Restart QGIS Completely**
- Close QGIS entirely
- Reopen QGIS
- Enable plugin again

## 🐛 **Advanced Debugging**

### **Check QGIS Plugin Manager Log**
1. In QGIS, go to **View → Panels → Log Messages**
2. Look for plugin-related errors
3. Check timestamps around plugin loading

### **Check Python Path Issues**
```python
# In QGIS Python Console
import sys
print("Python paths:")
for path in sys.path:
    print("  ", path)
    
# Check if plugin directory is in path
plugin_dir = r"C:\Users\[username]\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins"
print("Plugin directory in path:", plugin_dir in sys.path)
```

### **Test Individual Components**
```python
# Test each component separately
try:
    from hydro_suite_plugin import hydro_suite_interface
    print("✅ Interface OK")
except Exception as e:
    print("❌ Interface:", e)

try:
    from hydro_suite_plugin import shared_widgets
    print("✅ Widgets OK")
except Exception as e:
    print("❌ Widgets:", e)
```

## 📞 **Getting Help**

If plugin still doesn't work:

1. **Run diagnostics:**
   ```cmd
   debug_plugin.bat
   ```

2. **Collect error messages** from:
   - QGIS Python Console
   - Plugin Manager
   - Log Messages panel

3. **Check versions:**
   - QGIS version (must be 3.40+)
   - Python version in QGIS
   - Plugin version

4. **Report issue** with:
   - Exact error messages
   - QGIS version
   - Operating system
   - Steps you tried

## ✅ **Success Indicators**

Plugin is working correctly when:
- ✅ No "broken" status in Plugin Manager
- ✅ "Hydro Suite" appears in Plugins menu
- ✅ Clicking it opens the main window
- ✅ All 4 tools are visible in the interface
- ✅ No error messages in Python Console

---

**Latest plugin fixes pushed to:** https://github.com/Jwoody124/hydro-suite/tree/plugin-version