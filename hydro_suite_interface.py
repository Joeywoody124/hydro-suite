"""
Hydro Suite - Tool Interface Base Class
Defines the contract for all tools in the Hydro Suite
Version 1.0 - 2025
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple, Callable, Any, Dict
from qgis.PyQt.QtWidgets import QWidget
from qgis.core import QgsVectorLayer, QgsProject


class HydroToolInterface(ABC):
    """Base interface for all Hydro Suite tools"""
    
    def __init__(self):
        """Initialize the tool interface"""
        self.name = "Unnamed Tool"
        self.description = "No description provided"
        self.category = "General"
        self.icon = "default_icon.png"
        self.version = "1.0"
        self.author = "Unknown"
        self.help_url = ""
        
        # Runtime properties
        self.is_running = False
        self.current_progress = 0
        self.gui_widget = None
        
    @abstractmethod
    def create_gui(self, parent_widget: QWidget) -> QWidget:
        """
        Create and return the tool's GUI widget
        
        Args:
            parent_widget: Parent widget to attach the GUI to
            
        Returns:
            QWidget: The tool's GUI widget
        """
        pass
    
    @abstractmethod
    def validate_inputs(self) -> Tuple[bool, str]:
        """
        Validate the current tool inputs
        
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    def run(self, progress_callback: Optional[Callable[[int, str], None]] = None) -> bool:
        """
        Execute the tool's main processing
        
        Args:
            progress_callback: Optional callback function for progress updates
                              Signature: callback(progress: int, message: str)
                              
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    def get_help_content(self) -> str:
        """
        Get help content for the tool
        
        Returns:
            str: HTML-formatted help content
        """
        return f"""
        <h2>{self.name}</h2>
        <p><b>Version:</b> {self.version}</p>
        <p><b>Author:</b> {self.author}</p>
        <p><b>Description:</b> {self.description}</p>
        <p>No additional help available.</p>
        """
    
    def get_settings(self) -> Dict[str, Any]:
        """
        Get current tool settings/parameters
        
        Returns:
            Dict[str, Any]: Dictionary of current settings
        """
        return {}
    
    def set_settings(self, settings: Dict[str, Any]) -> None:
        """
        Set tool settings/parameters
        
        Args:
            settings: Dictionary of settings to apply
        """
        pass
    
    def cleanup(self) -> None:
        """
        Cleanup resources when tool is closed
        """
        pass
    
    def update_progress(self, value: int, message: str = "", 
                       callback: Optional[Callable] = None) -> None:
        """
        Helper method to update progress
        
        Args:
            value: Progress value (0-100)
            message: Optional status message
            callback: Progress callback function
        """
        self.current_progress = value
        if callback:
            callback(value, message)


class LayerSelectionMixin:
    """Mixin class providing common layer selection functionality"""
    
    @staticmethod
    def get_vector_layers(geometry_type: Optional[int] = None) -> list:
        """
        Get all vector layers from the current project
        
        Args:
            geometry_type: Optional geometry type filter (0=point, 1=line, 2=polygon)
            
        Returns:
            list: List of QgsVectorLayer objects
        """
        layers = []
        for layer in QgsProject.instance().mapLayers().values():
            if isinstance(layer, QgsVectorLayer):
                if geometry_type is None or layer.geometryType() == geometry_type:
                    layers.append(layer)
        return layers
    
    @staticmethod
    def get_layer_fields(layer: QgsVectorLayer) -> list:
        """
        Get field names from a layer
        
        Args:
            layer: Vector layer
            
        Returns:
            list: List of field names
        """
        return [field.name() for field in layer.fields()]
    
    @staticmethod
    def validate_field_exists(layer: QgsVectorLayer, field_name: str) -> bool:
        """
        Check if a field exists in a layer
        
        Args:
            layer: Vector layer
            field_name: Field name to check
            
        Returns:
            bool: True if field exists
        """
        return field_name in [field.name() for field in layer.fields()]


class ProgressReporter:
    """Helper class for progress reporting"""
    
    def __init__(self, callback: Optional[Callable] = None, 
                 total_steps: int = 100):
        """
        Initialize progress reporter
        
        Args:
            callback: Progress callback function
            total_steps: Total number of steps
        """
        self.callback = callback
        self.total_steps = total_steps
        self.current_step = 0
        
    def start(self, message: str = "Starting..."):
        """Start progress reporting"""
        self.current_step = 0
        self.update(0, message)
    
    def step(self, message: str = ""):
        """Increment progress by one step"""
        self.current_step += 1
        progress = int((self.current_step / self.total_steps) * 100)
        self.update(progress, message)
    
    def update(self, progress: int, message: str = ""):
        """Update progress"""
        if self.callback:
            self.callback(progress, message)
    
    def finish(self, message: str = "Complete"):
        """Finish progress reporting"""
        self.update(100, message)


# Example implementation template for new tools
class ToolTemplate(HydroToolInterface, LayerSelectionMixin):
    """Template for creating new Hydro Suite tools"""
    
    def __init__(self):
        super().__init__()
        self.name = "Tool Template"
        self.description = "Template for new tool development"
        self.category = "Templates"
        self.version = "1.0"
        self.author = "Developer Name"
        
    def create_gui(self, parent_widget: QWidget) -> QWidget:
        """Create the tool GUI"""
        from qgis.PyQt.QtWidgets import QVBoxLayout, QLabel, QPushButton
        
        widget = QWidget(parent_widget)
        layout = QVBoxLayout(widget)
        
        # Add GUI elements
        layout.addWidget(QLabel(f"<h2>{self.name}</h2>"))
        layout.addWidget(QLabel(self.description))
        
        # Add tool-specific controls here
        
        # Run button
        run_btn = QPushButton("Run Tool")
        run_btn.clicked.connect(lambda: self.run())
        layout.addWidget(run_btn)
        
        layout.addStretch()
        
        self.gui_widget = widget
        return widget
    
    def validate_inputs(self) -> Tuple[bool, str]:
        """Validate inputs"""
        # Add validation logic here
        return True, ""
    
    def run(self, progress_callback: Optional[Callable[[int, str], None]] = None) -> bool:
        """Execute the tool"""
        reporter = ProgressReporter(progress_callback, total_steps=5)
        
        try:
            reporter.start("Initializing...")
            
            # Step 1
            reporter.step("Processing step 1...")
            # Add processing logic here
            
            # Step 2
            reporter.step("Processing step 2...")
            # Add processing logic here
            
            # Complete
            reporter.finish("Tool completed successfully")
            return True
            
        except Exception as e:
            reporter.update(0, f"Error: {str(e)}")
            return False


# Wrapper adapters for existing tools
class CNCalculatorAdapter(HydroToolInterface, LayerSelectionMixin):
    """Adapter for the Curve Number Calculator"""
    
    def __init__(self):
        super().__init__()
        self.name = "Curve Number Calculator"
        self.description = "Calculate area-weighted composite curve numbers for hydrological modeling"
        self.category = "Runoff Analysis"
        self.version = "2.2"
        self.author = "Original Author"
        self.dialog = None
        
    def create_gui(self, parent_widget: QWidget) -> QWidget:
        """Create GUI by wrapping the existing dialog"""
        from qgis.PyQt.QtWidgets import QVBoxLayout, QPushButton, QLabel
        
        widget = QWidget(parent_widget)
        layout = QVBoxLayout(widget)
        
        # Description
        desc = QLabel(
            "<h2>Curve Number Calculator</h2>"
            "<p>This tool calculates area-weighted composite curve numbers "
            "for hydrological modeling applications.</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Multi-layer intersection analysis</li>"
            "<li>Split HSG handling (A/D, B/D, C/D)</li>"
            "<li>Flexible lookup table support</li>"
            "<li>SWMM/HEC-HMS compatible outputs</li>"
            "</ul>"
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Launch button
        launch_btn = QPushButton("Open CN Calculator")
        launch_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                padding: 15px;
                background-color: #007bff;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        launch_btn.clicked.connect(self.launch_original_dialog)
        layout.addWidget(launch_btn)
        
        layout.addStretch()
        
        self.gui_widget = widget
        return widget
    
    def launch_original_dialog(self):
        """Launch the original CN calculator dialog"""
        try:
            # This would import and launch the actual CN calculator
            # For now, we'll show a placeholder message
            from qgis.PyQt.QtWidgets import QMessageBox
            QMessageBox.information(
                self.gui_widget,
                "CN Calculator",
                "In production, this would launch the actual CN Calculator dialog.\n\n"
                "The tool would be imported from:\n"
                "Components/CN/composite_cn_calculator.py"
            )
        except Exception as e:
            from qgis.PyQt.QtWidgets import QMessageBox
            QMessageBox.critical(self.gui_widget, "Error", f"Failed to launch CN Calculator: {str(e)}")
    
    def validate_inputs(self) -> Tuple[bool, str]:
        """Validation is handled by the original dialog"""
        return True, ""
    
    def run(self, progress_callback: Optional[Callable[[int, str], None]] = None) -> bool:
        """Execution is handled by the original dialog"""
        # The actual tool handles its own execution
        return True


class RationalCAdapter(HydroToolInterface, LayerSelectionMixin):
    """Adapter for the Rational C Calculator"""
    
    def __init__(self):
        super().__init__()
        self.name = "Rational C Calculator"
        self.description = "Calculate composite runoff coefficients for rational method analysis"
        self.category = "Runoff Analysis"
        self.version = "1.0"
        self.author = "Original Author"
        
    def create_gui(self, parent_widget: QWidget) -> QWidget:
        """Create GUI by wrapping the existing dialog"""
        from qgis.PyQt.QtWidgets import QVBoxLayout, QPushButton, QLabel
        
        widget = QWidget(parent_widget)
        layout = QVBoxLayout(widget)
        
        # Description
        desc = QLabel(
            "<h2>Rational Method C Calculator</h2>"
            "<p>This tool calculates area-weighted composite runoff coefficients "
            "for rational method analysis.</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Slope-based C value determination</li>"
            "<li>Project-wide slope category selection</li>"
            "<li>Handles unrecognized soil groups</li>"
            "<li>Professional reporting formats</li>"
            "</ul>"
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Launch button
        launch_btn = QPushButton("Open C Value Calculator")
        launch_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                padding: 15px;
                background-color: #28a745;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        launch_btn.clicked.connect(self.launch_original_dialog)
        layout.addWidget(launch_btn)
        
        layout.addStretch()
        
        self.gui_widget = widget
        return widget
    
    def launch_original_dialog(self):
        """Launch the original C calculator dialog"""
        try:
            from qgis.PyQt.QtWidgets import QMessageBox
            QMessageBox.information(
                self.gui_widget,
                "C Value Calculator",
                "In production, this would launch the actual Rational C Calculator dialog.\n\n"
                "The tool would be imported from:\n"
                "Components/Rational_C/composite_C_calculator.py"
            )
        except Exception as e:
            from qgis.PyQt.QtWidgets import QMessageBox
            QMessageBox.critical(self.gui_widget, "Error", f"Failed to launch C Calculator: {str(e)}")
    
    def validate_inputs(self) -> Tuple[bool, str]:
        """Validation is handled by the original dialog"""
        return True, ""
    
    def run(self, progress_callback: Optional[Callable[[int, str], None]] = None) -> bool:
        """Execution is handled by the original dialog"""
        return True