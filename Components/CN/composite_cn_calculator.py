"""
Composite Curve Number Calculator - ENHANCED VERSION
Version 2.2 — 2025‑06‑05
Computes area‑weighted composite Curve Numbers in QGIS.

Enhanced Features:
- Select from loaded QGIS layers OR browse for files
- Improved user interface with layer selection options
- Support for both file browsing and project layer selection
- Enhanced lookup table handling
- Split HSG handling (A/D, B/D, C/D defaults to more restrictive group)

Required fields
---------------
Subbasins : Name (or any unique identifier field)
Land‑use  : LU (land use code field)
Soils     : hydgrpdcd (hydrologic soil group field)

Lookup table columns (case-insensitive)
---------------------------------------
landuse, a, b, c, d
OR
Class/Value, Description, A, B, C, D (NLCD format)
"""

import csv
import os
import traceback
from pathlib import Path

import pandas as pd
from qgis.PyQt.QtCore import Qt, QVariant
from qgis.PyQt.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QVBoxLayout,
    QComboBox,
    QGroupBox,
    QRadioButton,
    QButtonGroup,
    QFrame,
)
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsProcessingFeedback,
    QgsProject,
    QgsVectorFileWriter,
    QgsVectorLayer,
    QgsField,
    QgsFeature,
    QgsGeometry,
    Qgis,
    QgsMessageLog,
)
from qgis import processing


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def log_message(message: str, level=Qgis.Info):
    """Log message to QGIS message panel."""
    QgsMessageLog.logMessage(message, "Composite CN Calculator", level)


def parse_soil_group(soil_group_raw: str) -> str:
    """Parse soil group, handling split HSGs by defaulting to the second (more restrictive) group.
    
    Examples:
    - 'A' -> 'a'
    - 'B/D' -> 'd' 
    - 'A/D' -> 'd'
    - 'C/D' -> 'd'
    """
    soil_group = str(soil_group_raw).strip().upper()
    
    # Handle split soil groups (e.g., 'A/D', 'B/D', 'C/D')
    if '/' in soil_group:
        # Split and take the second (more restrictive) group
        parts = soil_group.split('/')
        if len(parts) >= 2:
            soil_group = parts[1].strip()
            log_message(f"Split HSG detected: '{soil_group_raw}' -> using '{soil_group}'")
    
    # Validate and return lowercase
    if soil_group in ['A', 'B', 'C', 'D']:
        return soil_group.lower()
    else:
        log_message(f"Warning: Invalid soil group '{soil_group_raw}', using 'd' as default", Qgis.Warning)
        return 'd'  # Default to most restrictive


def acres_from_sqft(area_sqft: float) -> float:
    """Convert square feet to acres."""
    return area_sqft / 43_560.0


def get_vector_layers_from_project():
    """Get all vector layers currently loaded in QGIS project."""
    project = QgsProject.instance()
    vector_layers = []
    
    for layer_id, layer in project.mapLayers().items():
        if isinstance(layer, QgsVectorLayer) and layer.geometryType() == 2:  # Polygon layers only
            vector_layers.append(layer)
    
    return vector_layers


def validate_layer_fields(layer: QgsVectorLayer, required_field: str, layer_name: str) -> bool:
    """Validate that a layer has the required field."""
    field_names = [field.name() for field in layer.fields()]
    if required_field not in field_names:
        raise ValueError(f"{layer_name} layer missing required field '{required_field}'. "
                        f"Available fields: {', '.join(field_names)}")
    return True


def read_lookup(path: str) -> pd.DataFrame:
    """Read CN lookup CSV or Excel into a DataFrame and validate."""
    ext = Path(path).suffix.lower()
    if ext in (".xls", ".xlsx", ".xlsm"):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)
    
    # Clean column names
    df.columns = [c.strip().lower() for c in df.columns]
    
    # Check for different lookup table formats
    # Format 1: landuse, a, b, c, d
    format1_cols = {"landuse", "a", "b", "c", "d"}
    # Format 2: class/value, description, a, b, c, d (NLCD style)
    format2_cols = {"class/value", "a", "b", "c", "d"}
    
    if format1_cols.issubset(set(df.columns)):
        log_message("Using lookup format: landuse, a, b, c, d")
        return df
    elif format2_cols.issubset(set(df.columns)):
        log_message("Using lookup format: class/value, description, a, b, c, d")
        # Rename class/value to landuse for consistency
        df = df.rename(columns={"class/value": "landuse"})
        return df
    else:
        missing = format1_cols - set(df.columns)
        raise ValueError(f"Lookup table format not recognized. Expected columns: "
                        f"{', '.join(format1_cols)} OR {', '.join(format2_cols)}. "
                        f"Found columns: {', '.join(df.columns)}")


