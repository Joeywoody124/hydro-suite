"""
Time of Concentration QGIS Plugin - MULTI-METHOD VERSION
Version 3.0.0 - Professional-grade plugin with multiple TC calculation methods
Supports Kirpich, FAA, SCS/NRCS Lag Time, and Kerby methods with comparative analysis
"""
import os
import sys
import importlib
import traceback
from typing import Optional

from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QObject, pyqtSignal
from qgis.core import QgsMessageLog, Qgis, QgsApplication


class TimeOfConcentrationPlugin(QObject):
    """Main plugin class for Multi-Method Time of Concentration Calculator"""
    
    # Signal for when dialog needs to be opened
    dialog_requested = pyqtSignal()
    
    def __init__(self, iface):
        """Initialize the multi-method plugin"""
        super().__init__()
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = 'Time of Concentration'
        self.toolbar = None
        self.dialog = None
        
        # Ensure plugin directory is in Python path
        if self.plugin_dir not in sys.path:
            sys.path.insert(0, self.plugin_dir)
            
        # Log plugin initialization
        QgsMessageLog.logMessage(
            f"=== TC MULTI-METHOD PLUGIN v3.0.0 INITIALIZING ===",
            "TC Calculator Multi",
            Qgis.Info
        )
        QgsMessageLog.logMessage(
            f"Plugin directory: {self.plugin_dir}",
            "TC Calculator Multi",
            Qgis.Info
        )
        QgsMessageLog.logMessage(
            f"Available methods: Kirpich, FAA, SCS/NRCS, Kerby",
            "TC Calculator Multi",
            Qgis.Info
        )
        
    def initGui(self):
        """Initialize the GUI elements"""
        # Create toolbar
        self.toolbar = self.iface.addToolBar('Time of Concentration Multi-Method')
        self.toolbar.setObjectName('TimeOfConcentrationMultiMethodToolbar')
        
        # Create action
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()
        
        self.action = QAction(
            icon,
            "Time of Concentration Calculator - Multiple Methods", 
            self.iface.mainWindow()
        )
        
        # Set action properties
        self.action.setObjectName('tcMultiMethodCalculatorAction')
        self.action.setWhatsThis(
            "Calculate time of concentration for watershed subbasins using multiple methods"
        )
        self.action.setStatusTip(
            "Multi-method TC Calculator: Kirpich, FAA, SCS/NRCS, Kerby with comparative analysis"
        )
        
        # Connect action
        self.action.triggered.connect(self.run)
        self.action.setEnabled(True)
        
        # Add to interface
        self.iface.addPluginToMenu(self.menu, self.action)
        self.toolbar.addAction(self.action)
        self.actions.append(self.action)
        
        # Log successful initialization
        QgsMessageLog.logMessage(
            "Multi-Method Time of Concentration plugin GUI initialized successfully",
            "TC Calculator Multi",
            Qgis.Info
        )

    def unload(self):
        """Remove the plugin menu item and icon"""
        try:
            # Remove menu items and toolbar icons
            for action in self.actions:
                self.iface.removePluginMenu(self.menu, action)
                self.iface.removeToolBarIcon(action)
            
            # Remove toolbar
            if self.toolbar:
                self.toolbar.deleteLater()
                del self.toolbar
            
            # Close dialog if open
            if self.dialog:
                self.dialog.close()
                self.dialog = None
                
            # FORCE CLEANUP ALL CACHED MODULES
            self._force_cleanup_all_modules()
                
            QgsMessageLog.logMessage(
                "Multi-Method Time of Concentration plugin unloaded successfully",
                "TC Calculator Multi",
                Qgis.Info
            )
            
        except Exception as e:
            QgsMessageLog.logMessage(
                f"Error unloading multi-method plugin: {str(e)}",
                "TC Calculator Multi",
                Qgis.Warning
            )
    
    def _force_cleanup_all_modules(self):
        """AGGRESSIVELY clean up all modules related to this plugin"""
        modules_to_remove = []
        
        # Find ALL modules that could be from our plugin
        for module_name in list(sys.modules.keys()):
            module = sys.modules.get(module_name)
            if module and hasattr(module, '__file__') and module.__file__:
                module_file = module.__file__
                # If module file is in our plugin directory, mark for removal
                if self.plugin_dir in module_file:
                    modules_to_remove.append(module_name)
                    
            # Also remove any module that starts with our known module names
            if module_name in ['tc_processing', 'time_of_concentration_dialog']:
                modules_to_remove.append(module_name)
        
        # Remove all found modules
        for module_name in modules_to_remove:
            try:
                if module_name in sys.modules:
                    del sys.modules[module_name]
                    QgsMessageLog.logMessage(
                        f"Removed cached module: {module_name}",
                        "TC Calculator Multi",
                        Qgis.Info
                    )
            except Exception as e:
                QgsMessageLog.logMessage(
                    f"Error removing module {module_name}: {str(e)}",
                    "TC Calculator Multi",
                    Qgis.Warning
                )

    def run(self):
        """Run the plugin - show the multi-method dialog with FORCED MODULE RELOAD"""
        try:
            QgsMessageLog.logMessage(
                "=== STARTING MULTI-METHOD PLUGIN RUN WITH FORCED RELOAD ===",
                "TC Calculator Multi",
                Qgis.Info
            )
            
            # STEP 1: FORCE CLEANUP
            QgsMessageLog.logMessage(
                "STEP 1: Force cleaning up cached modules...",
                "TC Calculator Multi",
                Qgis.Info
            )
            self._force_cleanup_all_modules()
            
            # STEP 2: VERIFY FILES EXIST
            QgsMessageLog.logMessage(
                "STEP 2: Verifying multi-method plugin files exist...",
                "TC Calculator Multi",
                Qgis.Info
            )
            if not self._verify_plugin_files():
                return
            
            # STEP 3: VERIFY MULTI-METHOD PROCESSING MODULE
            QgsMessageLog.logMessage(
                "STEP 3: Verifying multi-method tc_processing module...",
                "TC Calculator Multi",
                Qgis.Info
            )
            
            # Try to import and verify the processing module
            try:
                from . import tc_processing
                
                if hasattr(tc_processing, 'TimeOfConcentrationCalculator'):
                    calc_class = tc_processing.TimeOfConcentrationCalculator
                    test_calc = calc_class()
                    
                    # Check for multi-method signature
                    import inspect
                    sig = inspect.signature(test_calc.calculate_tc_for_subbasins)
                    if 'selected_methods' in sig.parameters:
                        QgsMessageLog.logMessage(
                            "✓ Multi-method capabilities confirmed in processing module",
                            "TC Calculator Multi",
                            Qgis.Info
                        )
                        
                        # Check for method factory
                        if hasattr(tc_processing, 'TCMethodFactory'):
                            available_methods = tc_processing.TCMethodFactory.get_available_methods()
                            QgsMessageLog.logMessage(
                                f"✓ Available methods: {', '.join(available_methods)}",
                                "TC Calculator Multi",
                                Qgis.Info
                            )
                        else:
                            QgsMessageLog.logMessage(
                                "⚠️ TCMethodFactory not found - may be using old version",
                                "TC Calculator Multi",
                                Qgis.Warning
                            )
                    else:
                        QgsMessageLog.logMessage(
                            "✗ Multi-method signature not found - using single-method version",
                            "TC Calculator Multi",
                            Qgis.Critical
                        )
                        QMessageBox.critical(
                            self.iface.mainWindow(),
                            "Multi-Method Processing Error",
                            "The processing module does not support multi-method capabilities.\n\n"
                            "Please check that the correct version is installed."
                        )
                        return
                else:
                    QgsMessageLog.logMessage(
                        "✗ tc_processing module missing TimeOfConcentrationCalculator class",
                        "TC Calculator Multi",
                        Qgis.Critical
                    )
                    QMessageBox.critical(
                        self.iface.mainWindow(),
                        "Processing Module Error",
                        "The processing module is missing the required TimeOfConcentrationCalculator class."
                    )
                    return
                    
            except ImportError as e:
                QgsMessageLog.logMessage(
                    f"✗ Could not import tc_processing module: {str(e)}",
                    "TC Calculator Multi",
                    Qgis.Critical
                )
                QMessageBox.critical(
                    self.iface.mainWindow(),
                    "Module Import Error",
                    f"Failed to import tc_processing module:\n{str(e)}\n\n"
                    "Please check that all plugin files are present and valid."
                )
                return
            
            # STEP 4: IMPORT MULTI-METHOD DIALOG
            QgsMessageLog.logMessage(
                "STEP 4: Importing multi-method dialog module...",
                "TC Calculator Multi",
                Qgis.Info
            )
            if self._import_dialog():
                self._show_dialog()
            
        except Exception as e:
            QgsMessageLog.logMessage(
                f"✗ Error running multi-method plugin: {str(e)}\n{traceback.format_exc()}",
                "TC Calculator Multi",
                Qgis.Critical
            )
            QMessageBox.critical(
                self.iface.mainWindow(),
                "Multi-Method Time of Concentration Error",
                f"Failed to open the multi-method plugin dialog:\n{str(e)}\n\n"
                "Please check the QGIS Python console for more details."
            )
    
    def _verify_plugin_files(self) -> bool:
        """Verify that all required plugin files exist"""
        required_files = [
            ('tc_processing.py', 'Multi-method processing module'),
            ('time_of_concentration_dialog.py', 'Multi-method dialog module'),
            ('__init__.py', 'Plugin initialization'),
            ('metadata.txt', 'Plugin metadata')
        ]
        
        missing_files = []
        
        for filename, description in required_files:
            filepath = os.path.join(self.plugin_dir, filename)
            if not os.path.exists(filepath):
                missing_files.append(f"{description} ({filename})")
                QgsMessageLog.logMessage(
                    f"Required file not found: {filepath}",
                    "TC Calculator Multi",
                    Qgis.Critical
                )
            else:
                QgsMessageLog.logMessage(
                    f"✓ Found required file: {filepath}",
                    "TC Calculator Multi",
                    Qgis.Info
                )
        
        if missing_files:
            QMessageBox.critical(
                self.iface.mainWindow(),
                "Missing Multi-Method Plugin Files",
                f"The following required files are missing:\n\n" +
                "\n".join(missing_files) +
                f"\n\nExpected location: {self.plugin_dir}\n\n"
                "Please ensure the multi-method plugin is properly installed."
            )
            return False
            
        return True
    
    def _import_dialog(self) -> bool:
        """Import the multi-method dialog module"""
        try:
            # Try simple import first
            from .time_of_concentration_dialog import TimeOfConcentrationDialog
            self.dialog_class = TimeOfConcentrationDialog
            
            QgsMessageLog.logMessage(
                "✓ Multi-method dialog module loaded successfully",
                "TC Calculator Multi",
                Qgis.Info
            )
            return True
            
        except ImportError as e:
            QgsMessageLog.logMessage(
                f"Import error: {str(e)}",
                "TC Calculator Multi",
                Qgis.Critical
            )
            
            # Try dynamic import as fallback
            try:
                dialog_path = os.path.join(self.plugin_dir, "time_of_concentration_dialog.py")
                QgsMessageLog.logMessage(
                    f"Trying dynamic import from: {dialog_path}",
                    "TC Calculator Multi",
                    Qgis.Info
                )
                
                import importlib.util
                spec = importlib.util.spec_from_file_location("dialog_multi", dialog_path)
                if spec and spec.loader:
                    dialog_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(dialog_module)
                    
                    if hasattr(dialog_module, 'TimeOfConcentrationDialog'):
                        self.dialog_class = dialog_module.TimeOfConcentrationDialog
                        QgsMessageLog.logMessage(
                            "✓ Dialog loaded via dynamic import",
                            "TC Calculator Multi",
                            Qgis.Info
                        )
                        return True
                    else:
                        QgsMessageLog.logMessage(
                            "✗ Dialog module missing TimeOfConcentrationDialog class",
                            "TC Calculator Multi",
                            Qgis.Critical
                        )
                        return False
                else:
                    QgsMessageLog.logMessage(
                        "✗ Could not create spec for dialog module",
                        "TC Calculator Multi",
                        Qgis.Critical
                    )
                    return False
                    
            except Exception as e2:
                QgsMessageLog.logMessage(
                    f"Dynamic import also failed: {str(e2)}",
                    "TC Calculator Multi",
                    Qgis.Critical
                )
                QMessageBox.critical(
                    self.iface.mainWindow(),
                    "Import Error",
                    f"Failed to import dialog module:\n{str(e)}\n\n"
                    f"Dynamic import error: {str(e2)}\n\n"
                    "Please check that all plugin files are present and valid."
                )
                return False
    
    def _show_dialog(self):
        """Show the multi-method plugin dialog"""
        try:
            # Create new dialog instance
            self.dialog = self.dialog_class(self.iface.mainWindow(), self.iface)
            
            # Connect dialog signals if needed
            self.dialog.finished.connect(self._on_dialog_closed)
            
            # Show the dialog
            self.dialog.show()
            
            QgsMessageLog.logMessage(
                "✓ Multi-method dialog opened successfully",
                "TC Calculator Multi",
                Qgis.Info
            )
            
        except Exception as e:
            QgsMessageLog.logMessage(
                f"✗ Error showing multi-method dialog: {str(e)}",
                "TC Calculator Multi",
                Qgis.Critical
            )
            QMessageBox.critical(
                self.iface.mainWindow(),
                "Dialog Error",
                f"Failed to show multi-method dialog:\n{str(e)}"
            )
    
    def _on_dialog_closed(self, result):
        """Handle dialog closed event"""
        self.dialog = None
        QgsMessageLog.logMessage(
            f"Multi-method dialog closed with result: {result}",
            "TC Calculator Multi",
            Qgis.Info
        )
