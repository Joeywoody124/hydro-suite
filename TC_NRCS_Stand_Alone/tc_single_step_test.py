"""
Time of Concentration - Single Step Tester
Version 1.0.0 - January 2025
Scientific hydrologic analysis with single-step testing for troubleshooting

Test one step at a time to identify and resolve preprocessing issues
Target CRS: EPSG:3361
Test Data: Single_Basin.shp
"""

import os
import traceback
from typing import Optional, Tuple, Dict, Any

from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QComboBox, QTextEdit, QProgressBar, QGroupBox,
    QWidget, QCheckBox, QSpinBox
)
from qgis.PyQt.QtCore import Qt, QThread, pyqtSignal
from qgis.PyQt.QtGui import QFont

from qgis.core import (
    QgsProject, QgsVectorLayer, QgsRasterLayer, QgsGeometry,
    QgsCoordinateReferenceSystem, QgsWkbTypes, QgsProcessingFeedback
)
from qgis import processing


class SingleStepTestWorker(QThread):
    """Worker for single-step testing"""
    
    progress_updated = pyqtSignal(str)
    test_completed = pyqtSignal(str, bool, dict)  # step_name, success, results
    error_occurred = pyqtSignal(str, str)  # step_name, error_message
    
    def __init__(self, basin_layer, dem_layer, test_step, target_crs="EPSG:3361"):
        super().__init__()
        self.basin_layer = basin_layer
        self.dem_layer = dem_layer
        self.test_step = test_step
        self.target_crs = QgsCoordinateReferenceSystem(target_crs)
        
    def run(self):
        """Execute single step test"""
        try:
            if self.test_step == "validate":
                self.test_input_validation()
            elif self.test_step == "preprocess":
                self.test_dem_preprocessing()
            elif self.test_step == "flow_direction":
                self.test_flow_direction()
            elif self.test_step == "slope":
                self.test_slope_calculation()
            else:
                self.error_occurred.emit(self.test_step, f"Unknown test step: {self.test_step}")
                
        except Exception as e:
            self.error_occurred.emit(self.test_step, f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
    
    def test_input_validation(self):
        """Test Step 1: Input validation"""
        self.progress_updated.emit("Testing input validation...")
        
        results = {}
        
        # Check basin layer
        if not self.basin_layer or not self.basin_layer.isValid():
            self.error_occurred.emit("validate", "Invalid basin layer")
            return
            
        basin_count = self.basin_layer.featureCount()
        basin_crs = self.basin_layer.crs()
        results['basin_count'] = basin_count
        results['basin_crs'] = basin_crs.authid()
        
        # Check DEM layer
        if not self.dem_layer or not self.dem_layer.isValid():
            self.error_occurred.emit("validate", "Invalid DEM layer")
            return
            
        dem_crs = self.dem_layer.crs()
        results['dem_crs'] = dem_crs.authid()
        
        # Get basin geometry and area
        if basin_count > 0:
            basin_feature = next(self.basin_layer.getFeatures())
            basin_geom = basin_feature.geometry()
            area_sq_m = basin_geom.area()
            area_acres = area_sq_m / 4046.86
            
            results['basin_area_acres'] = area_acres
            results['basin_area_sq_m'] = area_sq_m
            
            # Get bounding box info
            bbox = basin_geom.boundingBox()
            results['bbox_width_m'] = bbox.width()
            results['bbox_height_m'] = bbox.height()
        
        # CRS compatibility check
        results['crs_match'] = basin_crs == dem_crs
        results['target_crs_match'] = basin_crs.authid() == "EPSG:3361"
        
        self.test_completed.emit("validate", True, results)
    
    def test_dem_preprocessing(self):
        """Test Step 2: DEM preprocessing"""
        self.progress_updated.emit("Testing DEM preprocessing...")
        
        results = {}
        
        # Test Method 1: GDAL fillnodata
        try:
            self.progress_updated.emit("Trying GDAL fillnodata...")
            
            result = processing.run("gdal:fillnodata", {
                'INPUT': self.dem_layer,
                'BAND': 1,
                'DISTANCE': 10,
                'ITERATIONS': 0,
                'NO_MASK': False,
                'MASK_LAYER': None,
                'OPTIONS': '',
                'EXTRA': '',
                'OUTPUT': 'TEMPORARY_OUTPUT'
            })
            
            filled_dem = result['OUTPUT']
            results['method'] = 'GDAL fillnodata'
            results['success'] = True
            results['output_layer'] = filled_dem
            
            # Test if we can get basic statistics
            stats = processing.run("native:rasterlayerstatistics", {
                'INPUT': filled_dem,
                'BAND': 1,
                'OUTPUT_HTML_FILE': 'TEMPORARY_OUTPUT'
            })
            
            results['dem_stats'] = {
                'min': stats.get('MIN', 0),
                'max': stats.get('MAX', 0),
                'mean': stats.get('MEAN', 0)
            }
            
            self.test_completed.emit("preprocess", True, results)
            return
            
        except Exception as gdal_error:
            results['gdal_error'] = str(gdal_error)
            self.progress_updated.emit(f"GDAL fillnodata failed: {str(gdal_error)}")
        
        # Test Method 2: SAGA fillsinks
        try:
            self.progress_updated.emit("Trying SAGA fillsinks...")
            
            result = processing.run("saga:fillsinks", {
                'DEM': self.dem_layer,
                'RESULT': 'TEMPORARY_OUTPUT',
                'MINSLOPE': 0.01
            })
            
            filled_dem = result['RESULT']
            results['method'] = 'SAGA fillsinks'
            results['success'] = True
            results['output_layer'] = filled_dem
            
            self.test_completed.emit("preprocess", True, results)
            return
            
        except Exception as saga_error:
            results['saga_error'] = str(saga_error)
            self.progress_updated.emit(f"SAGA fillsinks failed: {str(saga_error)}")
        
        # Test Method 3: Use original DEM
        try:
            self.progress_updated.emit("Using original DEM (no preprocessing)...")
            
            results['method'] = 'Original DEM (no preprocessing)'
            results['success'] = True
            results['output_layer'] = self.dem_layer
            results['warning'] = 'No preprocessing applied - may affect flow analysis'
            
            self.test_completed.emit("preprocess", True, results)
            return
            
        except Exception as original_error:
            results['original_error'] = str(original_error)
        
        # All methods failed
        self.error_occurred.emit("preprocess", f"All preprocessing methods failed. GDAL: {results.get('gdal_error', 'Unknown')}, SAGA: {results.get('saga_error', 'Unknown')}")
    
    def test_flow_direction(self):
        """Test Step 3: Flow direction calculation"""
        self.progress_updated.emit("Testing flow direction calculation...")
        
        results = {}
        
        # First, we need a preprocessed DEM - use original for testing
        dem_to_use = self.dem_layer
        
        # Test Method 1: GRASS r.watershed
        try:
            self.progress_updated.emit("Trying GRASS r.watershed...")
            
            result = processing.run("grass7:r.watershed", {
                'elevation': dem_to_use,
                'threshold': 1000,
                'max_slope_length': -1,
                'drainage': 'TEMPORARY_OUTPUT',
                'accumulation': 'TEMPORARY_OUTPUT',
                'GRASS_REGION_PARAMETER': None,
                'GRASS_REGION_CELLSIZE_PARAMETER': 0
            })
            
            flow_direction = result['drainage']
            flow_accumulation = result['accumulation']
            
            results['method'] = 'GRASS r.watershed'
            results['success'] = True
            results['flow_direction'] = flow_direction
            results['flow_accumulation'] = flow_accumulation
            
            # Test clipping to basin
            clipped_accumulation = processing.run("gdal:cliprasterbymasklayer", {
                'INPUT': flow_accumulation,
                'MASK': self.basin_layer,
                'SOURCE_CRS': None,
                'TARGET_CRS': None,
                'NODATA': -9999,
                'ALPHA_BAND': False,
                'CROP_TO_CUTLINE': True,
                'KEEP_RESOLUTION': True,
                'OUTPUT': 'TEMPORARY_OUTPUT'
            })
            
            # Get accumulation statistics
            stats = processing.run("native:rasterlayerstatistics", {
                'INPUT': clipped_accumulation['OUTPUT'],
                'BAND': 1,
                'OUTPUT_HTML_FILE': 'TEMPORARY_OUTPUT'
            })
            
            results['accumulation_stats'] = {
                'min': stats.get('MIN', 0),
                'max': stats.get('MAX', 0),
                'mean': stats.get('MEAN', 0)
            }
            
            self.test_completed.emit("flow_direction", True, results)
            return
            
        except Exception as grass_error:
            results['grass_error'] = str(grass_error)
            self.progress_updated.emit(f"GRASS r.watershed failed: {str(grass_error)}")
        
        # Test Method 2: SAGA flow accumulation
        try:
            self.progress_updated.emit("Trying SAGA flow accumulation...")
            
            result = processing.run("saga:flowaccumulationtopdown", {
                'DEM': dem_to_use,
                'METHOD': 0,  # D8
                'FLOW': 'TEMPORARY_OUTPUT'
            })
            
            flow_accumulation = result['FLOW']
            results['method'] = 'SAGA flow accumulation'
            results['success'] = True
            results['flow_accumulation'] = flow_accumulation
            results['flow_direction'] = None  # SAGA doesn't provide direction in this algorithm
            
            self.test_completed.emit("flow_direction", True, results)
            return
            
        except Exception as saga_error:
            results['saga_error'] = str(saga_error)
            self.progress_updated.emit(f"SAGA flow accumulation failed: {str(saga_error)}")
        
        # All methods failed
        self.error_occurred.emit("flow_direction", f"All flow direction methods failed. GRASS: {results.get('grass_error', 'Unknown')}, SAGA: {results.get('saga_error', 'Unknown')}")
    
    def test_slope_calculation(self):
        """Test Step 4: Slope calculation from DEM"""
        self.progress_updated.emit("Testing slope calculation...")
        
        results = {}
        
        # Use original DEM for testing
        dem_to_use = self.dem_layer
        
        try:
            # Calculate slope raster
            self.progress_updated.emit("Calculating slope raster with GDAL...")
            
            slope_result = processing.run("gdal:slope", {
                'INPUT': dem_to_use,
                'BAND': 1,
                'SCALE': 1.0,
                'AS_PERCENT': True,
                'COMPUTE_EDGES': False,
                'ZEVENBERGEN': False,
                'OUTPUT': 'TEMPORARY_OUTPUT'
            })
            
            slope_raster = slope_result['OUTPUT']
            results['slope_raster'] = slope_raster
            
            # Clip slope to basin
            self.progress_updated.emit("Clipping slope to basin...")
            
            clipped_slope = processing.run("gdal:cliprasterbymasklayer", {
                'INPUT': slope_raster,
                'MASK': self.basin_layer,
                'SOURCE_CRS': None,
                'TARGET_CRS': None,
                'NODATA': -9999,
                'ALPHA_BAND': False,
                'CROP_TO_CUTLINE': True,
                'KEEP_RESOLUTION': True,
                'OUTPUT': 'TEMPORARY_OUTPUT'
            })
            
            # Calculate slope statistics
            self.progress_updated.emit("Calculating slope statistics...")
            
            slope_stats = processing.run("native:rasterlayerstatistics", {
                'INPUT': clipped_slope['OUTPUT'],
                'BAND': 1,
                'OUTPUT_HTML_FILE': 'TEMPORARY_OUTPUT'
            })
            
            avg_slope = slope_stats.get('MEAN', 0)
            min_slope = slope_stats.get('MIN', 0)
            max_slope = slope_stats.get('MAX', 0)
            std_slope = slope_stats.get('STD_DEV', 0)
            
            results['slope_statistics'] = {
                'mean': avg_slope,
                'min': min_slope,
                'max': max_slope,
                'std_dev': std_slope
            }
            
            # Apply scientific minimum (1% for validity)
            final_slope = max(avg_slope, 1.0)
            results['final_slope_percent'] = final_slope
            results['method'] = 'GDAL slope calculation'
            results['success'] = True
            
            self.test_completed.emit("slope", True, results)
            
        except Exception as e:
            self.error_occurred.emit("slope", f"Slope calculation failed: {str(e)}")


class SingleStepTesterDialog(QDialog):
    """Single step tester dialog"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TC Calculator - Single Step Tester v1.0.0")
        self.setMinimumSize(800, 600)
        self.resize(900, 700)
        
        self.setup_ui()
        self.populate_layers()
        
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Title
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        
        title = QLabel("TC Single Step Tester - Version 1.0.0")
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        desc = QLabel(
            "Test individual steps of hydrologic analysis for troubleshooting\n"
            "Target CRS: EPSG:3361 | Test Data: Single_Basin.shp"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; margin: 10px; font-style: italic;")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)
        
        # Input section
        input_group = QGroupBox("Input Data")
        input_layout = QVBoxLayout(input_group)
        
        # Basin layer
        basin_layout = QHBoxLayout()
        basin_layout.addWidget(QLabel("Basin Layer:"))
        self.basin_combo = QComboBox()
        self.basin_combo.setMinimumWidth(300)
        self.basin_combo.currentTextChanged.connect(self.update_ui_state)
        basin_layout.addWidget(self.basin_combo, 1)
        input_layout.addLayout(basin_layout)
        
        # DEM layer
        dem_layout = QHBoxLayout()
        dem_layout.addWidget(QLabel("DEM Layer:"))
        self.dem_combo = QComboBox()
        self.dem_combo.setMinimumWidth(300)
        self.dem_combo.currentTextChanged.connect(self.update_ui_state)
        dem_layout.addWidget(self.dem_combo, 1)
        input_layout.addLayout(dem_layout)
        
        layout.addWidget(input_group)
        
        # Test step selection
        test_group = QGroupBox("Test Step Selection")
        test_layout = QVBoxLayout(test_group)
        
        step_layout = QHBoxLayout()
        step_layout.addWidget(QLabel("Test Step:"))
        self.step_combo = QComboBox()
        self.step_combo.addItem("1. Input Validation", "validate")
        self.step_combo.addItem("2. DEM Preprocessing", "preprocess")
        self.step_combo.addItem("3. Flow Direction", "flow_direction")
        self.step_combo.addItem("4. Slope Calculation", "slope")
        step_layout.addWidget(self.step_combo, 1)
        test_layout.addLayout(step_layout)
        
        layout.addWidget(test_group)
        
        # Results display
        results_group = QGroupBox("Test Results")
        results_layout = QVBoxLayout(results_group)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMinimumHeight(250)
        self.results_text.setStyleSheet("font-family: 'Courier New', monospace; font-size: 10pt;")
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(results_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.status_label = QLabel("Select layers and test step")
        self.status_label.setStyleSheet("color: #666; padding: 5px;")
        button_layout.addWidget(self.status_label, 1)
        
        self.test_btn = QPushButton("Run Single Step Test")
        self.test_btn.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                font-weight: bold;
                padding: 8px 16px;
                background-color: #28a745;
                color: white;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.test_btn.clicked.connect(self.run_single_step_test)
        button_layout.addWidget(self.test_btn)
        
        layout.addLayout(button_layout)
        
        self.update_ui_state()
        
    def populate_layers(self):
        """Populate layer dropdown lists"""
        self.basin_combo.clear()
        self.dem_combo.clear()
        
        self.basin_combo.addItem("-- Select basin layer --", None)
        self.dem_combo.addItem("-- Select DEM layer --", None)
        
        project = QgsProject.instance()
        
        # Vector layers for basin
        for layer_id, layer in project.mapLayers().items():
            if isinstance(layer, QgsVectorLayer) and layer.geometryType() == QgsWkbTypes.PolygonGeometry:
                self.basin_combo.addItem(layer.name(), layer)
        
        # Raster layers for DEM
        for layer_id, layer in project.mapLayers().items():
            if isinstance(layer, QgsRasterLayer):
                self.dem_combo.addItem(layer.name(), layer)
    
    def update_ui_state(self):
        """Update UI state"""
        basin_layer = self.basin_combo.currentData()
        dem_layer = self.dem_combo.currentData()
        
        if basin_layer and dem_layer:
            self.status_label.setText("✅ Ready to test")
            self.status_label.setStyleSheet("color: #2e7d32; padding: 5px;")
            self.test_btn.setEnabled(True)
        else:
            missing = []
            if not basin_layer:
                missing.append("basin layer")
            if not dem_layer:
                missing.append("DEM layer")
            
            self.status_label.setText(f"Select: {', '.join(missing)}")
            self.status_label.setStyleSheet("color: #d32f2f; padding: 5px;")
            self.test_btn.setEnabled(False)
    
    def run_single_step_test(self):
        """Run single step test"""
        basin_layer = self.basin_combo.currentData()
        dem_layer = self.dem_combo.currentData()
        test_step = self.step_combo.currentData()
        
        if not basin_layer or not dem_layer:
            QMessageBox.warning(self, "Missing Input", "Please select both basin and DEM layers.")
            return
        
        # Clear results
        self.results_text.clear()
        step_name = self.step_combo.currentText()
        self.results_text.append(f"="*60)
        self.results_text.append(f"TESTING: {step_name}")
        self.results_text.append(f"="*60)
        self.results_text.append("")
        
        # Disable UI during testing
        self.test_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        # Create and start worker
        self.worker = SingleStepTestWorker(basin_layer, dem_layer, test_step)
        
        # Connect signals
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.test_completed.connect(self.on_test_completed)
        self.worker.error_occurred.connect(self.on_test_error)
        
        # Start test
        self.worker.start()
    
    def on_progress_updated(self, message):
        """Handle progress updates"""
        self.status_label.setText(message)
        self.results_text.append(f"🔄 {message}")
        self.results_text.ensureCursorVisible()
    
    def on_test_completed(self, step_name, success, results):
        """Handle test completion"""
        self.progress_bar.setVisible(False)
        self.test_btn.setEnabled(True)
        
        if success:
            self.results_text.append(f"✅ SUCCESS: {step_name}")
            self.results_text.append("")
            self.results_text.append("📊 RESULTS:")
            
            for key, value in results.items():
                if isinstance(value, dict):
                    self.results_text.append(f"  {key}:")
                    for sub_key, sub_value in value.items():
                        self.results_text.append(f"    {sub_key}: {sub_value}")
                else:
                    self.results_text.append(f"  {key}: {value}")
            
            self.status_label.setText(f"✅ {step_name} completed successfully")
            self.status_label.setStyleSheet("color: #2e7d32; padding: 5px;")
        else:
            self.results_text.append(f"❌ FAILED: {step_name}")
            self.status_label.setText(f"❌ {step_name} failed")
            self.status_label.setStyleSheet("color: #d32f2f; padding: 5px;")
        
        self.results_text.ensureCursorVisible()
    
    def on_test_error(self, step_name, error_message):
        """Handle test error"""
        self.progress_bar.setVisible(False)
        self.test_btn.setEnabled(True)
        
        self.results_text.append(f"❌ ERROR in {step_name}:")
        self.results_text.append(f"   {error_message}")
        
        self.status_label.setText(f"❌ {step_name} error")
        self.status_label.setStyleSheet("color: #d32f2f; padding: 5px;")
        
        self.results_text.ensureCursorVisible()


def run_single_step_tester():
    """Main function to run single step tester"""
    try:
        print("="*60)
        print("TC SINGLE STEP TESTER - VERSION 1.0.0")
        print("="*60)
        print("\nTROUBLESHOOTING APPROACH:")
        print("🔧 Test one step at a time")
        print("🔍 Identify exact failure points")
        print("📊 Detailed results for each step")
        print("🎯 Target CRS: EPSG:3361")
        print("\nOpening single step tester...")
        
        dialog = SingleStepTesterDialog()
        dialog.show()
        
        print("✅ Single step tester ready!")
        
        return dialog
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


# Execute the single step tester
print("🚀 Starting Single Step Tester...")
single_step_dialog = run_single_step_tester()

if single_step_dialog:
    print("\n" + "="*60)
    print("✅ SINGLE STEP TESTER READY!")
    print("="*60)
    print("📋 Testing steps available:")
    print("  1. Input Validation - Check layers and CRS")
    print("  2. DEM Preprocessing - Test fillnodata/fillsinks")
    print("  3. Flow Direction - Test GRASS/SAGA flow analysis")
    print("  4. Slope Calculation - Test GDAL slope from DEM")
    print("\n🎯 Load your Single_Basin.shp and DEM, then test each step!")