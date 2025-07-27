"""
Hydro Suite - Main Controller
Unified hydrological analysis toolbox for QGIS 3.40+
Version 1.0 - 2025
"""

import os
import sys
import importlib
import json
from pathlib import Path
from typing import Dict, Optional, Any

from qgis.PyQt.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget,
    QLabel, QPushButton, QProgressBar, QMessageBox,
    QFrame, QSplitter, QTextEdit, QToolBar, QAction,
    QMenuBar, QMenu, QStatusBar
)
from qgis.PyQt.QtCore import Qt, QSettings, pyqtSignal, QThread
from qgis.PyQt.QtGui import QIcon, QFont, QPixmap
from qgis.core import QgsProject, QgsMessageLog, Qgis
from qgis.gui import QgsGui

# Import the tool interface base class
from hydro_suite_interface import HydroToolInterface


class HydroSuiteController:
    """Main controller for the Hydro Suite toolbox"""
    
    def __init__(self):
        self.tools_registry = {}
        self.settings = QSettings("HydroSuite", "MainController")
        self.components_path = Path(__file__).parent / "Components"
        self.resources_path = Path(__file__).parent / "Resources"
        
        # Initialize logging
        QgsMessageLog.logMessage("Hydro Suite Controller initializing...", "HydroSuite", Qgis.Info)
        
        # Load available tools
        self.discover_tools()
    
    def discover_tools(self):
        """Discover and register available tools"""
        # Define tool configurations
        tool_configs = {
            "cn_calculator": {
                "name": "Curve Number Calculator",
                "module": "CN.composite_cn_calculator",
                "class": "CompositeCNTool",
                "icon": "cn_icon.png",
                "category": "Runoff Analysis",
                "description": "Calculate area-weighted composite curve numbers for hydrological modeling"
            },
            "c_calculator": {
                "name": "Rational C Calculator",
                "module": "Rational_C.composite_C_calculator",
                "class": "RationalCTool",
                "icon": "c_icon.png",
                "category": "Runoff Analysis",
                "description": "Calculate composite runoff coefficients for rational method analysis"
            },
            "tc_calculator": {
                "name": "Time of Concentration",
                "module": "TC_Multi_Method_Single_Basin.tc_wrapper",
                "class": "TimeOfConcentrationTool",
                "icon": "tc_icon.png",
                "category": "Watershed Analysis",
                "description": "Calculate time of concentration using multiple methods"
            },
            "channel_designer": {
                "name": "Channel Designer",
                "module": "Channel_Designer.channel_designer_wrapper",
                "class": "ChannelDesignerTool",
                "icon": "channel_icon.png",
                "category": "Hydraulic Design",
                "description": "Design trapezoidal channels for hydraulic modeling"
            }
        }
        
        # Register each tool
        for tool_id, config in tool_configs.items():
            self.register_tool(tool_id, config)
            
        QgsMessageLog.logMessage(
            f"Discovered {len(self.tools_registry)} tools", 
            "HydroSuite", 
            Qgis.Info
        )
    
    def register_tool(self, tool_id: str, config: Dict[str, Any]):
        """Register a tool in the registry"""
        self.tools_registry[tool_id] = {
            "id": tool_id,
            "config": config,
            "instance": None,  # Lazy loading
            "loaded": False
        }
    
    def load_tool(self, tool_id: str) -> Optional[HydroToolInterface]:
        """Load a tool instance (lazy loading)"""
        if tool_id not in self.tools_registry:
            QgsMessageLog.logMessage(
                f"Tool {tool_id} not found in registry", 
                "HydroSuite", 
                Qgis.Warning
            )
            return None
        
        tool_info = self.tools_registry[tool_id]
        
        # Return existing instance if already loaded
        if tool_info["loaded"] and tool_info["instance"]:
            return tool_info["instance"]
        
        try:
            # Import the tool module
            module_path = tool_info["config"]["module"]
            module_name = f"Components.{module_path}"
            
            # For existing tools, we'll create wrapper classes
            # This is a placeholder - actual implementation would wrap existing tools
            QgsMessageLog.logMessage(
                f"Loading tool module: {module_name}", 
                "HydroSuite", 
                Qgis.Info
            )
            
            # Create a mock instance for now
            # In production, this would actually import and instantiate the tool
            tool_info["instance"] = self.create_tool_wrapper(tool_id, tool_info["config"])
            tool_info["loaded"] = True
            
            return tool_info["instance"]
            
        except Exception as e:
            QgsMessageLog.logMessage(
                f"Error loading tool {tool_id}: {str(e)}", 
                "HydroSuite", 
                Qgis.Critical
            )
            return None
    
    def create_tool_wrapper(self, tool_id: str, config: Dict[str, Any]) -> HydroToolInterface:
        """Create a wrapper for existing tools"""
        
        # Import actual tools
        if tool_id == "cn_calculator":
            from cn_calculator_tool import CNCalculatorTool
            return CNCalculatorTool()
        elif tool_id == "c_calculator":
            from rational_c_tool import RationalCTool
            return RationalCTool()
        elif tool_id == "tc_calculator":
            from tc_calculator_tool import TCCalculatorTool
            return TCCalculatorTool()
        
        # For other tools, return mock until implemented
        class MockTool(HydroToolInterface):
            def __init__(self):
                super().__init__()
                self.name = config["name"]
                self.description = config["description"]
                self.category = config["category"]
                self.icon = config.get("icon", "default_icon.png")
                self.tool_id = tool_id
            
            def create_gui(self, parent_widget):
                """Create mock GUI"""
                widget = QWidget(parent_widget)
                layout = QVBoxLayout(widget)
                
                # Title
                title = QLabel(f"<h2>{self.name}</h2>")
                layout.addWidget(title)
                
                # Description
                desc = QLabel(self.description)
                desc.setWordWrap(True)
                layout.addWidget(desc)
                
                # Implementation status
                status_label = QLabel("🚧 This tool is being migrated to the new framework")
                status_label.setAlignment(Qt.AlignCenter)
                status_label.setStyleSheet("""
                    QLabel {
                        border: 2px dashed #ff9800;
                        padding: 20px;
                        background-color: #fff3e0;
                        border-radius: 8px;
                        color: #f57c00;
                        font-weight: bold;
                    }
                """)
                layout.addWidget(status_label)
                
                # Placeholder for future implementation
                placeholder = QLabel(f"Full {self.name} interface coming soon...")
                placeholder.setAlignment(Qt.AlignCenter)
                placeholder.setStyleSheet("""
                    QLabel {
                        padding: 20px;
                        color: #666;
                        font-style: italic;
                    }
                """)
                layout.addWidget(placeholder)
                
                layout.addStretch()
                return widget
            
            def validate_inputs(self):
                return True, "Mock tool - validation not implemented"
            
            def run(self, progress_callback):
                QMessageBox.information(
                    None, 
                    "Tool Under Development",
                    f"The {self.name} tool is being integrated into the new framework.\n\n"
                    f"For now, please use the original standalone version:\n"
                    f"Module: {config['module']}\n\n"
                    f"This tool will be fully integrated soon!"
                )
        
        return MockTool()
    
    def get_tool_categories(self) -> Dict[str, list]:
        """Get tools organized by category"""
        categories = {}
        for tool_id, tool_info in self.tools_registry.items():
            category = tool_info["config"]["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(tool_id)
        return categories


class HydroSuiteMainWindow(QMainWindow):
    """Main window for the Hydro Suite toolbox"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.controller = HydroSuiteController()
        self.current_tool = None
        
        self.setWindowTitle("Hydro Suite - Hydrological Analysis Tools")
        self.setMinimumSize(1000, 700)
        
        # Setup UI
        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_statusbar()
        
        # Load settings
        self.load_settings()
        
        # Select first tool by default
        if self.tool_list.count() > 0:
            self.tool_list.setCurrentRow(0)
    
    def setup_ui(self):
        """Setup the main UI layout"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main horizontal layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Tool selection
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Tool interface and log
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter sizes (30% / 70%)
        splitter.setSizes([300, 700])
    
    def create_left_panel(self) -> QWidget:
        """Create the left tool selection panel"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        panel.setMinimumWidth(250)
        
        layout = QVBoxLayout(panel)
        
        # Title
        title = QLabel("Available Tools")
        title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                background-color: #2c3e50;
                color: white;
                border-radius: 4px;
            }
        """)
        layout.addWidget(title)
        
        # Tool list
        self.tool_list = QListWidget()
        self.tool_list.setStyleSheet("""
            QListWidget {
                font-size: 14px;
                border: none;
                background-color: #f8f9fa;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #dee2e6;
            }
            QListWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e9ecef;
            }
        """)
        
        # Populate tool list by category
        categories = self.controller.get_tool_categories()
        for category, tool_ids in categories.items():
            # Add category header
            category_item = QListWidgetItem(f"━━ {category} ━━")
            category_item.setFlags(Qt.NoItemFlags)
            category_item.setFont(QFont("Arial", 10, QFont.Bold))
            self.tool_list.addItem(category_item)
            
            # Add tools in category
            for tool_id in tool_ids:
                tool_info = self.controller.tools_registry[tool_id]
                tool_item = QListWidgetItem(f"  ▸ {tool_info['config']['name']}")
                tool_item.setData(Qt.UserRole, tool_id)
                self.tool_list.addItem(tool_item)
        
        # Connect selection change
        self.tool_list.currentItemChanged.connect(self.on_tool_selected)
        
        layout.addWidget(self.tool_list)
        
        # Info button
        info_btn = QPushButton("ℹ About Selected Tool")
        info_btn.clicked.connect(self.show_tool_info)
        layout.addWidget(info_btn)
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """Create the right panel with tool interface and log"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create vertical splitter for tool area and log
        v_splitter = QSplitter(Qt.Vertical)
        layout.addWidget(v_splitter)
        
        # Tool interface area
        self.tool_stack = QStackedWidget()
        self.tool_stack.setMinimumHeight(400)
        
        # Add welcome screen
        welcome = self.create_welcome_screen()
        self.tool_stack.addWidget(welcome)
        
        v_splitter.addWidget(self.tool_stack)
        
        # Log area
        log_frame = QFrame()
        log_frame.setFrameStyle(QFrame.StyledPanel)
        log_frame.setMaximumHeight(200)
        
        log_layout = QVBoxLayout(log_frame)
        
        # Log header
        log_header = QLabel("Processing Log")
        log_header.setStyleSheet("""
            QLabel {
                font-weight: bold;
                padding: 5px;
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
            }
        """)
        log_layout.addWidget(log_header)
        
        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                font-family: Consolas, Monaco, monospace;
                font-size: 12px;
                background-color: #f8f9fa;
                border: none;
            }
        """)
        log_layout.addWidget(self.log_text)
        
        v_splitter.addWidget(log_frame)
        
        # Set splitter sizes (70% / 30%)
        v_splitter.setSizes([500, 200])
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        return panel
    
    def create_welcome_screen(self) -> QWidget:
        """Create the welcome screen"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        
        # Logo placeholder
        logo_label = QLabel("🌊")
        logo_label.setStyleSheet("font-size: 64px;")
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)
        
        # Title
        title = QLabel("Welcome to Hydro Suite")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                margin: 20px;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Description
        desc = QLabel(
            "A comprehensive QGIS toolbox for hydrological and stormwater analysis.\n\n"
            "Select a tool from the left panel to begin."
        )
        desc.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #555;
                margin: 20px;
            }
        """)
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Quick stats
        stats = QLabel(f"✓ {len(self.controller.tools_registry)} tools available")
        stats.setStyleSheet("color: #28a745; font-size: 12px;")
        stats.setAlignment(Qt.AlignCenter)
        layout.addWidget(stats)
        
        return widget
    
    def setup_menu(self):
        """Setup the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_project = QAction("&New Project", self)
        new_project.setShortcut("Ctrl+N")
        file_menu.addAction(new_project)
        
        open_project = QAction("&Open Project", self)
        open_project.setShortcut("Ctrl+O")
        file_menu.addAction(open_project)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        # Add tools by category
        categories = self.controller.get_tool_categories()
        for category, tool_ids in categories.items():
            category_menu = tools_menu.addMenu(category)
            for tool_id in tool_ids:
                tool_info = self.controller.tools_registry[tool_id]
                action = QAction(tool_info['config']['name'], self)
                action.setData(tool_id)
                action.triggered.connect(lambda checked, tid=tool_id: self.select_tool(tid))
                category_menu.addAction(action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        user_guide = QAction("&User Guide", self)
        user_guide.setShortcut("F1")
        help_menu.addAction(user_guide)
        
        help_menu.addSeparator()
        
        about = QAction("&About Hydro Suite", self)
        about.triggered.connect(self.show_about)
        help_menu.addAction(about)
    
    def setup_toolbar(self):
        """Setup the toolbar"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Run action
        run_action = QAction("▶ Run", self)
        run_action.setShortcut("F5")
        run_action.triggered.connect(self.run_current_tool)
        toolbar.addAction(run_action)
        
        toolbar.addSeparator()
        
        # Settings action
        settings_action = QAction("⚙ Settings", self)
        toolbar.addAction(settings_action)
        
        # Help action
        help_action = QAction("❓ Help", self)
        help_action.setShortcut("F1")
        toolbar.addAction(help_action)
    
    def setup_statusbar(self):
        """Setup the status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def on_tool_selected(self, current, previous):
        """Handle tool selection change"""
        if not current:
            return
        
        # Get tool ID from item data
        tool_id = current.data(Qt.UserRole)
        if not tool_id:
            return  # Category header
        
        self.select_tool(tool_id)
    
    def select_tool(self, tool_id: str):
        """Select and load a tool"""
        self.log(f"Loading {tool_id}...")
        
        # Load the tool
        tool = self.controller.load_tool(tool_id)
        if not tool:
            self.log(f"Failed to load {tool_id}", level="error")
            return
        
        # Create tool GUI if not already in stack
        if tool_id not in [self.tool_stack.widget(i).property("tool_id") 
                          for i in range(self.tool_stack.count())]:
            tool_widget = tool.create_gui(self.tool_stack)
            tool_widget.setProperty("tool_id", tool_id)
            self.tool_stack.addWidget(tool_widget)
        
        # Switch to tool widget
        for i in range(self.tool_stack.count()):
            if self.tool_stack.widget(i).property("tool_id") == tool_id:
                self.tool_stack.setCurrentIndex(i)
                break
        
        self.current_tool = tool
        self.status_bar.showMessage(f"Loaded: {tool.name}")
        self.log(f"Tool {tool.name} ready")
    
    def run_current_tool(self):
        """Run the currently selected tool"""
        if not self.current_tool:
            QMessageBox.warning(self, "No Tool Selected", 
                              "Please select a tool before running.")
            return
        
        # Validate inputs
        valid, message = self.current_tool.validate_inputs()
        if not valid:
            QMessageBox.warning(self, "Validation Error", message)
            return
        
        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Run tool with progress callback
        def progress_callback(value, message=""):
            self.progress_bar.setValue(value)
            if message:
                self.status_bar.showMessage(message)
        
        try:
            self.log(f"Running {self.current_tool.name}...")
            self.current_tool.run(progress_callback)
            self.log(f"{self.current_tool.name} completed successfully", level="success")
        except Exception as e:
            self.log(f"Error running {self.current_tool.name}: {str(e)}", level="error")
            QMessageBox.critical(self, "Execution Error", str(e))
        finally:
            self.progress_bar.setVisible(False)
            self.status_bar.showMessage("Ready")
    
    def show_tool_info(self):
        """Show information about the selected tool"""
        current = self.tool_list.currentItem()
        if not current:
            return
        
        tool_id = current.data(Qt.UserRole)
        if not tool_id:
            return
        
        tool_info = self.controller.tools_registry[tool_id]
        config = tool_info['config']
        
        info_text = f"""
