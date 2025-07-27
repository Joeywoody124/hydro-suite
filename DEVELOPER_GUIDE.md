# Hydro Suite Developer Guide

**Version**: 1.0.0  
**For Developers**: Technical implementation guide  
**Last Updated**: 2025

## Overview

This guide provides technical details for developers working on the Hydro Suite project. It covers architecture patterns, coding standards, and step-by-step instructions for extending the framework.

## Quick Development Setup

### Prerequisites
- QGIS 3.40+ with Python 3.9+
- Access to the project directory
- Basic understanding of PyQt5 and QGIS APIs

### Development Environment
1. **Launch QGIS** and open Python Console
2. **Set working directory** to project folder
3. **Use the launcher** for rapid testing:
```python
exec(open(r'E:\CLAUDE_Workspace\Claude\Report_Files\Codebase\Hydro_Suite\Hydro_Suite_Data\launch_hydro_suite.py').read())
```

## Architecture Deep Dive

### Core Components

#### 1. Main Controller (`hydro_suite_main.py`)
- **Purpose**: Application lifecycle management and tool orchestration
- **Key Classes**: `HydroSuiteController`, `HydroSuiteMainWindow`
- **Responsibilities**:
  - Tool discovery and registration
  - GUI window management
  - Tool loading and instantiation
  - Event handling and coordination

#### 2. Base Interface (`hydro_suite_interface.py`)
- **Purpose**: Contracts and base functionality for all tools
- **Key Classes**: `HydroToolInterface`, `LayerSelectionMixin`
- **Responsibilities**:
  - Define tool interface contract
  - Provide common layer operations
  - Standardize validation patterns

#### 3. Shared Widgets (`shared_widgets.py`)
- **Purpose**: Reusable UI components
- **Key Classes**: `LayerFieldSelector`, `ValidationPanel`, `ProgressLogger`
- **Responsibilities**:
  - Consistent UI patterns
  - Input validation
  - Progress reporting

### Tool Implementation Pattern

Every tool follows this structure:
```python
class ToolName(HydroToolInterface, LayerSelectionMixin):
    def __init__(self):
        # Initialize tool properties
        super().__init__()
        self.name = "Tool Display Name"
        self.description = "Tool description"
        self.category = "Tool Category"
        
        # Tool-specific properties
        self.validation_panel = None
        self.progress_logger = None
        
    def create_gui(self, parent_widget):
        # Create and return tool GUI
        pass
        
    def validate_inputs(self):
        # Validate all inputs
        return is_valid, error_message
        
    def run(self, progress_callback):
        # Execute tool processing
        pass
```

## Adding a New Tool - Step by Step

### Step 1: Create Tool File
Create `new_tool.py` in the project directory:

```python
"""
New Tool for Hydro Suite
Description of what the tool does
Version 1.0 - 2025
"""

import os
from typing import Optional, Tuple, Callable

from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea
)
from qgis.core import QgsWkbTypes

from hydro_suite_interface import HydroToolInterface, LayerSelectionMixin
from shared_widgets import (
    LayerFieldSelector, ValidationPanel, ProgressLogger
)

class NewTool(HydroToolInterface, LayerSelectionMixin):
    def __init__(self):
        super().__init__()
        self.name = "New Tool Name"
        self.description = "What this tool does"
        self.category = "Tool Category"
        self.version = "1.0"
        
        # GUI components
        self.validation_panel = None
        self.progress_logger = None
        
    def create_gui(self, parent_widget: QWidget) -> QWidget:
        # Create scroll area
        scroll = QScrollArea(parent_widget)
        scroll.setWidgetResizable(True)
        
        main_widget = QWidget()
        scroll.setWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Add title
        layout.addWidget(QLabel(f"<h2>{self.name}</h2>"))
        
        # Add validation panel
        self.validation_panel = ValidationPanel()
        layout.addWidget(self.validation_panel)
        
        # Add tool-specific components here
        # Example: Layer selector
        self.layer_selector = LayerFieldSelector(
            "Input Layer",
            default_field="field_name",
            geometry_type=QgsWkbTypes.PolygonGeometry
        )
        layout.addWidget(self.layer_selector)
        
        # Add progress logger
        self.progress_logger = ProgressLogger()
        layout.addWidget(self.progress_logger)
        
        # Add run button
        run_btn = QPushButton("Run Tool")
        run_btn.clicked.connect(self.run_tool)
        layout.addWidget(run_btn)
        
        # Setup validation
        self.setup_validation()
        
        self.gui_widget = scroll
        return scroll
        
    def setup_validation(self):
        """Setup validation monitoring"""
        self.validation_panel.add_validation("layer", "Input layer and field")
        
        self.layer_selector.selection_valid.connect(
            lambda valid: self.validation_panel.set_validation_status("layer", valid)
        )
        
    def validate_inputs(self) -> Tuple[bool, str]:
        """Validate all inputs"""
        if not self.layer_selector.is_valid():
            return False, "Please select a valid layer and field"
        return True, "All inputs valid"
        
    def run_tool(self):
        """Run button handler"""
        try:
            self.run(lambda p, m: self.progress_logger.update_progress(p, m))
        except Exception as e:
            self.progress_logger.log(f"Error: {str(e)}", "error")
            
    def run(self, progress_callback: Optional[Callable[[int, str], None]] = None) -> bool:
        """Execute tool processing"""
        if not progress_callback:
            progress_callback = lambda p, m: None
            
        try:
            progress_callback(0, "Starting...")
            
            # Validate inputs
            valid, message = self.validate_inputs()
            if not valid:
                raise ValueError(message)
                
            # Get inputs
            layer = self.layer_selector.get_selected_layer()
            field = self.layer_selector.get_selected_field()
            
            # Process (add your logic here)
            progress_callback(50, "Processing...")
            
            # Complete
            progress_callback(100, "Complete!")
            return True
            
        except Exception as e:
            progress_callback(0, f"Error: {str(e)}")
            raise
```

### Step 2: Register in Main Controller
Edit `hydro_suite_main.py` in the `create_tool_wrapper()` method:

```python
def create_tool_wrapper(self, tool_id: str, config: Dict[str, Any]) -> HydroToolInterface:
    # Import actual tools
    if tool_id == "cn_calculator":
        from cn_calculator_tool import CNCalculatorTool
        return CNCalculatorTool()
    elif tool_id == "c_calculator":
        from rational_c_tool import RationalCTool
        return RationalCTool()
    elif tool_id == "new_tool":  # Add this
        from new_tool import NewTool
        return NewTool()
```

Also add to the `discover_tools()` method:
```python
tool_configs = {
    # ... existing tools ...
    "new_tool": {
        "name": "New Tool Name",
        "module": "new_tool",
        "class": "NewTool",
        "icon": "new_tool_icon.png",
        "category": "Tool Category",
        "description": "What this tool does"
    }
}
```

### Step 3: Test Integration
1. Launch the framework
2. Look for your tool in the tool list
3. Select it and verify the GUI loads
4. Test validation and error handling

## UI Component Reference

### LayerFieldSelector
```python
selector = LayerFieldSelector(
    title="Layer Display Name",
    default_field="expected_field_name",
    geometry_type=QgsWkbTypes.PolygonGeometry  # or None, Point, Line
)

# Connect validation
selector.selection_valid.connect(callback_function)

# Get values
layer = selector.get_selected_layer()
field = selector.get_selected_field()
is_valid = selector.is_valid()
```

### FileSelector
```python
selector = FileSelector(
    title="File Type",
    file_filter="CSV files (*.csv);;Excel files (*.xlsx)",
    default_path="/default/directory"
)

# Connect signals
selector.file_selected.connect(callback_function)

# Get values
file_path = selector.get_selected_file()
is_valid = selector.is_valid()
```