def load_layer(path: str, name: str) -> QgsVectorLayer:
    """Load a vector layer with validation."""
    lyr = QgsVectorLayer(path, name, "ogr")
    if not lyr.isValid():
        raise ValueError(f"Cannot load layer: {path}")
    if lyr.featureCount() == 0:
        raise ValueError(f"Layer is empty: {path}")
    return lyr


def reproject_layer(layer: QgsVectorLayer, target_crs: QgsCoordinateReferenceSystem, 
                   feedback) -> QgsVectorLayer:
    """Reproject layer to target CRS if needed."""
    if layer.crs() == target_crs:
        return layer
    
    log_message(f"Reprojecting layer from {layer.crs().authid()} to {target_crs.authid()}")
    params = {
        "INPUT": layer,
        "TARGET_CRS": target_crs,
        "OUTPUT": "memory:",
    }
    result = processing.run("native:reprojectlayer", params, feedback=feedback)
    return result["OUTPUT"]


def intersect_layers(layer1: QgsVectorLayer, layer2: QgsVectorLayer, 
                    feedback) -> QgsVectorLayer:
    """Perform intersection with proper error handling."""
    log_message(f"Intersecting {layer1.name()} with {layer2.name()}")
    params = {
        "INPUT": layer1,
        "OVERLAY": layer2,
        "INPUT_FIELDS": [],
        "OVERLAY_FIELDS": [],
        "OVERLAY_FIELDS_PREFIX": "",
        "OUTPUT": "memory:",
    }
    result = processing.run("native:intersection", params, feedback=feedback)
    intersection = result["OUTPUT"]
    
    if intersection.featureCount() == 0:
        raise ValueError(f"Intersection resulted in no features. Check layer overlap and geometry validity.")
    
    return intersection


# ---------------------------------------------------------------------------
# Layer Selection Widget
# ---------------------------------------------------------------------------

