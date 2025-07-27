"""
Test script to validate plugin Python syntax
Run this to check for syntax errors before installing in QGIS
"""

import os
import sys
import importlib.util

def test_plugin_file(filepath, description):
    """Test a Python file for syntax errors"""
    print(f"Testing {description}: {os.path.basename(filepath)}")
    
    try:
        # Read and compile the file
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Compile to check syntax
        compile(source, filepath, 'exec')
        print(f"✅ {description} - Syntax OK")
        return True
        
    except SyntaxError as e:
        print(f"❌ {description} - Syntax Error:")
        print(f"   Line {e.lineno}: {e.text}")
        print(f"   Error: {e.msg}")
        return False
    except Exception as e:
        print(f"❌ {description} - Error: {e}")
        return False

def main():
    print("🧪 Testing Hydro Suite Plugin Files")
    print("=" * 50)
    
    plugin_dir = os.path.join(os.path.dirname(__file__), 'hydro_suite_plugin')
    
    if not os.path.exists(plugin_dir):
        print("❌ Plugin directory not found!")
        return False
    
    # Test files
    test_files = [
        ('__init__.py', 'Plugin Entry Point'),
        ('hydro_suite.py', 'Main Plugin Class'),
        ('hydro_suite_main.py', 'Main Window'),
        ('hydro_suite_interface.py', 'Base Interfaces'),
        ('shared_widgets.py', 'Shared Components'),
        ('cn_calculator_tool.py', 'CN Calculator'),
        ('rational_c_tool.py', 'Rational C Calculator'),
        ('tc_calculator_tool.py', 'TC Calculator'),
        ('channel_designer_tool.py', 'Channel Designer'),
    ]
    
    all_passed = True
    
    for filename, description in test_files:
        filepath = os.path.join(plugin_dir, filename)
        if os.path.exists(filepath):
            if not test_plugin_file(filepath, description):
                all_passed = False
        else:
            print(f"⚠️  {description} - File missing: {filename}")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All plugin files passed syntax check!")
        print("\nNext steps:")
        print("1. Run install_plugin.bat")
        print("2. Enable plugin in QGIS")
        print("3. Check QGIS Python Console for any runtime errors")
    else:
        print("❌ Some plugin files have issues!")
        print("Fix the errors above before installing in QGIS")
    
    return all_passed

if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")