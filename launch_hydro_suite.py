"""
Hydro Suite Launcher
Simple launcher script for testing the Hydro Suite framework in QGIS
Version 1.0 - 2025

Usage:
1. Copy this file to a location accessible from QGIS
2. In QGIS Python Console, run:
   exec(open(r'path/to/launch_hydro_suite.py').read())
"""

import os
import sys
from pathlib import Path

def launch_hydro_suite():
    """Launch the Hydro Suite application"""
    
    # Get the directory containing this script
    # Handle case where __file__ is not defined (QGIS console execution)
    try:
        script_dir = Path(__file__).parent
    except NameError:
        # When executed from QGIS console, use the known path
        script_dir = Path(r'E:\CLAUDE_Workspace\Claude\Report_Files\Codebase\Hydro_Suite\Hydro_Suite_Data')
    
    # Add the directory to Python path if not already there
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    
    try:
        # Import and launch the main application
        from hydro_suite_main import HydroSuiteMainWindow
        
        # Check if instance already exists and close it
        global hydro_suite_window
        try:
            if 'hydro_suite_window' in globals() and hydro_suite_window:
                hydro_suite_window.close()
                hydro_suite_window.deleteLater()
        except:
            pass
        
        # Create and show new window
        hydro_suite_window = HydroSuiteMainWindow()
        hydro_suite_window.show()
        
        # Log successful launch
        from qgis.core import QgsMessageLog, Qgis
        QgsMessageLog.logMessage(
            "Hydro Suite launched successfully", 
            "HydroSuite", 
            Qgis.Info
        )
        
        return hydro_suite_window
        
    except ImportError as e:
        from qgis.PyQt.QtWidgets import QMessageBox
        QMessageBox.critical(
            None,
            "Import Error",
            f"Failed to import Hydro Suite modules:\n{str(e)}\n\n"
            f"Please ensure all files are in the correct location:\n{script_dir}"
        )
        return None
        
    except Exception as e:
        from qgis.PyQt.QtWidgets import QMessageBox
        QMessageBox.critical(
            None,
            "Launch Error", 
            f"Failed to launch Hydro Suite:\n{str(e)}"
        )
        return None

# Auto-launch when script is executed
if __name__ == "__main__":
    window = launch_hydro_suite()
else:
    # Also launch when exec'd from console
    window = launch_hydro_suite()