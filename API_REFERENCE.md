# Hydro Suite API Reference

**Version**: 1.0.0  
**For Extension Developers**: Technical API documentation  
**Last Updated**: 2025

## Overview

This document provides detailed API reference for developers extending the Hydro Suite framework. It covers all public interfaces, shared components, and extension points.

## Core Interfaces

### HydroToolInterface

Base interface that all tools must implement.

```python
class HydroToolInterface(ABC):
    """Base interface for all Hydro Suite tools"""
    
    def __init__(self):
        self.name: str = "Unnamed Tool"
        self.description: str = "No description provided"
        self.category: str = "General"
        self.icon: str = "default_icon.png"
        self.version: str = "1.0"
        self.author: str = "Unknown"
        self.help_url: str = ""
        
        # Runtime properties
        self.is_running: bool = False
        self.current_progress: int = 0
        self.gui_widget: Optional[QWidget] = None
```

#### Required Methods

**`create_gui(parent_widget: QWidget) -> QWidget`**
- **Purpose**: Create and return the tool's GUI widget
- **Parameters**: 
  - `parent_widget`: Parent widget to attach the GUI to
- **Returns**: QWidget containing the tool's interface
- **Example**:
```python
def create_gui(self, parent_widget):
    scroll = QScrollArea(parent_widget)
    main_widget = QWidget()
    scroll.setWidget(main_widget)
    
    layout = QVBoxLayout(main_widget)
    layout.addWidget(QLabel(f"<h2>{self.name}</h2>"))
    
    # Add tool-specific components
    
    return scroll
```

**`validate_inputs() -> Tuple[bool, str]`**
- **Purpose**: Validate the current tool inputs
- **Returns**: Tuple of (is_valid: bool, error_message: str)
- **Example**:
```python
def validate_inputs(self):
    if not self.layer_selector.is_valid():
        return False, "Please select a valid layer"
    if not self.output_selector.is_valid():
        return False, "Please select an output directory"
    return True, "All inputs valid"
```

**`run(progress_callback: Optional[Callable[[int, str], None]]) -> bool`**
- **Purpose**: Execute the tool's main processing
- **Parameters**:
  - `progress_callback`: Optional function for progress updates (progress: int 0-100, message: str)
- **Returns**: True if successful, False otherwise
- **Example**:
```python
def run(self, progress_callback=None):
    if not progress_callback:
        progress_callback = lambda p, m: None
        
    try:
        progress_callback(0, "Starting...")
        
        # Validate inputs
        valid, message = self.validate_inputs()
        if not valid:
            raise ValueError(message)
            
        # Process data
        progress_callback(50, "Processing...")
        result = self.process_data()
        
        progress_callback(100, "Complete!")
        return True
        
    except Exception as e:
        progress_callback(0, f"Error: {str(e)}")
        raise
```

#### Optional Methods

**`get_help_content() -> str`**
- **Purpose**: Return HTML-formatted help content
- **Returns**: HTML string with tool documentation

**`get_settings() -> Dict[str, Any]`**
- **Purpose**: Get current tool settings/parameters
- **Returns**: Dictionary of current settings

**`set_settings(settings: Dict[str, Any]) -> None`**
- **Purpose**: Set tool settings/parameters
- **Parameters**: Dictionary of settings to apply

**`cleanup() -> None`**
- **Purpose**: Cleanup resources when tool is closed

### LayerSelectionMixin

Provides common layer selection functionality.

```python
class LayerSelectionMixin:
    """Mixin class providing common layer selection functionality"""
```

#### Static Methods

**`get_vector_layers(geometry_type: Optional[int] = None) -> List[QgsVectorLayer]`**
- **Purpose**: Get all vector layers from current project
- **Parameters**: 
  - `geometry_type`: Optional filter (0=point, 1=line, 2=polygon)
- **Returns**: List of QgsVectorLayer objects

**`get_layer_fields(layer: QgsVectorLayer) -> List[str]`**
- **Purpose**: Get field names from a layer
- **Parameters**: Vector layer
- **Returns**: List of field names

**`validate_field_exists(layer: QgsVectorLayer, field_name: str) -> bool`**
- **Purpose**: Check if field exists in layer
- **Parameters**: Layer and field name
- **Returns**: True if field exists

## Shared UI Components

### LayerFieldSelector

Widget for selecting a layer and field with validation.

```python
class LayerFieldSelector(QWidget):
    # Signals
    layer_changed = pyqtSignal(QgsVectorLayer)
    field_changed = pyqtSignal(str)
    selection_valid = pyqtSignal(bool)
```

#### Constructor

```python
LayerFieldSelector(
    title: str, 
    default_field: str = "", 
    geometry_type: Optional[int] = None, 
    parent=None
)
```

**Parameters**:
- `title`: Display title for the selector
- `default_field`: Default field name to select
- `geometry_type`: Filter by geometry type (0=point, 1=line, 2=polygon, None=any)
- `parent`: Parent widget

#### Methods

**`get_selected_layer() -> Optional[QgsVectorLayer]`**
- **Returns**: Currently selected layer or None