### ValidationPanel
```python
panel = ValidationPanel()

# Add validation items
panel.add_validation("item_id", "Item description")

# Update status
panel.set_validation_status("item_id", is_valid, "Optional message")

# Check overall status
all_valid = panel.is_all_valid()
invalid_items = panel.get_invalid_items()
```

### ProgressLogger
```python
logger = ProgressLogger()

# Show/hide progress bar
logger.show_progress(True)

# Update progress
logger.update_progress(50, "Halfway done...")

# Log messages
logger.log("Info message", "info")
logger.log("Warning message", "warning") 
logger.log("Error message", "error")
logger.log("Success message", "success")
```

## Advanced Patterns

### Processing with QGIS Algorithms
```python
def process_layers(self, layer1, layer2, feedback):
    """Example of using QGIS processing algorithms"""
    # Reproject if needed
    if layer1.crs() != self.target_crs:
        params = {
            'INPUT': layer1,
            'TARGET_CRS': self.target_crs,
            'OUTPUT': 'memory:'
        }
        result = processing.run("native:reprojectlayer", params, feedback=feedback)
        layer1 = result['OUTPUT']
    
    # Intersection
    params = {
        'INPUT': layer1,
        'OVERLAY': layer2,
        'OUTPUT': 'memory:'
    }
    result = processing.run("native:intersection", params, feedback=feedback)
    return result['OUTPUT']
```

### Error Handling Best Practices
```python
def run(self, progress_callback):
    try:
        progress_callback(0, "Starting...")
        
        # Validate first
        valid, message = self.validate_inputs()
        if not valid:
            raise ValueError(message)
            
        # Process with try/catch for specific errors
        try:
            result = self.do_processing()
        except processing.ProcessingException as e:
            raise ValueError(f"Processing failed: {str(e)}")
        except FileNotFoundError as e:
            raise ValueError(f"File not found: {str(e)}")
            
        progress_callback(100, "Complete!")
        return True
        
    except Exception as e:
        # Log full traceback for debugging
        import traceback
        self.progress_logger.log(traceback.format_exc(), "error")
        
        # Re-raise with user-friendly message
        raise ValueError(f"Tool execution failed: {str(e)}")
```

### Output File Management
```python
def create_outputs(self, data, output_dir):
    """Standard output creation pattern"""
    from qgis.PyQt.QtCore import QVariant
    
    # Create output layer
    output_layer = QgsVectorLayer(
        f"Polygon?crs={self.target_crs.authid()}", 
        "output_name", 
        "memory"
    )
    
    # Add fields
    provider = output_layer.dataProvider()
    provider.addAttributes([
        QgsField("result_field", QVariant.Double, "double", 10, 2)
    ])
    output_layer.updateFields()
    
    # Add features (your logic here)
    
    # Save shapefile
    shp_path = os.path.join(output_dir, "output.shp")
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "ESRI Shapefile"
    
    error = QgsVectorFileWriter.writeAsVectorFormatV3(
        output_layer, shp_path, 
        QgsProject.instance().transformContext(), 
        options
    )
    
    if error[0] != QgsVectorFileWriter.NoError:
        raise ValueError(f"Error saving shapefile: {error[1]}")
        
    return shp_path
```

## Testing and Debugging

### Local Testing
```python
# Test tool in isolation
tool = NewTool()
widget = tool.create_gui(None)

# Test validation
valid, message = tool.validate_inputs()
print(f"Validation: {valid}, {message}")

# Test with mock data
try:
    result = tool.run(lambda p, m: print(f"Progress: {p}% - {m}"))
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {e}")
```

### Debug Logging
```python
import logging

# Setup debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Use in your tool
logger.debug("Debug information")
logger.info("Process step completed")
logger.warning("Potential issue detected")
logger.error("Error occurred")
```

### Common Issues and Solutions

