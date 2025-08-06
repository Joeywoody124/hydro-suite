"""
Launcher for Composite CN Calculator v2.2
Enhanced version with split HSG handling

Usage:
1. Copy and paste this entire script into the QGIS Python Console
2. Press Enter to execute
3. The CN Calculator dialog will open

Features:
- Handles split HSGs (A/D, B/D, C/D) by defaulting to more restrictive group
- Enhanced user interface with layer selection options
- Detailed CSV output with original HSG tracking
- Comprehensive error handling and logging
"""

import sys
import os
from pathlib import Path

def launch_cn_calculator():
    """Launch the Composite CN Calculator v2.2"""
    
    try:
        # Define the path to the CN calculator script
        script_path = r'E:\CLAUDE_Workspace\Claude\Report_Files\Codebase\CN'
        
        # Check if the path exists
        if not os.path.exists(script_path):
            print(f"ERROR: Script path not found: {script_path}")
            print("Please verify the path to the CN calculator script.")
            return False
        
        # Add the script path to Python path if not already there
        if script_path not in sys.path:
            sys.path.insert(0, script_path)
            print(f"Added to Python path: {script_path}")
        
        # Clear any previous imports to ensure we get the latest version
        module_name = 'composite_cn_calculator'
        if module_name in sys.modules:
            del sys.modules[module_name]
            print("Cleared previous module import")
        
        # Import and run the calculator
        print("Importing Composite CN Calculator v2.2...")
        from composite_cn_calculator import main
        
        print("Launching CN Calculator dialog...")
        result = main()
        
        print("CN Calculator execution completed.")
        return True
        
    except ImportError as e:
        print(f"IMPORT ERROR: {e}")
        print("Make sure the composite_cn_calculator.py file exists in the specified path.")
        return False
        
    except Exception as e:
        print(f"EXECUTION ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_environment():
    """Verify that the QGIS environment is ready"""
    
    try:
        # Check QGIS imports
        from qgis.core import QgsApplication
        from qgis.PyQt.QtWidgets import QDialog
        print("✓ QGIS environment verified")
        return True
        
    except ImportError as e:
        print(f"✗ QGIS environment error: {e}")
        print("This script must be run from within QGIS Python Console")
        return False

def check_dependencies():
    """Check for required dependencies"""
    
    missing_deps = []
    
    # Check pandas
    try:
        import pandas as pd
        print("✓ pandas available")
    except ImportError:
        missing_deps.append("pandas")
    
    # Check pathlib (should be standard)
    try:
        from pathlib import Path
        print("✓ pathlib available")
    except ImportError:
        missing_deps.append("pathlib")
    
    if missing_deps:
        print(f"✗ Missing dependencies: {', '.join(missing_deps)}")
        print("Install missing packages using: pip install pandas")
        return False
    
    return True

def main_launcher():
    """Main launcher function with comprehensive checks"""
    
    print("=" * 60)
    print("Composite CN Calculator v2.2 Launcher")
    print("Enhanced with Split HSG Handling")
    print("=" * 60)
    
    # Step 1: Verify QGIS environment
    print("\n1. Checking QGIS environment...")
    if not verify_environment():
        return
    
    # Step 2: Check dependencies
    print("\n2. Checking dependencies...")
    if not check_dependencies():
        return
    
    # Step 3: Launch the calculator
    print("\n3. Launching CN Calculator...")
    success = launch_cn_calculator()
    
    if success:
        print("\n" + "=" * 60)
        print("CN Calculator launched successfully!")
        print("New features in v2.2:")
        print("• Split HSG handling (A/D → D, B/D → D, etc.)")
        print("• Enhanced CSV output with original HSG tracking")
        print("• Improved error messages and logging")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("Failed to launch CN Calculator")
        print("Please check the error messages above")
        print("=" * 60)

# Execute the launcher
if __name__ == "__main__":
    main_launcher()
else:
    # This allows the script to be executed directly in QGIS console
    main_launcher()