**`get_selected_field() -> Optional[str]`**
- **Returns**: Currently selected field name or None

**`is_valid() -> bool`**
- **Returns**: True if valid layer and field selected

**`set_enabled(enabled: bool)`**
- **Purpose**: Enable/disable the entire widget

#### Example Usage

```python
self.layer_selector = LayerFieldSelector(
    "Input Layer",
    default_field="Name",
    geometry_type=QgsWkbTypes.PolygonGeometry
)

# Connect validation
self.layer_selector.selection_valid.connect(
    lambda valid: self.update_validation("layer", valid)
)

# Get values
layer = self.layer_selector.get_selected_layer()
field = self.layer_selector.get_selected_field()
```

### FileSelector

Widget for selecting files with validation.

```python
class FileSelector(QWidget):
    file_selected = pyqtSignal(str)
```

#### Constructor

```python
FileSelector(
    title: str, 
    file_filter: str = "All files (*.*)", 
    default_path: str = "", 
    parent=None
)
```

#### Methods

**`get_selected_file() -> str`**
- **Returns**: Selected file path

**`is_valid() -> bool`**
- **Returns**: True if valid file selected

**`set_file(file_path: str)`**
- **Purpose**: Programmatically set selected file

### DirectorySelector

Widget for selecting output directories.

```python
class DirectorySelector(QWidget):
    directory_selected = pyqtSignal(str)
```

#### Constructor

```python
DirectorySelector(
    title: str = "Output Directory", 
    default_path: str = "", 
    parent=None
)
```

#### Methods

**`get_selected_directory() -> str`**
- **Returns**: Selected directory path

**`is_valid() -> bool`**
- **Returns**: True if valid directory selected

### ValidationPanel

Panel showing validation status for multiple inputs.

```python
class ValidationPanel(QWidget):
```

#### Methods

**`add_validation(name: str, description: str)`**
- **Purpose**: Add a validation item
- **Parameters**: 
  - `name`: Unique identifier
  - `description`: User-friendly description

**`set_validation_status(name: str, valid: bool, message: str = "")`**
- **Purpose**: Update validation status
- **Parameters**:
  - `name`: Validation item identifier
  - `valid`: Whether validation passed
  - `message`: Optional status message

**`is_all_valid() -> bool`**
- **Returns**: True if all validations pass

**`get_invalid_items() -> List[str]`**
- **Returns**: List of invalid item names

#### Example Usage

```python
self.validation_panel = ValidationPanel()

# Add validation items
self.validation_panel.add_validation("layer", "Input layer selection")
self.validation_panel.add_validation("output", "Output directory")

# Update status
self.validation_panel.set_validation_status("layer", True, "Layer valid")
self.validation_panel.set_validation_status("output", False, "No directory selected")

# Check overall status
if self.validation_panel.is_all_valid():
    self.run_btn.setEnabled(True)
```

### ProgressLogger

Widget for progress reporting and logging.

```python
class ProgressLogger(QWidget):
```

#### Methods

**`show_progress(visible: bool = True)`**
- **Purpose**: Show/hide progress bar

**`update_progress(value: int, message: str = "")`**
- **Purpose**: Update progress bar and log message
- **Parameters**:
  - `value`: Progress value (0-100)
  - `message`: Optional status message

**`log(message: str, level: str = "info")`**
- **Purpose**: Add message to log
- **Parameters**:
  - `message`: Log message
  - `level`: Message level ("info", "warning", "error", "success")

**`clear_log()`**
- **Purpose**: Clear the log display

## Helper Classes

### ProgressReporter

Helper class for structured progress reporting.

```python
class ProgressReporter:
    def __init__(self, callback: Optional[Callable] = None, total_steps: int = 100)
```

#### Methods

**`start(message: str = "Starting...")`**
- **Purpose**: Initialize progress reporting

**`step(message: str = "")`**
- **Purpose**: Increment progress by one step

**`update(progress: int, message: str = "")`**
- **Purpose**: Update progress to specific value

**`finish(message: str = "Complete")`**
- **Purpose**: Complete progress reporting

#### Example Usage

```python
def run(self, progress_callback):
    reporter = ProgressReporter(progress_callback, total_steps=5)
    
    reporter.start("Initializing...")
    
    # Step 1
    self.prepare_data()
    reporter.step("Data prepared")
    
    # Step 2
    self.process_data()
    reporter.step("Data processed")
    
    reporter.finish("Processing complete")
```

## Extension Patterns

### Adding New Shared Components

1. **Create component class** in `shared_widgets.py`
2. **Follow existing patterns** for signals and methods
3. **Add comprehensive docstrings**
4. **Update this API reference**

Example:
```python
class CustomWidget(QWidget):
    """Custom widget for specific functionality"""
    
    # Define signals
    value_changed = pyqtSignal(object)
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        # Add UI components
        
    def get_value(self) -> Any:
        """Get current value"""
        pass
        
    def set_value(self, value: Any):
        """Set current value"""
        pass
        
    def is_valid(self) -> bool:
        """Check if current value is valid"""
        pass
```