<h3>{config['name']}</h3>
<p><b>Category:</b> {config['category']}</p>
<p><b>Description:</b> {config['description']}</p>
<p><b>Module:</b> {config['module']}</p>
"""
        
        QMessageBox.information(self, "Tool Information", info_text)
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
<h2>Hydro Suite</h2>
<p>Version 1.0 - 2025</p>
<p>A comprehensive QGIS toolbox for hydrological and stormwater analysis.</p>
<p><b>Features:</b></p>
<ul>
<li>Curve Number Calculator</li>
<li>Rational Method C Calculator</li>
<li>Time of Concentration (Multi-Method)</li>
<li>Trapezoidal Channel Designer</li>
</ul>
<p><b>Developed for:</b> QGIS 3.40+</p>
"""
        QMessageBox.about(self, "About Hydro Suite", about_text)
    
    def log(self, message: str, level: str = "info"):
        """Add message to log"""
        timestamp = QgsMessageLog.logMessage(message, "HydroSuite", 
                                            getattr(Qgis, level.capitalize(), Qgis.Info))
        
        # Color code by level
        colors = {
            "info": "#000000",
            "warning": "#ff9800",
            "error": "#f44336",
            "success": "#4caf50"
        }
        color = colors.get(level, "#000000")
        
        # Add to log widget
        self.log_text.append(f'<span style="color: {color}">[{level.upper()}] {message}</span>')
    
    def load_settings(self):
        """Load saved settings"""
        settings = QSettings("HydroSuite", "MainWindow")
        
        # Window geometry
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        # Window state
        state = settings.value("windowState")
        if state:
            self.restoreState(state)
    
    def save_settings(self):
        """Save current settings"""
        settings = QSettings("HydroSuite", "MainWindow")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.save_settings()
        event.accept()


def run_hydro_suite():
    """Main entry point for Hydro Suite"""
    # Create and show main window
    window = HydroSuiteMainWindow()
    window.show()
    return window


# For testing in QGIS Python Console
if __name__ == "__main__":
    window = run_hydro_suite()