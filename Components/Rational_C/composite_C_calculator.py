# -*- coding: utf-8 -*-
"""
Rational Method Composite C Calculator
Version 1.0 — 2025-06-06

Calculates area-weighted composite Rational Method runoff coefficients (C) in QGIS.
This script is designed for use in the QGIS Python Console.

Key Features:
- Calculates composite 'C' based on catchment, land use, and soils layers.
- User selects a project-wide slope category (0-2%, 2-6%, 6%+) via the GUI.
- Flexible input layer selection (from QGIS project or file browsing).
- Handles split hydrologic soil groups (e.g., 'B/D' defaults to 'D').
- Assigns a C-value of 0.95 for unrecognized soil groups (e.g., Water).
- Generates a new shapefile with the C_Comp field.
- Creates detailed and summary CSV reports of the calculation.
- Inspired by the framework of the Composite CN Calculator v2.2.

Required Fields
---------------
Catchment Layer : A unique identifier field (e.g., 'Name').
Land-Use Layer  : A land use code field (e.g., 'LU').
Soils Layer     : A hydrologic soil group field (e.g., 'hydgrpdcd').

Lookup Table Columns (case-insensitive)
---------------------------------------
landuse, A_0-2%, A_2-6%, A_6%+, B_0-2%, B_2-6%, B_6%+, C_0-2%, C_2-6%, C_6%+, D_0-2%, D_2-6%, D_6%+

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
    QgsWkbTypes
)
from qgis import processing


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def log_message(message: str, level=Qgis.Info):
    """Logs a message to the QGIS message log panel."""
    QgsMessageLog.logMessage(message, "Rational C Calculator", level)


def parse_soil_group(soil_group_raw: str) -> str or None:
    """
    Parses a soil group string. Handles split HSGs by defaulting to the
    more restrictive (second) group. Returns the lowercase soil group ('a', 'b',
    'c', 'd') if valid, otherwise returns None.

    Examples:
    - 'A'     -> 'a'
    - 'B/D'   -> 'd'
    - 'C/D'   -> 'd'
    - 'Water' -> None
    - ''      -> None
    """
    if not soil_group_raw or pd.isna(soil_group_raw):
        log_message("Unrecognized soil group (empty), will use default C=0.95", Qgis.Warning)
        return None

    soil_group = str(soil_group_raw).strip().upper()

    # Handle split soil groups (e.g., 'A/D', 'B/D', 'C/D')
    if '/' in soil_group:
        parts = soil_group.split('/')
        if len(parts) > 1:
            soil_group = parts[1].strip()
            log_message(f"Split HSG detected: '{soil_group_raw}' -> using '{soil_group}'")

    # Validate and return lowercase, or None if invalid
    if soil_group in ['A', 'B', 'C', 'D']:
        return soil_group.lower()
    else:
        log_message(f"Unrecognized soil group '{soil_group_raw}', will use default C=0.95", Qgis.Warning)
        return None  # Indicates a case like 'Water' or other non-standard entry


def acres_from_sqft(area_sqft: float) -> float:
    """Converts square feet to acres."""
    return area_sqft / 43560.0


def get_vector_layers_from_project():
    """Gets all polygon vector layers currently loaded in the QGIS project."""
    return [
        layer for layer in QgsProject.instance().mapLayers().values()
        if isinstance(layer, QgsVectorLayer) and layer.geometryType() == QgsWkbTypes.PolygonGeometry
    ]


def validate_layer_fields(layer: QgsVectorLayer, required_field: str, layer_name: str) -> bool:
    """Validates that a layer has a required field."""
    if required_field not in layer.fields().names():
        raise ValueError(f"{layer_name} layer missing required field '{required_field}'.")
    return True


def read_lookup(path: str) -> pd.DataFrame:
    """
    Reads a Rational C lookup CSV or Excel file into a pandas DataFrame and
    prepares it for use.
    """
    ext = Path(path).suffix.lower()
    df = pd.read_excel(path) if ext in (".xls", ".xlsx") else pd.read_csv(path)

    df.columns = [c.strip().lower() for c in df.columns]

    # Validate required 'landuse' column
    if "landuse" not in df.columns:
        raise ValueError("Lookup table is missing the required 'landuse' column.")

    # Prepare landuse column for consistent matching
    df['landuse'] = df['landuse'].astype(str).str.strip().str.lower()
    
    # Set landuse as the index for efficient lookups
    df = df.set_index('landuse')

    log_message("Successfully read and prepared lookup table.")
    return df


def load_layer(path: str, name: str) -> QgsVectorLayer:
    """Loads a vector layer with validation."""
    layer = QgsVectorLayer(path, name, "ogr")
    if not layer.isValid():
        raise ValueError(f"Cannot load layer: {path}")
    if layer.featureCount() == 0:
        raise ValueError(f"Layer is empty: {path}")
    return layer


def reproject_layer(layer: QgsVectorLayer, target_crs: QgsCoordinateReferenceSystem, feedback) -> QgsVectorLayer:
    """Reprojects a layer to the target CRS if necessary."""
    if layer.crs() == target_crs:
        return layer

    log_message(f"Reprojecting layer from {layer.crs().authid()} to {target_crs.authid()}")
    return processing.run("native:reprojectlayer", {"INPUT": layer, "TARGET_CRS": target_crs, "OUTPUT": "memory:"}, feedback=feedback)["OUTPUT"]


def intersect_layers(layer1: QgsVectorLayer, layer2: QgsVectorLayer, feedback) -> QgsVectorLayer:
    """Performs an intersection between two layers."""
    log_message(f"Intersecting {layer1.name()} with {layer2.name()}")
    result = processing.run("native:intersection", {"INPUT": layer1, "OVERLAY": layer2, "OUTPUT": "memory:"}, feedback=feedback)
    intersection = result["OUTPUT"]
    if intersection.featureCount() == 0:
        raise ValueError("Intersection resulted in no features. Check for layer overlap.")
    return intersection


# ---------------------------------------------------------------------------
# Layer Selection Widget (Reused from example)
# ---------------------------------------------------------------------------
class LayerSelectionWidget(QFrame):
    """A widget for selecting a layer from the project or a file."""
    
    def __init__(self, layer_type: str, default_field: str, parent=None):
        super().__init__(parent)
        self.layer_type = layer_type
        self.default_field = default_field
        self.selected_layer = None
        self.setup_ui()
        self.update_layer_combo()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        title = QLabel(f"{self.layer_type.title()} Layer Selection")
        title.setStyleSheet("font-weight: bold;")
        layout.addWidget(title)
        
        self.radio_project = QRadioButton("Use layer from current project")
        self.radio_file = QRadioButton("Browse for file")
        self.radio_project.setChecked(True)
        
        layout.addWidget(self.radio_project)
        layout.addWidget(self.radio_file)
        
        self.combo_layers = QComboBox()
        self.combo_layers.setMinimumWidth(300)
        layout.addWidget(self.combo_layers)
        
        file_layout = QHBoxLayout()
        self.lbl_file = QLabel("No file selected")
        self.btn_browse = QPushButton("Browse...")
        self.btn_browse.setEnabled(False)
        file_layout.addWidget(self.lbl_file, 2)
        file_layout.addWidget(self.btn_browse, 1)
        layout.addLayout(file_layout)
        
        field_layout = QHBoxLayout()
        field_layout.addWidget(QLabel("Field:"))
        self.combo_fields = QComboBox()
        field_layout.addWidget(self.combo_fields)
        layout.addLayout(field_layout)
        
        self.setLayout(layout)
        
        self.radio_project.toggled.connect(self.on_selection_method_changed)
        self.combo_layers.currentTextChanged.connect(self.on_layer_changed)
        self.btn_browse.clicked.connect(self.browse_for_file)
        
    def update_layer_combo(self):
        self.combo_layers.clear()
        self.combo_layers.addItem("-- Select a layer --")
        vector_layers = get_vector_layers_from_project()
        for layer in vector_layers:
            self.combo_layers.addItem(layer.name(), layer)
        if not vector_layers:
            self.combo_layers.addItem("No polygon layers loaded")
            self.radio_project.setEnabled(False)
            self.radio_file.setChecked(True)
        else:
            self.radio_project.setEnabled(True)
    
    def on_selection_method_changed(self, is_checked):
        if not is_checked: return
        use_project = self.radio_project.isChecked()
        self.combo_layers.setEnabled(use_project)
        self.btn_browse.setEnabled(not use_project)
        self.lbl_file.setText("Using project layer" if use_project else "No file selected")
        if use_project: self.on_layer_changed(self.combo_layers.currentIndex())
        else: self.combo_fields.clear(); self.selected_layer = None
    
    def on_layer_changed(self, index):
        if not self.radio_project.isChecked(): return
        layer = self.combo_layers.currentData()
        self.selected_layer = layer if isinstance(layer, QgsVectorLayer) else None
        self.populate_field_combo(self.selected_layer)
    
    def browse_for_file(self):
        path, _ = QFileDialog.getOpenFileName(self, f"Select {self.layer_type} layer", "", "Vector files (*.shp *.gpkg)")
        if path:
            try:
                layer = load_layer(path, self.layer_type)
                self.selected_layer = layer
                self.lbl_file.setText(Path(path).name)
                self.populate_field_combo(layer)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading layer: {e}")
                self.selected_layer = None
    
    def populate_field_combo(self, layer: QgsVectorLayer):
        self.combo_fields.clear()
        if layer and layer.isValid():
            field_names = layer.fields().names()
            self.combo_fields.addItems(field_names)
            if self.default_field in field_names:
                self.combo_fields.setCurrentText(self.default_field)
    
    def get_selected_layer(self): return self.selected_layer
    def get_selected_field(self): return self.combo_fields.currentText()
    def is_valid_selection(self): return self.selected_layer and self.selected_layer.isValid() and self.get_selected_field()


# ---------------------------------------------------------------------------
# Main Dialog
# ---------------------------------------------------------------------------

class RationalCCalculatorDialog(QDialog):
    """GUI for the Rational Method Composite C Calculator."""

    CRS_TARGET = QgsCoordinateReferenceSystem("EPSG:3361") # A projected CRS for accurate area calculation

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rational Method 'C' Calculator v1.0")
        self.setMinimumWidth(700)
        self.lookup_path = None
        self.out_dir = None
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        # --- Input Layers Group ---
        input_group = QGroupBox("Input Layers")
        input_layout = QVBoxLayout()
        self.catchment_widget = LayerSelectionWidget("Catchment", "Name")
        self.lu_widget = LayerSelectionWidget("Land-Use", "LU")
        self.soil_widget = LayerSelectionWidget("Soils", "hydgrpdcd")
        input_layout.addWidget(self.catchment_widget)
        input_layout.addWidget(self.create_separator())
        input_layout.addWidget(self.lu_widget)
        input_layout.addWidget(self.create_separator())
        input_layout.addWidget(self.soil_widget)
        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)
        
        # --- Slope Selection Group ---
        slope_group = QGroupBox("Project-Wide Land Slope Category")
        slope_layout = QHBoxLayout()
        self.slope_button_group = QButtonGroup()
        self.radio_slope1 = QRadioButton("0% - 2%")
        self.radio_slope2 = QRadioButton("2% - 6%")
        self.radio_slope3 = QRadioButton("6% +")
        self.radio_slope1.setChecked(True) # Default selection
        self.slope_button_group.addButton(self.radio_slope1)
        self.slope_button_group.addButton(self.radio_slope2)
        self.slope_button_group.addButton(self.radio_slope3)
        slope_layout.addWidget(self.radio_slope1)
        slope_layout.addWidget(self.radio_slope2)
        slope_layout.addWidget(self.radio_slope3)
        slope_group.setLayout(slope_layout)
        main_layout.addWidget(slope_group)

        # --- Files and Output Group ---
        files_group = QGroupBox("Lookup Table and Output")
        files_layout = QVBoxLayout()
        lookup_layout = QHBoxLayout()
        self.lbl_lookup = QLabel("Lookup table: not selected")
        self.btn_lookup = QPushButton("Browse for Lookup Table...")
        lookup_layout.addWidget(self.lbl_lookup, 2)
        lookup_layout.addWidget(self.btn_lookup, 1)
        files_layout.addLayout(lookup_layout)
        output_layout = QHBoxLayout()
        self.lbl_out = QLabel("Output folder: not selected")
        self.btn_out = QPushButton("Select Output Folder...")
        output_layout.addWidget(self.lbl_out, 2)
        output_layout.addWidget(self.btn_out, 1)
        files_layout.addLayout(output_layout)
        files_group.setLayout(files_layout)
        main_layout.addWidget(files_group)
        
        # --- Controls ---
        self.progress = QProgressBar()
        self.progress.setAlignment(Qt.AlignCenter)
        self.btn_run = QPushButton("Run 'C' Value Calculation")
        self.btn_run.setMinimumHeight(40)
        self.btn_run.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.progress)
        main_layout.addWidget(self.btn_run)
        self.setLayout(main_layout)

    def create_separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line

    def connect_signals(self):
        self.btn_lookup.clicked.connect(self.pick_lookup)
        self.btn_out.clicked.connect(self.pick_out_dir)
        self.btn_run.clicked.connect(self.run_calculation)

    def pick_lookup(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select C-Value Lookup Table", "", "Data files (*.csv *.xlsx *.xls)")
        if path:
            try:
                df = read_lookup(path)
                self.lookup_path = path
                self.lbl_lookup.setText(f"Lookup: {Path(path).name} ({len(df)} records)")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error reading lookup table: {e}")

    def pick_out_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if d:
            self.out_dir = d
            self.lbl_out.setText(f"Output: {d}")

    def validate_inputs(self):
        errors = []
        if not self.catchment_widget.is_valid_selection(): errors.append("Select a valid catchment layer and field.")
        if not self.lu_widget.is_valid_selection(): errors.append("Select a valid land-use layer and field.")
        if not self.soil_widget.is_valid_selection(): errors.append("Select a valid soils layer and field.")
        if not self.lookup_path: errors.append("Select a lookup table.")
        if not self.out_dir: errors.append("Select an output folder.")
        
        if errors:
            raise ValueError("Please fix the following issues:\n• " + "\n• ".join(errors))
        
        # Validate required fields exist on selected layers
        validate_layer_fields(self.catchment_widget.get_selected_layer(), self.catchment_widget.get_selected_field(), "Catchment")
        validate_layer_fields(self.lu_widget.get_selected_layer(), self.lu_widget.get_selected_field(), "Land-use")
        validate_layer_fields(self.soil_widget.get_selected_layer(), self.soil_widget.get_selected_field(), "Soils")

    def run_calculation(self):
        try:
            self.validate_inputs()
            self.progress.setValue(0)
            log_message("Starting composite 'C' value calculation...")

            # --- 1. Get Inputs and Prepare Data ---
            catchment_layer = self.catchment_widget.get_selected_layer()
            lu_layer = self.lu_widget.get_selected_layer()
            soil_layer = self.soil_widget.get_selected_layer()
            
            catchment_field = self.catchment_widget.get_selected_field()
            lu_field = self.lu_widget.get_selected_field()
            soil_field = self.soil_widget.get_selected_field()

            # Determine selected slope category to build the lookup column name
            if self.radio_slope1.isChecked(): slope_suffix = "_0-2%"
            elif self.radio_slope2.isChecked(): slope_suffix = "_2-6%"
            else: slope_suffix = "_6%+"
            log_message(f"Using slope category for lookup: {slope_suffix}")
            
            feedback = QgsProcessingFeedback()
            c_lookup_df = read_lookup(self.lookup_path)
            self.progress.setValue(10)

            # --- 2. Reproject and Intersect Layers ---
            log_message("Reprojecting layers...")
            catchment_reproj = reproject_layer(catchment_layer, self.CRS_TARGET, feedback)
            lu_reproj = reproject_layer(lu_layer, self.CRS_TARGET, feedback)
            soil_reproj = reproject_layer(soil_layer, self.CRS_TARGET, feedback)
            self.progress.setValue(25)

            log_message("Intersecting land-use with soils...")
            lu_soil_intersect = intersect_layers(lu_reproj, soil_reproj, feedback)
            self.progress.setValue(45)

            log_message("Intersecting catchments with combined land-use/soils...")
            final_intersect = intersect_layers(catchment_reproj, lu_soil_intersect, feedback)
            self.progress.setValue(65)

            # --- 3. Calculate Composite C Values ---
            log_message("Calculating C values for each polygon...")
            catchment_data = {}
            detailed_records = []

            for feature in final_intersect.getFeatures():
                catchment_id = feature[catchment_field]
                landuse_code = str(feature[lu_field]).strip().lower()
                soil_group_raw = feature[soil_field]
                
                soil_group = parse_soil_group(soil_group_raw)
                area_acres = acres_from_sqft(feature.geometry().area())

                if soil_group is None:
                    # Case for water or unrecognized HSG, use fixed C value
                    c_value = 0.95
                else:
                    # Standard case: look up C value from the table
                    column_to_lookup = f"{soil_group}{slope_suffix}"
                    try:
                        # Use .loc to find the value at the intersection of landuse (index) and the constructed column
                        c_value = c_lookup_df.loc[landuse_code, column_to_lookup]
                    except KeyError:
                        log_message(f"Warning: No C value found for land-use '{landuse_code}' and column '{column_to_lookup}'. Skipping polygon.", Qgis.Warning)
                        continue
                
                if catchment_id not in catchment_data:
                    catchment_data[catchment_id] = {'total_area': 0.0, 'c_area_sum': 0.0}
                
                catchment_data[catchment_id]['total_area'] += area_acres
                catchment_data[catchment_id]['c_area_sum'] += c_value * area_acres
                
                detailed_records.append({
                    'catchment_id': catchment_id, 'landuse': landuse_code,
                    'soil_group_raw': str(soil_group_raw).strip(), 'soil_group_used': soil_group.upper() if soil_group else 'N/A',
                    'area_acres': area_acres, 'c_value': c_value, 'c_area_product': c_value * area_acres
                })

            self.progress.setValue(80)

            # --- 4. Create and Save Output Layer ---
            log_message("Creating output shapefile...")
            output_layer = QgsVectorLayer(f"Polygon?crs={self.CRS_TARGET.authid()}", "catchments_c_value", "memory")
            output_provider = output_layer.dataProvider()
            
            # Copy fields from original reprojected catchment layer
            new_fields = list(catchment_reproj.fields())
            new_fields.append(QgsField("C_Comp", QVariant.Double, "double", 10, 3))
            new_fields.append(QgsField("Area_acres", QVariant.Double, "double", 15, 2))
            output_provider.addAttributes(new_fields)
            output_layer.updateFields()

            output_features = []
            for orig_feature in catchment_reproj.getFeatures():
                catchment_id = orig_feature[catchment_field]
                new_feature = QgsFeature(output_layer.fields()) # Use fields from output layer
                new_feature.setGeometry(orig_feature.geometry())
                
                # Copy original attributes
                for i, field in enumerate(catchment_reproj.fields()):
                    new_feature[field.name()] = orig_feature.attribute(field.name())
                
                # Calculate and add new attributes
                if catchment_id in catchment_data and catchment_data[catchment_id]['total_area'] > 0:
                    data = catchment_data[catchment_id]
                    c_comp = data['c_area_sum'] / data['total_area']
                    total_area = data['total_area']
                else:
                    c_comp, total_area = None, None # Use None for NULL
                    log_message(f"Warning: No C value calculated for catchment {catchment_id}", Qgis.Warning)
                
                new_feature["C_Comp"] = c_comp
                new_feature["Area_acres"] = total_area
                output_features.append(new_feature)

            output_provider.addFeatures(output_features)
            self.progress.setValue(90)
            shp_path = os.path.join(self.out_dir, "catchments_with_C_value.shp")
            QgsVectorFileWriter.writeAsVectorFormat(output_layer, shp_path, "UTF-8", output_layer.crs(), "ESRI Shapefile")

            # --- 5. Save CSV Reports ---
            log_message("Saving CSV reports...")
            # Detailed CSV
            csv_path = os.path.join(self.out_dir, "c_value_calculations_detailed.csv")
            df_detailed = pd.DataFrame(detailed_records)
            df_detailed.to_csv(csv_path, index=False, float_format='%.4f')
            
            # Summary CSV
            summary_data = []
            for cid, data in catchment_data.items():
                if data['total_area'] > 0:
                    c_comp = data['c_area_sum'] / data['total_area']
                    summary_data.append([cid, data['total_area'], data['c_area_sum'], c_comp])
            
            df_summary = pd.DataFrame(summary_data, columns=["Catchment_ID", "Total_Area_Acres", "Sum_C_x_Area", "C_Composite"])
            summary_csv_path = os.path.join(self.out_dir, "c_value_summary.csv")
            df_summary.to_csv(summary_csv_path, index=False, float_format='%.3f')
            
            self.progress.setValue(100)
            
            # --- 6. Finalize and Notify User ---
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setText("Calculation Complete!")
            msg_box.setInformativeText(f"Outputs saved to:\n• {shp_path}\n• {csv_path}\n• {summary_csv_path}\n\nLoad the result layer into QGIS?")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.Yes)
            
            if msg_box.exec() == QMessageBox.Yes:
                QgsProject.instance().addMapLayer(QgsVectorLayer(shp_path, "Catchments with C-Value", "ogr"))
            
            log_message("Calculation finished successfully.")

        except Exception as e:
            error_msg = f"An error occurred: {e}"
            log_message(error_msg, Qgis.Critical)
            traceback.print_exc()
            QMessageBox.critical(self, "Error", error_msg)
        finally:
            self.progress.setValue(0)

# ---------------------------------------------------------------------------
# Entry Point for QGIS Python Console
# ---------------------------------------------------------------------------
def run_dialog():
    """Function to create and show the dialog."""
    # This check ensures it works with Plugin Reloader or from the console
    global c_calculator_dialog
    try:
        # If the dialog exists, close and delete it to avoid duplicates
        c_calculator_dialog.close()
        c_calculator_dialog.deleteLater()
    except (NameError, AttributeError):
        pass # Dialog doesn't exist yet, which is fine
    
    # Create and show the new dialog
    c_calculator_dialog = RationalCCalculatorDialog()
    c_calculator_dialog.show()

# --- Run the script ---
# This line makes it easy to start the tool from the QGIS Python Console
run_dialog()