class LayerSelectionWidget(QFrame):
    """Widget for selecting either a loaded layer or browsing for a file."""
    
    def __init__(self, layer_type: str, default_field: str, parent=None):
        super().__init__(parent)
        self.layer_type = layer_type
        self.default_field = default_field
        self.selected_layer = None
        
        self.setup_ui()
        self.update_layer_combo()
        
    def setup_ui(self):
        """Setup the UI for layer selection."""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel(f"{self.layer_type.title()} Layer Selection")
        title.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(title)
        
        # Radio buttons for selection method
        self.button_group = QButtonGroup()
        self.radio_project = QRadioButton("Use layer from current project")
        self.radio_file = QRadioButton("Browse for file")
        self.radio_project.setChecked(True)
        
        self.button_group.addButton(self.radio_project, 1)
        self.button_group.addButton(self.radio_file, 2)
        
        layout.addWidget(self.radio_project)
        layout.addWidget(self.radio_file)
        
        # Layer selection combo
        self.combo_layers = QComboBox()
        self.combo_layers.setMinimumWidth(300)
        layout.addWidget(self.combo_layers)
        
        # File selection
        file_layout = QHBoxLayout()
        self.lbl_file = QLabel("No file selected")
        self.btn_browse = QPushButton("Browse...")
        self.btn_browse.setEnabled(False)
        
        file_layout.addWidget(self.lbl_file, 2)
        file_layout.addWidget(self.btn_browse, 1)
        layout.addLayout(file_layout)
        
        # Field selection
        field_layout = QHBoxLayout()
        field_layout.addWidget(QLabel("Field:"))
        self.combo_fields = QComboBox()
        field_layout.addWidget(self.combo_fields)
        layout.addLayout(field_layout)
        
        self.setLayout(layout)
        
        # Connect signals
        self.radio_project.toggled.connect(self.on_selection_method_changed)
        self.radio_file.toggled.connect(self.on_selection_method_changed)
        self.combo_layers.currentTextChanged.connect(self.on_layer_changed)
        self.btn_browse.clicked.connect(self.browse_for_file)
        
    def update_layer_combo(self):
        """Update the layer combo with currently loaded layers."""
        self.combo_layers.clear()
        self.combo_layers.addItem("-- Select a layer --")
        
        vector_layers = get_vector_layers_from_project()
        for layer in vector_layers:
            self.combo_layers.addItem(layer.name(), layer)
            
        if len(vector_layers) == 0:
            self.combo_layers.addItem("No vector layers loaded")
            self.radio_project.setEnabled(False)
            self.radio_file.setChecked(True)
        else:
            self.radio_project.setEnabled(True)
    
    def on_selection_method_changed(self):
        """Handle selection method change."""
        use_project = self.radio_project.isChecked()
        
        self.combo_layers.setEnabled(use_project)
        self.btn_browse.setEnabled(not use_project)
        
        if use_project:
            self.lbl_file.setText("Using project layer")
            self.on_layer_changed()
        else:
            self.lbl_file.setText("No file selected")
            self.combo_fields.clear()
            self.selected_layer = None
    
    def on_layer_changed(self):
        """Handle layer selection change."""
        if not self.radio_project.isChecked():
            return
            
        current_data = self.combo_layers.currentData()
        if isinstance(current_data, QgsVectorLayer):
            self.selected_layer = current_data
            self.populate_field_combo(current_data)
        else:
            self.selected_layer = None
            self.combo_fields.clear()
    
    def browse_for_file(self):
        """Browse for a vector file."""
        path, _ = QFileDialog.getOpenFileName(
            self, f"Select {self.layer_type} layer", "", 
            "Vector files (*.shp *.gpkg *.geojson);;Shapefiles (*.shp);;GeoPackage (*.gpkg)"
        )
        if path:
            try:
                layer = load_layer(path, self.layer_type)
                self.selected_layer = layer
                self.lbl_file.setText(Path(path).name)
                self.populate_field_combo(layer)
                log_message(f"Loaded {self.layer_type} layer from file: {Path(path).name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading {self.layer_type} layer: {str(e)}")
                self.lbl_file.setText("Error loading file")
                self.selected_layer = None
    
    def populate_field_combo(self, layer: QgsVectorLayer):
        """Populate field combo with layer fields."""
        self.combo_fields.clear()
        if layer and layer.isValid():
            field_names = [field.name() for field in layer.fields()]
            self.combo_fields.addItems(field_names)
            
            # Set default field if exists
            if self.default_field in field_names:
                self.combo_fields.setCurrentText(self.default_field)
    
    def get_selected_layer(self):
        """Get the currently selected layer."""
        return self.selected_layer
    
    def get_selected_field(self):
        """Get the currently selected field."""
        return self.combo_fields.currentText()
    
    def is_valid_selection(self):
        """Check if current selection is valid."""
        return (self.selected_layer is not None and 
                self.selected_layer.isValid() and 
                self.get_selected_field())


# ---------------------------------------------------------------------------
# Main dialog
# ---------------------------------------------------------------------------