#### 1. Import Errors
```python
# Problem: Module not found
# Solution: Check Python path
import sys
print(sys.path)

# Add project directory if needed
project_dir = r"E:\CLAUDE_Workspace\Claude\Report_Files\Codebase\Hydro_Suite\Hydro_Suite_Data"
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)
```

#### 2. Layer Loading Issues
```python
# Problem: Layer not loading
# Solution: Validate layer thoroughly
def validate_layer(self, layer_path):
    layer = QgsVectorLayer(layer_path, "test", "ogr")
    if not layer.isValid():
        raise ValueError(f"Cannot load layer: {layer_path}")
    if layer.featureCount() == 0:
        raise ValueError(f"Layer is empty: {layer_path}")
    return layer
```

#### 3. Processing Errors
```python
# Problem: QGIS processing fails
# Solution: Check parameters and feedback
def safe_processing(self, algorithm, params):
    from qgis.core import QgsProcessingFeedback
    
    feedback = QgsProcessingFeedback()
    
    try:
        result = processing.run(algorithm, params, feedback=feedback)
        return result
    except Exception as e:
        # Check what went wrong
        print(f"Algorithm: {algorithm}")
        print(f"Parameters: {params}")
        print(f"Error: {e}")
        raise
```

## Version Control Guidelines

### Git Workflow
1. **Create feature branch**: `git checkout -b feature/new-tool`
2. **Make changes**: Implement your tool
3. **Test thoroughly**: Verify no regressions
4. **Commit with clear message**: `git commit -m "Add new tool for [purpose]"`
5. **Update documentation**: Modify this guide if needed
6. **Merge to develop**: Create pull request

### Commit Message Format
```
type(scope): brief description

Longer description if needed

- Bullet points for specific changes
- Breaking changes noted clearly
```

Examples:
- `feat(tools): add watershed delineation tool`
- `fix(ui): resolve layer selection validation issue`
- `docs(guide): update developer guide with new patterns`

### File Organization
- Keep tool files focused and single-purpose
- Use consistent naming conventions
- Document any new patterns or approaches
- Update this guide when adding new capabilities

## Performance Considerations

### Large Dataset Handling
```python
def process_large_dataset(self, layer, progress_callback):
    """Handle large datasets efficiently"""
    total_features = layer.featureCount()
    batch_size = 1000
    
    for i in range(0, total_features, batch_size):
        # Process in batches
        features = layer.getFeatures(QgsFeatureRequest().setLimit(batch_size).setStartId(i))
        
        # Process batch
        batch_results = []
        for feature in features:
            # Process individual feature
            result = self.process_feature(feature)
            batch_results.append(result)
            
        # Update progress
        progress = int((i + batch_size) / total_features * 100)
        progress_callback(progress, f"Processed {i + batch_size}/{total_features} features")
        
        # Allow cancellation
        if self.should_cancel:
            break
```

### Memory Management
- Use `'memory:'` outputs for intermediate processing
- Clean up temporary layers when done
- Process in chunks for very large datasets
- Monitor memory usage during development

## Extension Points

The framework provides several extension points:

1. **New Tool Types**: Inherit from `HydroToolInterface`
2. **Custom UI Components**: Add to `shared_widgets.py`
3. **Processing Algorithms**: Create reusable processing functions
4. **Output Formats**: Extend output creation methods
5. **Validation Rules**: Add custom validation patterns

## Best Practices Summary

1. **Follow existing patterns**: Use established UI and processing patterns
2. **Validate thoroughly**: Check all inputs before processing
3. **Provide feedback**: Use progress reporting and clear error messages
4. **Handle errors gracefully**: Catch and report errors appropriately
5. **Test incrementally**: Test each component as you build
6. **Document changes**: Update guides and API documentation
7. **Use version control**: Commit frequently with clear messages

---

This guide should provide everything needed to understand, modify, and extend the Hydro Suite framework. For questions or clarifications, refer to the existing tool implementations as examples.