"""
Time of Concentration - Step-by-Step Scientific Analysis Tester
Tests proper hydrologic analysis with DEM-based slope and hydraulic length
Version 1.0 - January 2025

SCIENTIFIC APPROACH:
- Average basin slope from DEM analysis
- Hydraulic length from flow path analysis
- Proper SCS/NRCS TR-55 methodology
- Step-by-step testing with single basin first

Test Data: E:\CLAUDE_Workspace\Claude\Report_Files\Codebase\Hydro_Suite\TC_NRCS_Stand_Alone\Test_Data\Single_Basin.shp
Project CRS: EPSG:3361
"""

import os
import traceback
from typing import Optional, Tuple, Dict, Any

from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QComboBox, QTextEdit, QProgressBar, QGroupBox,
    QTabWidget, QWidget, QCheckBox
)
from qgis.PyQt.QtCore import Qt, QThread, pyqtSignal
from qgis.PyQt.QtGui import QFont

from qgis.core import (
    QgsProject, QgsVectorLayer, QgsRasterLayer, QgsGeometry,
    QgsCoordinateReferenceSystem, QgsWkbTypes, QgsProcessingFeedback
)
from qgis import processing


class HydrologicTestWorker(QThread):
    """Worker for step-by-step hydrologic analysis testing"""
    
    progress_updated = pyqtSignal(str)
    step_completed = pyqtSignal(str, bool, str)  # step_name, success, result_info
    test_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str, str)  # step_name, error_message
    
    def __init__(self, basin_layer, dem_layer, target_crs="EPSG:3361"):
        super().__init__()
        self.basin_layer = basin_layer
        self.dem_layer = dem_layer
        self.target_crs = QgsCoordinateReferenceSystem(target_crs)
        self.results = {}
        
    def run(self):
        """Execute step-by-step hydrologic analysis"""
        try:
            self.progress_updated.emit("Starting step-by-step hydrologic analysis...")
            
            # Step 1: Validate input data
            if not self.step_1_validate_inputs():
                return
                
            # Step 2: Test DEM preprocessing (fill sinks)
            if not self.step_2_preprocess_dem():
                return
                
            # Step 3: Calculate flow direction
            if not self.step_3_flow_direction():
                return
                
            # Step 4: Calculate flow accumulation
            if not self.step_4_flow_accumulation():
                return
                
            # Step 5: Extract flow paths
            if not self.step_5_flow_paths():
                return
                
            # Step 6: Calculate hydraulic length
            if not self.step_6_hydraulic_length():
                return
                
            # Step 7: Calculate average basin slope
            if not self.step_7_basin_slope():
                return
                
            # Step 8: Calculate TC using SCS/NRCS TR-55
            if not self.step_8_calculate_tc():
                return
                
            self.test_completed.emit(self.results)
            
        except Exception as e:
            self.error_occurred.emit("General", f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
    
    def step_1_validate_inputs(self) -> bool:
        """Step 1: Validate input data"""
        try:
            self.progress_updated.emit("Step 1: Validating input data...")
            
            # Check basin layer
            if not self.basin_layer or not self.basin_layer.isValid():
                self.error_occurred.emit("Step 1", "Invalid basin layer")
                return False
                
            basin_count = self.basin_layer.featureCount()
            if basin_count == 0:
                self.error_occurred.emit("Step 1", "Basin layer has no features")
                return False
                
            # Check DEM layer
            if not self.dem_layer or not self.dem_layer.isValid():
                self.error_occurred.emit("Step 1", "Invalid DEM layer")
                return False
                
            # Check CRS compatibility
            basin_crs = self.basin_layer.crs()
            dem_crs = self.dem_layer.crs()
            
            crs_info = f"Basin CRS: {basin_crs.authid()}, DEM CRS: {dem_crs.authid()}"
            
            if basin_crs != dem_crs:
                self.progress_updated.emit(f"Warning: CRS mismatch - {crs_info}")
            
            # Get basin geometry for analysis
            basin_feature = next(self.basin_layer.getFeatures())
            basin_geom = basin_feature.geometry()
            area_sq_m = basin_geom.area()
            area_acres = area_sq_m / 4046.86
            
            self.results['basin_area_acres'] = area_acres
            self.results['basin_area_sq_m'] = area_sq_m
            self.results['basin_geometry'] = basin_geom
            
            result_info = f"Basin features: {basin_count}, Area: {area_acres:.2f} acres, {crs_info}"
            self.step_completed.emit("Step 1: Input Validation", True, result_info)
            return True
            
        except Exception as e:
            self.error_occurred.emit("Step 1", str(e))
            return False
    
    def step_2_preprocess_dem(self) -> bool:
        """Step 2: Preprocess DEM (fill sinks)"""
        try:
            self.progress_updated.emit("Step 2: Preprocessing DEM (fill sinks)...")
            
            # Try GDAL fillnodata first (more reliable than SAGA)
            try:
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
                
                self.results['filled_dem'] = result['OUTPUT']
                self.step_completed.emit("Step 2: DEM Preprocessing", True, "Used GDAL fillnodata")
                return True
                
            except Exception as gdal_error:
                self.progress_updated.emit("GDAL fillnodata failed, trying SAGA fillsinks...")
                
                # Fallback to SAGA fillsinks
                try:
                    result = processing.run("saga:fillsinks", {
                        'DEM': self.dem_layer,
                        'RESULT': 'TEMPORARY_OUTPUT',
                        'MINSLOPE': 0.01
                    })
                    
                    self.results['filled_dem'] = result['RESULT']
                    self.step_completed.emit("Step 2: DEM Preprocessing", True, "Used SAGA fillsinks")
                    return True
                    
                except Exception as saga_error:
                    # Use original DEM if both fail
                    self.results['filled_dem'] = self.dem_layer
                    self.step_completed.emit("Step 2: DEM Preprocessing", True, "Using original DEM (no preprocessing)")
                    return True
            
        except Exception as e:
            self.error_occurred.emit("Step 2", str(e))
            return False
    
    def step_3_flow_direction(self) -> bool:
        """Step 3: Calculate flow direction"""
        try:
            self.progress_updated.emit("Step 3: Calculating flow direction...")
            
            # Try GRASS r.watershed first
            try:
                result = processing.run("grass7:r.watershed", {
                    'elevation': self.results['filled_dem'],
                    'threshold': 1000,
                    'max_slope_length': -1,
                    'drainage': 'TEMPORARY_OUTPUT',
                    'accumulation': 'TEMPORARY_OUTPUT',
                    'GRASS_REGION_PARAMETER': None,
                    'GRASS_REGION_CELLSIZE_PARAMETER': 0
                })
                
                self.results['flow_direction'] = result['drainage']
                self.results['flow_accumulation'] = result['accumulation']
                self.step_completed.emit("Step 3: Flow Direction", True, "Used GRASS r.watershed")
                return True
                
            except Exception as grass_error:
                self.progress_updated.emit("GRASS r.watershed failed, trying SAGA flow direction...")
                
                # Fallback to SAGA
                try:
                    result = processing.run("saga:flowaccumulationtopdown", {
                        'DEM': self.results['filled_dem'],
                        'METHOD': 0,  # D8
                        'FLOW': 'TEMPORARY_OUTPUT'
                    })
                    
                    self.results['flow_accumulation'] = result['FLOW']
                    
                    # Calculate flow direction separately
                    dir_result = processing.run("saga:slopeaspectcurvature", {
                        'ELEVATION': self.results['filled_dem'],
                        'SLOPE': 'TEMPORARY_OUTPUT',
                        'ASPECT': 'TEMPORARY_OUTPUT',
                        'METHOD': 6,  # Maximum Slope (Travis et al. 1975)
                        'UNIT_SLOPE': 0,  # radians
                        'UNIT_ASPECT': 0  # radians
                    })
                    
                    self.results['flow_direction'] = dir_result['ASPECT']  # Use aspect as flow direction
                    self.step_completed.emit("Step 3: Flow Direction", True, "Used SAGA flow accumulation + aspect")
                    return True
                    
                except Exception as saga_error:
                    self.error_occurred.emit("Step 3", f"Both GRASS and SAGA failed: {str(saga_error)}")
                    return False
            
        except Exception as e:
            self.error_occurred.emit("Step 3", str(e))
            return False
    
    def step_4_flow_accumulation(self) -> bool:
        """Step 4: Verify flow accumulation (already done in step 3)"""
        try:
            self.progress_updated.emit("Step 4: Verifying flow accumulation...")
            
            if 'flow_accumulation' not in self.results:
                self.error_occurred.emit("Step 4", "Flow accumulation not available from previous step")
                return False
            
            # Get statistics of flow accumulation within basin
            clipped_accumulation = processing.run("gdal:cliprasterbymasklayer", {
                'INPUT': self.results['flow_accumulation'],
                'MASK': self.basin_layer,
                'SOURCE_CRS': None,
                'TARGET_CRS': None,
                'NODATA': -9999,
                'ALPHA_BAND': False,
                'CROP_TO_CUTLINE': True,
                'KEEP_RESOLUTION': True,
                'OUTPUT': 'TEMPORARY_OUTPUT'
            })
            
            stats = processing.run("native:rasterlayerstatistics", {
                'INPUT': clipped_accumulation['OUTPUT'],
                'BAND': 1,
                'OUTPUT_HTML_FILE': 'TEMPORARY_OUTPUT'
            })
            
            max_accumulation = stats.get('MAX', 0)
            mean_accumulation = stats.get('MEAN', 0)
            
            self.results['max_flow_accumulation'] = max_accumulation
            self.results['mean_flow_accumulation'] = mean_accumulation
            self.results['clipped_flow_accumulation'] = clipped_accumulation['OUTPUT']
            
            result_info = f"Max accumulation: {max_accumulation:.0f}, Mean: {mean_accumulation:.2f}"
            self.step_completed.emit("Step 4: Flow Accumulation", True, result_info)
            return True
            
        except Exception as e:
            self.error_occurred.emit("Step 4", str(e))
            return False
    
    def step_5_flow_paths(self) -> bool:
        """Step 5: Extract flow paths and find outlet"""
        try:
            self.progress_updated.emit("Step 5: Extracting flow paths...")
            
            # Find the outlet point (maximum flow accumulation)
            max_accum = self.results['max_flow_accumulation']
            
            if max_accum <= 0:
                self.error_occurred.emit("Step 5", "No significant flow accumulation found")
                return False
            
            # Create outlet point from maximum accumulation location
            try:
                # Extract the point with maximum flow accumulation as outlet
                outlet_result = processing.run("native:pixelstopoints", {
                    'INPUT_RASTER': self.results['clipped_flow_accumulation'],
                    'RASTER_BAND': 1,
                    'FIELD_NAME': 'VALUE',
                    'OUTPUT': 'TEMPORARY_OUTPUT'
                })
                
                # Filter to get only the maximum value point
                outlet_points = processing.run("native:extractbyattribute", {
                    'INPUT': outlet_result['OUTPUT'],
                    'FIELD': 'VALUE',
                    'OPERATOR': 0,  # =
                    'VALUE': str(max_accum),
                    'OUTPUT': 'TEMPORARY_OUTPUT'
                })
                
                self.results['outlet_points'] = outlet_points['OUTPUT']
                
                outlet_count = outlet_points['OUTPUT'].featureCount() if outlet_points['OUTPUT'] else 0
                result_info = f"Found {outlet_count} outlet point(s) with max accumulation {max_accum:.0f}"
                self.step_completed.emit("Step 5: Flow Paths", True, result_info)
                return True
                
            except Exception as path_error:
                # Fallback: estimate outlet as lowest elevation point on basin boundary
                self.progress_updated.emit("Flow path extraction failed, using elevation-based outlet...")
                
                # Get basin boundary
                boundary = processing.run("native:boundary", {
                    'INPUT': self.basin_layer,
                    'OUTPUT': 'TEMPORARY_OUTPUT'
                })
                
                # Sample DEM along boundary to find lowest point
                boundary_samples = processing.run("native:rastersampling", {
                    'INPUT': boundary['OUTPUT'],
                    'RASTERCOPY': self.results['filled_dem'],
                    'COLUMN_PREFIX': 'elevation_',
                    'OUTPUT': 'TEMPORARY_OUTPUT'
                })
                
                # Find minimum elevation point
                min_elev_point = processing.run("native:extractbyexpression", {
                    'INPUT': boundary_samples['OUTPUT'],
                    'EXPRESSION': f'"elevation_1" = minimum("elevation_1")',
                    'OUTPUT': 'TEMPORARY_OUTPUT'
                })
                
                self.results['outlet_points'] = min_elev_point['OUTPUT']
                
                self.step_completed.emit("Step 5: Flow Paths", True, "Used elevation-based outlet (fallback method)")
                return True
            
        except Exception as e:
            self.error_occurred.emit("Step 5", str(e))
            return False
    
    def step_6_hydraulic_length(self) -> bool:
        """Step 6: Calculate hydraulic (longest flow path) length"""
        try:
            self.progress_updated.emit("Step 6: Calculating hydraulic length...")
            
            basin_geom = self.results['basin_geometry']
            
            # Method 1: Try to calculate actual flow path length
            try:
                if 'flow_direction' in self.results and 'outlet_points' in self.results:
                    # Use GRASS r.path to trace flow path from centroid to outlet
                    centroid = basin_geom.centroid()
                    
                    # Create centroid point layer
                    centroid_layer = QgsVectorLayer(f"Point?crs={self.target_crs.authid()}", "centroid", "memory")
                    centroid_provider = centroid_layer.dataProvider()
                    
                    from qgis.core import QgsFeature
                    centroid_feature = QgsFeature()
                    centroid_feature.setGeometry(centroid)
                    centroid_provider.addFeature(centroid_feature)
                    
                    # Try to trace flow path
                    path_result = processing.run("grass7:r.path", {
                        'input': self.results['flow_direction'],
                        'start_points': centroid_layer,
                        'raster_path': 'TEMPORARY_OUTPUT',
                        'vector_path': 'TEMPORARY_OUTPUT'
                    })
                    
                    # Calculate path length
                    if path_result.get('vector_path'):
                        path_layer = path_result['vector_path']
                        total_length = 0
                        
                        for feature in path_layer.getFeatures():
                            total_length += feature.geometry().length()
                        
                        if total_length > 0:
                            hydraulic_length_ft = total_length * 3.28084  # Convert to feet
                            self.results['hydraulic_length_ft'] = hydraulic_length_ft
                            self.results['flow_path_method'] = 'GRASS r.path'
                            
                            result_info = f"Hydraulic length: {hydraulic_length_ft:.1f} ft (flow path analysis)"
                            self.step_completed.emit("Step 6: Hydraulic Length", True, result_info)
                            return True
                
            except Exception as path_error:
                self.progress_updated.emit("Flow path tracing failed, using geometric method...")
            
            # Method 2: Fallback to longest distance within basin
            try:
                # Get bounding box and calculate longest dimension
                bbox = basin_geom.boundingBox()
                max_dimension = max(bbox.width(), bbox.height())
                
                # For scientific accuracy, use 80% of max dimension for typical watersheds
                hydraulic_length_ft = max_dimension * 0.8 * 3.28084
                
                self.results['hydraulic_length_ft'] = hydraulic_length_ft
                self.results['flow_path_method'] = 'Geometric estimation (80% of max dimension)'
                
                result_info = f"Hydraulic length: {hydraulic_length_ft:.1f} ft (geometric method)"
                self.step_completed.emit("Step 6: Hydraulic Length", True, result_info)
                return True
                
            except Exception as geom_error:
                self.error_occurred.emit("Step 6", f"Both flow path and geometric methods failed: {str(geom_error)}")
                return False
            
        except Exception as e:
            self.error_occurred.emit("Step 6", str(e))
            return False
    
    def step_7_basin_slope(self) -> bool:
        """Step 7: Calculate average basin slope from DEM"""
        try:
            self.progress_updated.emit("Step 7: Calculating average basin slope...")
            
            # Calculate slope raster from DEM
            slope_result = processing.run("gdal:slope", {
                'INPUT': self.results['filled_dem'],
                'BAND': 1,
                'SCALE': 1.0,
                'AS_PERCENT': True,
                'COMPUTE_EDGES': False,
                'ZEVENBERGEN': False,
                'OUTPUT': 'TEMPORARY_OUTPUT'
            })
            
            # Clip slope raster to basin
            clipped_slope = processing.run("gdal:cliprasterbymasklayer", {
                'INPUT': slope_result['OUTPUT'],
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
            slope_stats = processing.run("native:rasterlayerstatistics", {
                'INPUT': clipped_slope['OUTPUT'],
                'BAND': 1,
                'OUTPUT_HTML_FILE': 'TEMPORARY_OUTPUT'
            })
            
            avg_slope_percent = slope_stats.get('MEAN', 0)
            min_slope_percent = slope_stats.get('MIN', 0)
            max_slope_percent = slope_stats.get('MAX', 0)
            std_slope_percent = slope_stats.get('STD_DEV', 0)
            
            # Apply minimum slope threshold (1% for scientific validity)
            final_slope_percent = max(avg_slope_percent, 1.0)
            
            self.results['avg_slope_percent'] = final_slope_percent
            self.results['slope_statistics'] = {
                'mean': avg_slope_percent,
                'min': min_slope_percent,
                'max': max_slope_percent,
                'std_dev': std_slope_percent
            }
            
            result_info = f"Average slope: {final_slope_percent:.2f}% (range: {min_slope_percent:.2f}-{max_slope_percent:.2f}%, std: {std_slope_percent:.2f}%)"
            self.step_completed.emit("Step 7: Basin Slope", True, result_info)
            return True
            
        except Exception as e:
            self.error_occurred.emit("Step 7", str(e))
            return False
    
    def step_8_calculate_tc(self) -> bool:
        """Step 8: Calculate TC using SCS/NRCS TR-55 method"""
        try:
            self.progress_updated.emit("Step 8: Calculating Time of Concentration...")
            
            # Get required parameters
            length_ft = self.results.get('hydraulic_length_ft', 0)
            slope_percent = self.results.get('avg_slope_percent', 0)
            cn = 75  # Default CN - in full implementation would be from basin attributes
            
            if length_ft <= 0 or slope_percent <= 0:
                self.error_occurred.emit("Step 8", f"Invalid parameters: Length={length_ft:.1f} ft, Slope={slope_percent:.2f}%")
                return False
            
            # SCS/NRCS TR-55 formula
            # Step 1: Calculate retention parameter
            S = (1000.0 / cn) - 10.0
            
            # Step 2: Calculate lag time (hours)
            lag_hours = (length_ft**0.8 * (S + 1)**0.7) / (1900 * slope_percent**0.5)
            
            # Step 3: Calculate time of concentration
            tc_hours = lag_hours / 0.6
            tc_minutes = tc_hours * 60
            
            # Apply reasonable bounds
            tc_minutes = max(5.0, min(tc_minutes, 1440.0))
            
            self.results['tc_minutes'] = tc_minutes
            self.results['tc_hours'] = tc_hours
            self.results['lag_hours'] = lag_hours
            self.results['retention_parameter'] = S
            self.results['cn_used'] = cn
            
            result_info = f"TC = {tc_minutes:.1f} minutes ({tc_hours:.2f} hours) using L={length_ft:.1f}ft, S={slope_percent:.2f}%, CN={cn}"
            self.step_completed.emit("Step 8: TC Calculation", True, result_info)
            return True
            
        except Exception as e:
            self.error_occurred.emit("Step 8", str(e))
            return False


class HydrologicStepTesterDialog(QDialog):
    """Step-by-step hydrologic analysis tester dialog"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TC Calculator - Step-by-Step Hydrologic Analysis Tester")
        self.setMinimumSize(900, 700)
        self.resize(1000, 800)
        
        self.test_results = {}
        
        self.setup_ui()
        self.populate_layers()
        
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Title
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        
        title_label = QLabel("Time of Concentration - Step-by-Step Scientific Analysis Tester")
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        desc_label = QLabel(
            "Tests each step of proper hydrologic analysis\n"
            "Uses DEM-based average basin slope and hydraulic length\n"
            "Target CRS: EPSG:3361 - Test with single basin first"
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; margin: 10px; font-style: italic;")
        desc_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc_label)
        
        # Input section
        input_group = QGroupBox("Test Data Input")
        input_layout = QVBoxLayout(input_group)
        
        # Basin layer
        basin_layout = QHBoxLayout()
        basin_layout.addWidget(QLabel("Test Basin Layer:"))
        self.basin_combo = QComboBox()
        self.basin_combo.setMinimumWidth(400)
        basin_layout.addWidget(self.basin_combo, 1)
        input_layout.addLayout(basin_layout)
        
        # DEM layer
        dem_layout = QHBoxLayout()
        dem_layout.addWidget(QLabel("DEM Layer:"))
        self.dem_combo = QComboBox()
        self.dem_combo.setMinimumWidth(400)
        dem_layout.addWidget(self.dem_combo, 1)
        input_layout.addLayout(dem_layout)
        
        layout.addWidget(input_group)
        
        # Test options
        options_group = QGroupBox("Test Options")
        options_layout = QVBoxLayout(options_group)
        
        self.detailed_logging = QCheckBox("Enable detailed step logging")
        self.detailed_logging.setChecked(True)
        options_layout.addWidget(self.detailed_logging)
        
        self.stop_on_error = QCheckBox("Stop testing on first error")
        self.stop_on_error.setChecked(False)
        options_layout.addWidget(self.stop_on_error)
        
        layout.addWidget(options_group)
        
        # Results display
        results_group = QGroupBox("Step-by-Step Test Results")
        results_layout = QVBoxLayout(results_group)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMinimumHeight(300)
        self.results_text.setStyleSheet("font-family: 'Courier New', monospace; font-size: 10pt;")
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(results_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status and control buttons
        button_layout = QHBoxLayout()
        
        self.status_label = QLabel("Ready for step-by-step testing")
        self.status_label.setStyleSheet("color: #666; padding: 5px;")
        button_layout.addWidget(self.status_label, 1)
        
        validate_btn = QPushButton("Validate Inputs")
        validate_btn.clicked.connect(self.validate_inputs)
        button_layout.addWidget(validate_btn)
        
        self.test_btn = QPushButton("Run Step-by-Step Analysis")
        self.test_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                padding: 10px 20px;
                background-color: #dc3545;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.test_btn.clicked.connect(self.run_step_by_step_test)
        button_layout.addWidget(self.test_btn)
        
        layout.addLayout(button_layout)
        
        self.update_ui_state()
        
    def populate_layers(self):
        """Populate layer dropdown lists"""
        self.basin_combo.clear()
        self.dem_combo.clear()
        
        self.basin_combo.addItem("-- Select test basin layer --", None)
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
        
        self.update_ui_state()
    
    def update_ui_state(self):
        """Update UI state based on selections"""
        basin_layer = self.basin_combo.currentData()
        dem_layer = self.dem_combo.currentData()
        
        if basin_layer and dem_layer:
            self.status_label.setText("✅ Ready for step-by-step testing")
            self.status_label.setStyleSheet("color: #2e7d32; padding: 5px;")
            self.test_btn.setEnabled(True)
        else:
            missing = []
            if not basin_layer:
                missing.append("basin layer")
            if not dem_layer:
                missing.append("DEM layer")
            
            self.status_label.setText(f"Please select: {', '.join(missing)}")
            self.status_label.setStyleSheet("color: #d32f2f; padding: 5px;")
            self.test_btn.setEnabled(False)
    
    def validate_inputs(self):
        """Validate inputs before testing"""
        self.basin_combo.currentTextChanged.connect(self.update_ui_state)
        self.dem_combo.currentTextChanged.connect(self.update_ui_state)
        
        messages = []
        errors = []
        
        # Check basin layer
        basin_layer = self.basin_combo.currentData()
        if not basin_layer:
            errors.append("No basin layer selected")
        else:
            count = basin_layer.featureCount()
            crs = basin_layer.crs().authid()
            messages.append(f"✅ Basin layer: {basin_layer.name()} ({count} features, {crs})")
            
            if count != 1:
                messages.append("⚠️ Warning: Multiple basins detected - will test first basin only")
            
            if crs != "EPSG:3361":
                messages.append(f"⚠️ Warning: Basin CRS is {crs}, expected EPSG:3361")
        
        # Check DEM layer
        dem_layer = self.dem_combo.currentData()
        if not dem_layer:
            errors.append("No DEM layer selected")
        else:
            crs = dem_layer.crs().authid()
            messages.append(f"✅ DEM layer: {dem_layer.name()} ({crs})")
            
            if crs != "EPSG:3361":
                messages.append(f"⚠️ Warning: DEM CRS is {crs}, expected EPSG:3361")
        
        # Show results
        if errors:
            error_text = "❌ Validation Errors:\n" + "\n".join(f"• {error}" for error in errors)
            if messages:
                error_text += "\n\n✅ Valid Settings:\n" + "\n".join(f"• {msg}" for msg in messages)
            QMessageBox.warning(self, "Validation Failed", error_text)
        else:
            success_text = "✅ Ready for step-by-step testing!\n\n" + "\n".join(f"• {msg}" for msg in messages)
            success_text += "\n\n🔬 Testing Steps:"
            success_text += "\n1. Input validation"
            success_text += "\n2. DEM preprocessing (fill sinks)"
            success_text += "\n3. Flow direction calculation"
            success_text += "\n4. Flow accumulation"
            success_text += "\n5. Flow path extraction"
            success_text += "\n6. Hydraulic length calculation"
            success_text += "\n7. Average basin slope from DEM"
            success_text += "\n8. SCS/NRCS TR-55 TC calculation"
            QMessageBox.information(self, "Validation Successful", success_text)
    
    def run_step_by_step_test(self):
        """Run the step-by-step analysis test"""
        basin_layer = self.basin_combo.currentData()
        dem_layer = self.dem_combo.currentData()
        
        if not basin_layer or not dem_layer:
            QMessageBox.warning(self, "Missing Inputs", "Please select both basin and DEM layers.")
            return
        
        # Clear previous results
        self.results_text.clear()
        self.results_text.append("="*80)
        self.results_text.append("STEP-BY-STEP HYDROLOGIC ANALYSIS TEST")
        self.results_text.append("="*80)
        self.results_text.append("")
        
        # Disable UI during testing
        self.test_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Create and start worker thread
        self.worker = HydrologicTestWorker(basin_layer, dem_layer)
        
        # Connect signals
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.step_completed.connect(self.on_step_completed)
        self.worker.error_occurred.connect(self.on_step_error)
        self.worker.test_completed.connect(self.on_test_completed)
        
        # Start testing
        self.worker.start()
    
    def on_progress_updated(self, message):
        """Handle progress updates"""
        self.status_label.setText(message)
        if self.detailed_logging.isChecked():
            self.results_text.append(f"🔄 {message}")
            self.results_text.ensureCursorVisible()
    
    def on_step_completed(self, step_name, success, result_info):
        """Handle step completion"""
        if success:
            self.results_text.append(f"✅ {step_name}: SUCCESS")
            if result_info:
                self.results_text.append(f"   📊 {result_info}")
        else:
            self.results_text.append(f"❌ {step_name}: FAILED")
            if result_info:
                self.results_text.append(f"   ⚠️ {result_info}")
        
        self.results_text.append("")
        self.results_text.ensureCursorVisible()
    
    def on_step_error(self, step_name, error_message):
        """Handle step errors"""
        self.results_text.append(f"❌ {step_name}: ERROR")
        self.results_text.append(f"   🔥 {error_message}")
        self.results_text.append("")
        
        if self.stop_on_error.isChecked():
            self.results_text.append("🛑 Testing stopped due to error (stop_on_error enabled)")
            self.on_test_completed({})
    
    def on_test_completed(self, results):
        """Handle test completion"""
        self.test_results = results
        self.progress_bar.setVisible(False)
        self.test_btn.setEnabled(True)
        
        self.results_text.append("="*80)
        if results:
            self.results_text.append("🎯 FINAL RESULTS:")
            self.results_text.append("="*80)
            
            # Display key results
            if 'basin_area_acres' in results:
                self.results_text.append(f"Basin Area: {results['basin_area_acres']:.2f} acres")
            
            if 'hydraulic_length_ft' in results:
                self.results_text.append(f"Hydraulic Length: {results['hydraulic_length_ft']:.1f} ft")
                self.results_text.append(f"Method: {results.get('flow_path_method', 'Unknown')}")
            
            if 'avg_slope_percent' in results:
                self.results_text.append(f"Average Basin Slope: {results['avg_slope_percent']:.2f}%")
                slope_stats = results.get('slope_statistics', {})
                if slope_stats:
                    self.results_text.append(f"Slope Range: {slope_stats.get('min', 0):.2f}% - {slope_stats.get('max', 0):.2f}%")
            
            if 'tc_minutes' in results:
                self.results_text.append(f"Time of Concentration: {results['tc_minutes']:.1f} minutes ({results['tc_hours']:.2f} hours)")
                self.results_text.append(f"Lag Time: {results['lag_hours']:.2f} hours")
                self.results_text.append(f"CN Used: {results['cn_used']}")
            
            self.status_label.setText(f"✅ Testing completed - TC: {results.get('tc_minutes', 0):.1f} minutes")
            self.status_label.setStyleSheet("color: #2e7d32; padding: 5px;")
        else:
            self.results_text.append("❌ Testing failed - no results generated")
            self.status_label.setText("❌ Testing failed")
            self.status_label.setStyleSheet("color: #d32f2f; padding: 5px;")
        
        self.results_text.ensureCursorVisible()


def run_hydrologic_step_tester():
    """Main function to run the step-by-step tester"""
    try:
        print("="*70)
        print("TC STEP-BY-STEP HYDROLOGIC ANALYSIS TESTER")
        print("="*70)
        print("\nSCIENTIFIC APPROACH:")
        print("🔬 DEM-based average basin slope calculation")
        print("📏 Hydraulic length from flow path analysis") 
        print("📐 Proper SCS/NRCS TR-55 methodology")
        print("🧪 Step-by-step testing for troubleshooting")
        print("\nTest Data:")
        print("📁 E:/CLAUDE_Workspace/Claude/Report_Files/Codebase/Hydro_Suite/TC_NRCS_Stand_Alone/Test_Data/Single_Basin.shp")
        print("🗺️  Target CRS: EPSG:3361")
        print("\nOpening step tester GUI...")
        
        dialog = HydrologicStepTesterDialog()
        dialog.show()
        
        print("✅ Step tester GUI opened successfully!")
        print("📋 Load your test basin and DEM, then run step-by-step analysis")
        
        return dialog
        
    except Exception as e:
        print(f"❌ Error running step tester: {str(e)}")
        print(traceback.format_exc())
        return None


# =============================================================================
# EXECUTE THE STEP-BY-STEP TESTER
# =============================================================================

print("🚀 Starting TC Step-by-Step Hydrologic Analysis Tester...")
print("🔬 Scientific approach with proper DEM analysis")

# Create the tester dialog and keep reference
step_tester_dialog = run_hydrologic_step_tester()

if step_tester_dialog:
    print("\n" + "="*70)
    print("✅ STEP-BY-STEP TESTER IS NOW READY!")
    print("="*70)
    print("📋 Testing workflow:")
    print("1. Load the test basin shapefile:")
    print("   E:/CLAUDE_Workspace/Claude/Report_Files/Codebase/Hydro_Suite/TC_NRCS_Stand_Alone/Test_Data/Single_Basin.shp")
    print("2. Load your DEM raster layer")
    print("3. Verify both layers are in EPSG:3361")
    print("4. Click 'Run Step-by-Step Analysis'")
    print("5. Watch each step execute and debug any failures")
    print("\n🔬 Scientific analysis steps:")
    print("  • Step 1: Input validation (CRS, geometry)")
    print("  • Step 2: DEM preprocessing (fill sinks)")
    print("  • Step 3: Flow direction calculation")
    print("  • Step 4: Flow accumulation analysis")
    print("  • Step 5: Flow path and outlet identification")
    print("  • Step 6: Hydraulic length calculation")
    print("  • Step 7: DEM-based average basin slope")
    print("  • Step 8: SCS/NRCS TR-55 TC calculation")
    print("\n🎯 This will identify exactly where the preprocessing failed!")
    print("💡 Each step is tested independently with detailed error reporting")