class CompositeCNDialog(QDialog):
    """GUI for composite CN calculation with enhanced layer selection."""

    CRS_TARGET = QgsCoordinateReferenceSystem("EPSG:3361")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Composite Curve Number Calculator v2.2")
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)

        # Data members
        self.lookup_path = None
        self.out_dir = None

        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """Setup the user interface."""
        main_layout = QVBoxLayout()

        # Input layers group
        input_group = QGroupBox("Input Layers")
        input_layout = QVBoxLayout()

        # Layer selection widgets
        self.sub_widget = LayerSelectionWidget("subbasin", "Name")
        self.lu_widget = LayerSelectionWidget("land-use", "LU")
        self.soil_widget = LayerSelectionWidget("soils", "hydgrpdcd")

        input_layout.addWidget(self.sub_widget)
        input_layout.addWidget(self.create_separator())
        input_layout.addWidget(self.lu_widget)
        input_layout.addWidget(self.create_separator())
        input_layout.addWidget(self.soil_widget)

        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)

        # Lookup table and output group
        files_group = QGroupBox("Lookup Table and Output")
        files_layout = QVBoxLayout()

        # Lookup table selection
        lookup_layout = QHBoxLayout()
        self.lbl_lookup = QLabel("Lookup table: not selected")
        self.btn_lookup = QPushButton("Browse for Lookup Table...")
        lookup_layout.addWidget(self.lbl_lookup, 2)
        lookup_layout.addWidget(self.btn_lookup, 1)
        files_layout.addLayout(lookup_layout)

        # Output folder selection
        output_layout = QHBoxLayout()
        self.lbl_out = QLabel("Output folder: not selected")
        self.btn_out = QPushButton("Select Output Folder...")
        output_layout.addWidget(self.lbl_out, 2)
        output_layout.addWidget(self.btn_out, 1)
        files_layout.addLayout(output_layout)

        files_group.setLayout(files_layout)
        main_layout.addWidget(files_group)

        # Refresh button for project layers
        refresh_layout = QHBoxLayout()
        self.btn_refresh = QPushButton("🔄 Refresh Project Layers")
        refresh_layout.addStretch()
        refresh_layout.addWidget(self.btn_refresh)
        main_layout.addLayout(refresh_layout)

        # Progress and run button
        self.progress = QProgressBar()
        self.progress.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.progress)

        self.btn_run = QPushButton("Run Composite CN Calculation")
        self.btn_run.setMinimumHeight(40)
        self.btn_run.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.btn_run)

        self.setLayout(main_layout)

    def create_separator(self):
        """Create a visual separator line."""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line

    def connect_signals(self):
        """Connect button signals."""
        self.btn_lookup.clicked.connect(self.pick_lookup)
        self.btn_out.clicked.connect(self.pick_out_dir)
        self.btn_run.clicked.connect(self.run_calculation)
        self.btn_refresh.clicked.connect(self.refresh_project_layers)

    def refresh_project_layers(self):
        """Refresh the list of available project layers."""
        self.sub_widget.update_layer_combo()
        self.lu_widget.update_layer_combo()
        self.soil_widget.update_layer_combo()
        
        QMessageBox.information(self, "Refreshed", "Project layer lists have been refreshed.")

    def pick_lookup(self):
        """Pick CN lookup table."""
        # Try to find lookup tables in Global References first
        global_ref_path = r"E:\CLAUDE_Workspace\Claude\Report_Files\Templates\Global References"
        start_dir = global_ref_path if os.path.exists(global_ref_path) else ""
        
        path, _ = QFileDialog.getOpenFileName(
            self, "Select CN lookup table", start_dir,
            "CSV or Excel (*.csv *.xls *.xlsx);;CSV files (*.csv);;Excel files (*.xls *.xlsx);;All files (*.*)"
        )
        if path:
            try:
                # Validate lookup table
                df = read_lookup(path)
                self.lookup_path = path
                self.lbl_lookup.setText(f"Lookup table: {Path(path).name} ({len(df)} records)")
                log_message(f"Loaded lookup table: {Path(path).name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading lookup table: {str(e)}")

    def pick_out_dir(self):
        """Pick output directory."""
        # Try to default to project output folder
        default_dir = r"E:\CLAUDE_Workspace\Claude\Report_Files\Projects\2025_Project_Crooked\04_Analysis"
        start_dir = default_dir if os.path.exists(default_dir) else ""
        
        d = QFileDialog.getExistingDirectory(self, "Select output folder", start_dir)
        if d:
            self.out_dir = d
            self.lbl_out.setText(f"Output folder: {d}")

    def validate_inputs(self):
        """Validate all inputs before processing."""
        errors = []
        
        # Check layer selections
        if not self.sub_widget.is_valid_selection():
            errors.append("Please select a valid subbasin layer and field")
        
        if not self.lu_widget.is_valid_selection():
            errors.append("Please select a valid land-use layer and field")
            
        if not self.soil_widget.is_valid_selection():
            errors.append("Please select a valid soils layer and field")
        
        # Check lookup table
        if not self.lookup_path:
            errors.append("Please select a lookup table")
            
        # Check output directory
        if not self.out_dir:
            errors.append("Please select an output folder")
            
        if errors:
            raise ValueError("Please fix the following issues:\n• " + "\n• ".join(errors))
        
        # Validate field existence
        try:
            validate_layer_fields(self.sub_widget.get_selected_layer(), 
                                 self.sub_widget.get_selected_field(), "Subbasin")
            validate_layer_fields(self.lu_widget.get_selected_layer(), 
                                 self.lu_widget.get_selected_field(), "Land-use")
            validate_layer_fields(self.soil_widget.get_selected_layer(), 
                                 self.soil_widget.get_selected_field(), "Soils")
        except ValueError as e:
            raise ValueError(f"Field validation error: {str(e)}")

    def run_calculation(self):
        """Run the composite CN calculation."""
        try:
            # Validate inputs
            self.validate_inputs()
            
            self.progress.setValue(0)
            log_message("Starting composite CN calculation...")

            # Get selected layers and fields
            sub_layer = self.sub_widget.get_selected_layer()
            lu_layer = self.lu_widget.get_selected_layer()
            soil_layer = self.soil_widget.get_selected_layer()
            
            sub_field = self.sub_widget.get_selected_field()
            lu_field = self.lu_widget.get_selected_field()
            soil_field = self.soil_widget.get_selected_field()

            # Create feedback object
            feedback = QgsProcessingFeedback()
            
            # Read and prepare lookup table
            log_message("Reading lookup table...")
            df = read_lookup(self.lookup_path)
            cn_lookup = {}
            
            for _, row in df.iterrows():
                landuse_key = str(row["landuse"]).strip().lower()
                for soil_group in ("a", "b", "c", "d"):
                    cn_lookup[(landuse_key, soil_group)] = float(row[soil_group])
            
            log_message(f"Loaded {len(cn_lookup)} CN lookup entries")
            self.progress.setValue(10)

            # Reproject layers to target CRS
            log_message("Reprojecting layers...")
            sub_reproj = reproject_layer(sub_layer, self.CRS_TARGET, feedback)
            lu_reproj = reproject_layer(lu_layer, self.CRS_TARGET, feedback)
            soil_reproj = reproject_layer(soil_layer, self.CRS_TARGET, feedback)
            self.progress.setValue(25)

            # First intersection: land-use with soils
            log_message("Intersecting land-use with soils...")
            lu_soil = intersect_layers(lu_reproj, soil_reproj, feedback)
            self.progress.setValue(45)

            # Second intersection: subbasins with land-use/soils
            log_message("Intersecting subbasins with land-use/soils...")
            final_intersection = intersect_layers(sub_reproj, lu_soil, feedback)
            self.progress.setValue(65)

            # Calculate composite CN for each subbasin
            log_message("Calculating composite CN values...")
            subbasin_data = {}  # {subbasin_id: {'total_area': float, 'cn_area_sum': float, 'details': []}}
            detailed_records = []  # For comprehensive CSV output
            split_hsg_count = 0  # Track number of split HSGs processed

            for feature in final_intersection.getFeatures():
                # Get attributes
                subbasin_id = feature[sub_field]
                landuse_code = str(feature[lu_field]).strip().lower()
                soil_group_raw = str(feature[soil_field]).strip()
                
                # Parse soil group, handling split HSGs
                soil_group = parse_soil_group(soil_group_raw)
                
                # Track split HSGs
                if '/' in soil_group_raw:
                    split_hsg_count += 1
                
                # Calculate area in acres
                area_sqft = feature.geometry().area()
                area_acres = acres_from_sqft(area_sqft)
                
                # Look up CN value
                cn_key = (landuse_code, soil_group)
                if cn_key not in cn_lookup:
                    log_message(f"Warning: No CN found for land-use '{landuse_code}' and soil group '{soil_group}' (original: '{soil_group_raw}')", Qgis.Warning)
                    continue
                
                cn_value = cn_lookup[cn_key]
                
                # Accumulate data for subbasin
                if subbasin_id not in subbasin_data:
                    subbasin_data[subbasin_id] = {'total_area': 0.0, 'cn_area_sum': 0.0, 'details': []}
                
                subbasin_data[subbasin_id]['total_area'] += area_acres
                subbasin_data[subbasin_id]['cn_area_sum'] += cn_value * area_acres
                
                # Store detailed record for comprehensive output
                detailed_record = {
                    'subbasin_id': subbasin_id,
                    'landuse_code': landuse_code,
                    'soil_group': soil_group.upper(),
                    'soil_group_original': soil_group_raw,  # Keep original for reference
                    'area_acres': area_acres,
                    'cn_value': cn_value,
                    'cn_area_product': cn_value * area_acres
                }
                subbasin_data[subbasin_id]['details'].append(detailed_record)
                detailed_records.append(detailed_record)

            self.progress.setValue(80)

            # Create output subbasin layer with CN_Comp field
            log_message("Creating output layer...")
            
            # Create a new layer based on the reprojected subbasin layer
            output_layer = QgsVectorLayer(f"Polygon?crs={self.CRS_TARGET.authid()}", "subbasins_cn", "memory")
            output_provider = output_layer.dataProvider()
            
            # Copy fields from original subbasin layer and add CN_Comp
            original_fields = sub_reproj.fields()
            new_fields = [field for field in original_fields]
            new_fields.append(QgsField("CN_Comp", QVariant.Double, "double", 10, 2))
            new_fields.append(QgsField("Area_acres", QVariant.Double, "double", 15, 2))
            
            output_provider.addAttributes(new_fields)
            output_layer.updateFields()

            # Add features with calculated CN values
            output_features = []
            for orig_feature in sub_reproj.getFeatures():
                subbasin_id = orig_feature[sub_field]
                
                # Create new feature
                new_feature = QgsFeature()
                new_feature.setGeometry(orig_feature.geometry())
                
                # Copy original attributes
                attributes = list(orig_feature.attributes())
                
                # Calculate and add CN_Comp
                if subbasin_id in subbasin_data and subbasin_data[subbasin_id]['total_area'] > 0:
                    cn_comp = subbasin_data[subbasin_id]['cn_area_sum'] / subbasin_data[subbasin_id]['total_area']
                    total_area = subbasin_data[subbasin_id]['total_area']
                else:
                    cn_comp = None
                    total_area = None
                    log_message(f"Warning: No CN calculated for subbasin {subbasin_id}", Qgis.Warning)
                
                attributes.extend([cn_comp, total_area])
                new_feature.setAttributes(attributes)
                output_features.append(new_feature)

            output_provider.addFeatures(output_features)
            self.progress.setValue(90)

            # Save outputs
            log_message("Saving outputs...")
            
            # Save shapefile
            shp_path = os.path.join(self.out_dir, "subbasins_cn.shp")
            write_options = QgsVectorFileWriter.SaveVectorOptions()
            write_options.driverName = "ESRI Shapefile"
            write_options.fileEncoding = "UTF-8"
            
            error = QgsVectorFileWriter.writeAsVectorFormatV3(
                output_layer, shp_path, QgsProject.instance().transformContext(), write_options
            )
            
            if error[0] != QgsVectorFileWriter.NoError:
                raise ValueError(f"Error saving shapefile: {error[1]}")

            # Save detailed CSV results in the format shown in example
            csv_path = os.path.join(self.out_dir, "cn_calculations_detailed.csv")
            with open(csv_path, "w", newline="", encoding="utf-8") as f_csv:
                writer = csv.writer(f_csv)
                
                # Group detailed records by subbasin
                subbasin_groups = {}
                for record in detailed_records:
                    subbasin_id = record['subbasin_id']
                    if subbasin_id not in subbasin_groups:
                        subbasin_groups[subbasin_id] = []
                    subbasin_groups[subbasin_id].append(record)
                
                # Write data in hierarchical format matching the example
                for subbasin_id in sorted(subbasin_groups.keys()):
                    subbasin_total = subbasin_data[subbasin_id]['total_area']
                    cn_composite = subbasin_data[subbasin_id]['cn_area_sum'] / subbasin_total if subbasin_total > 0 else 0
                    
                    # Write subbasin header row
                    writer.writerow([f"Subbasin ID", "Total Area (acres)", "Composite CN", "", "", "", "", "", ""])
                    writer.writerow([subbasin_id, round(subbasin_total, 2), round(cn_composite, 2), "", "", "", "", "", ""])
                    
                    # Write detail header row
                    writer.writerow(["", "Land Use", "Soil Type", "Area (acres)", "CN Value", "CN x Area", "Original HSG", "", ""])
                    
                    # Write detail rows for this subbasin
                    for record in subbasin_groups[subbasin_id]:
                        # Show original soil group if it was split, otherwise show processed
                        display_soil = record['soil_group']
                        if record['soil_group_original'] != record['soil_group'].upper():
                            display_soil = f"{record['soil_group']} (was {record['soil_group_original']})"
                        
                        writer.writerow([
                            "",
                            record['landuse_code'].upper(),
                            record['soil_group'],
                            round(record['area_acres'], 2),
                            int(record['cn_value']),
                            round(record['cn_area_product'], 2),
                            record['soil_group_original'],
                            "", ""
                        ])
                    
                    # Write empty row separator
                    writer.writerow(["", "", "", "", "", "", "", "", ""])
            
            # Save summary CSV
            summary_csv_path = os.path.join(self.out_dir, "cn_summary.csv")
            with open(summary_csv_path, "w", newline="", encoding="utf-8") as f_csv:
                writer = csv.writer(f_csv)
                writer.writerow(["Subbasin_ID", "Total_Area_Acres", "Sum_CN_x_Area", "CN_Composite"])
                
                for subbasin_id, data in subbasin_data.items():
                    if data['total_area'] > 0:
                        cn_comp = round(data['cn_area_sum'] / data['total_area'], 2)
                        area_acres = round(data['total_area'], 3)
                        cn_area_sum = round(data['cn_area_sum'], 3)
                        writer.writerow([subbasin_id, area_acres, cn_area_sum, cn_comp])

            self.progress.setValue(100)
            
            # Ask if user wants to load result into project
            reply = QMessageBox.question(
                self, "Load Results?", 
                f"Calculation completed successfully!\n\n"
                f"Processed {len([d for d in subbasin_data.values() if d['total_area'] > 0])} subbasins\n\n"
                f"Would you like to load the results into the current QGIS project?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                result_layer = QgsVectorLayer(shp_path, "Subbasins with CN", "ogr")
                QgsProject.instance().addMapLayer(result_layer)
                log_message("Results loaded into QGIS project")
            
            # Success message
            processed_count = len([data for data in subbasin_data.values() if data['total_area'] > 0])
            total_detail_records = len(detailed_records)
            
            # Create detailed success message
            message_parts = [
                f"Composite CN calculation complete!",
                f"Processed {processed_count} subbasins",
                f"Generated {total_detail_records} detailed calculation records"
            ]
            
            if split_hsg_count > 0:
                message_parts.append(f"Handled {split_hsg_count} split HSG records (defaulted to more restrictive group)")
            
            message_parts.extend([
                f"Outputs saved to:",
                f"• {shp_path}",
                f"• {csv_path}",
                f"• {summary_csv_path}"
            ])
            
            message = "\n".join(message_parts[:3]) + "\n\n" + "\n".join(message_parts[3:])
            
            QMessageBox.information(self, "Success", message)
            log_message("Composite CN calculation completed successfully")

        except Exception as e:
            error_msg = f"Error during calculation: {str(e)}"
            log_message(error_msg, Qgis.Critical)
            traceback.print_exc()
            QMessageBox.critical(self, "Error", error_msg)
        finally:
            self.progress.setValue(0)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    """Main entry point for the dialog."""
    dlg = CompositeCNDialog()
    dlg.show()
    return dlg.exec_()


# For direct execution from the Python console
if __name__ == "__main__":
    main()