### Creating Custom Tool Categories

Tools are organized by category. To add a new category:

1. **Update tool configuration** in `hydro_suite_main.py`:
```python
"new_tool": {
    "name": "New Tool",
    "module": "new_tool_module",
    "class": "NewToolClass", 
    "icon": "new_tool.png",
    "category": "New Category",  # New category
    "description": "Tool description"
}
```

2. **Tools will automatically group** by category in the UI

### Processing Algorithm Integration

For tools that use QGIS processing algorithms:

```python
def process_with_algorithm(self, input_layer, parameters, feedback):
    """Standard pattern for QGIS processing integration"""
    
    # Prepare parameters
    params = {
        'INPUT': input_layer,
        'PARAMETER1': parameters.get('param1', default_value),
        'OUTPUT': 'memory:'
    }
    
    # Run algorithm with error handling
    try:
        result = processing.run("algorithm:name", params, feedback=feedback)
        return result['OUTPUT']
    except Exception as e:
        raise ValueError(f"Processing failed: {str(e)}")
```

### Error Handling Patterns

**Standard Error Handling**:
```python
def risky_operation(self):
    try:
        # Risky code here
        result = self.do_something()
        return result
    except SpecificException as e:
        # Handle specific error
        raise ValueError(f"Specific error: {str(e)}")
    except Exception as e:
        # Handle general error
        self.progress_logger.log(f"Unexpected error: {str(e)}", "error")
        raise
```

**Progress Callback Error Handling**:
```python
def run(self, progress_callback):
    try:
        progress_callback(0, "Starting...")
        # Processing steps
        progress_callback(100, "Complete!")
        return True
    except Exception as e:
        progress_callback(0, f"Error: {str(e)}")
        raise
```

## Tool Registration

### Main Controller Integration

To register a new tool in the framework:

1. **Add to tool configurations** in `discover_tools()`:
```python
tool_configs = {
    "tool_id": {
        "name": "Display Name",
        "module": "module_name", 
        "class": "ClassName",
        "icon": "icon.png",
        "category": "Category Name",
        "description": "Tool description"
    }
}
```

2. **Add import case** in `create_tool_wrapper()`:
```python
elif tool_id == "tool_id":
    from module_name import ClassName
    return ClassName()
```

3. **Tool will automatically appear** in the tool list

### Dynamic Tool Loading

Tools are loaded lazily when first accessed:

```python
def load_tool(self, tool_id: str) -> Optional[HydroToolInterface]:
    """Load a tool instance (lazy loading)"""
    
    # Check if already loaded
    if tool_info["loaded"] and tool_info["instance"]:
        return tool_info["instance"]
    
    # Load and cache the tool
    tool_instance = self.create_tool_wrapper(tool_id, config)
    tool_info["instance"] = tool_instance
    tool_info["loaded"] = True
    
    return tool_instance
```

## Testing Patterns

### Unit Testing Tools

```python
import unittest
from tool_module import ToolClass

class TestTool(unittest.TestCase):
    def setUp(self):
        self.tool = ToolClass()
        
    def test_initialization(self):
        self.assertEqual(self.tool.name, "Expected Name")
        self.assertEqual(self.tool.category, "Expected Category")
        
    def test_validation(self):
        # Test with invalid inputs
        valid, message = self.tool.validate_inputs()
        self.assertFalse(valid)
        
        # Setup valid inputs
        self.tool.setup_valid_inputs()
        valid, message = self.tool.validate_inputs()
        self.assertTrue(valid)
        
    def test_processing(self):
        # Test with mock data
        result = self.tool.run(lambda p, m: None)
        self.assertTrue(result)
```

### Integration Testing

```python
def test_tool_integration():
    """Test tool within framework"""
    from hydro_suite_main import HydroSuiteController
    
    controller = HydroSuiteController()
    tool = controller.load_tool("tool_id")
    
    assert tool is not None
    assert tool.name == "Expected Name"
    
    # Test GUI creation
    gui = tool.create_gui(None)
    assert gui is not None
```

## Performance Considerations

### Memory Management

- Use `'memory:'` outputs for temporary processing layers
- Clean up resources in `cleanup()` method
- Process large datasets in chunks

### Spatial Processing

- Create spatial indexes before intersection operations
- Use appropriate CRS for calculations
- Monitor processing algorithm performance

### UI Responsiveness

- Use progress callbacks for long operations
- Process data in background threads for complex operations
- Provide cancel capabilities where appropriate

## Migration Guide

### From Standalone Scripts

1. **Wrap existing logic** in HydroToolInterface
2. **Extract GUI components** to create_gui() method
3. **Implement validation** in validate_inputs() method
4. **Add progress reporting** to processing logic
5. **Register tool** in main controller

### Backward Compatibility

- Existing tool APIs remain stable
- New optional parameters added to extend functionality
- Deprecated features marked clearly with migration path

---

This API reference provides the foundation for extending the Hydro Suite framework. For specific implementation examples, refer to existing tools in the codebase.