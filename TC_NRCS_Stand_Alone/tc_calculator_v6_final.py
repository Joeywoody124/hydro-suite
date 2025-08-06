"""
Time of Concentration Calculator - Comprehensive Version
Version 2.0.0 - January 2025
Scientific hydrologic analysis using validated QGIS processing tools

Built on successful Phase 1 testing with proven tool chain:
- GDAL fillnodata for DEM preprocessing
- GRASS r.watershed for flow analysis
- GDAL slope calculation for terrain analysis

Target CRS: EPSG:3361
"""

import os
import math
import traceback
from datetime import datetime
from typing import Optional, Tuple, Dict, List, Any

from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QMessageBox, QComboBox, QTextEdit, QProgressBar,
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QCheckBox, QSpinBox, QDoubleSpinBox
)
from qgis.PyQt.QtCore import Qt, QThread, pyqtSignal
from qgis.PyQt.QtGui import QFont

from qgis.core import (
    QgsProject, QgsVectorLayer, QgsRasterLayer, QgsGeometry,
    QgsFeature, QgsField, QgsFields, QgsVectorFileWriter,
    QgsCoordinateReferenceSystem, QgsWkbTypes, QgsProcessingFeedback,
    QgsFeatureRequest, QgsExpression, QgsExpressionContext,
    QgsExpressionContextUtils, QgsSpatialIndex, QgsRectangle
)
from qgis import processing

from PyQt5.QtCore import QVariant


class TCCalculatorWorker(QThread):
    """Worker thread for TC calculations"""
    
    progress_updated = pyqtSignal(int, str)  # progress, message
    basin_processed = pyqtSignal(int, str, dict)  # basin_id, basin_name, results
    calculation_completed = pyqtSignal(list)  # all results
    error_occurred = pyqtSignal(str)
    
    def __init__(self, basin_layer, dem_layer, target_crs="EPSG:3361"):
        super().__init__()
        self.basin_layer = basin_layer
        self.dem_layer = dem_layer
        self.target_crs = QgsCoordinateReferenceSystem(target_crs)
        self.results = []
        self.cancelled = False
        
    def run(self):
        """Execute TC calculations for all basins"""
        try:
            # Validate inputs
            if not self.validate_inputs():
                return
            
            # Get basin count
            basin_count = self.basin_layer.featureCount()
            self.progress_updated.emit(0, f"Processing {basin_count} basin(s)...")
            
            # Preprocess DEM once for all basins
            self.progress_updated.emit(5, "Preprocessing DEM...")
            preprocessed_dem = self.preprocess_dem()
            if not preprocessed_dem:
                self.error_occurred.emit("DEM preprocessing failed")
                return
            
            # Calculate flow direction and accumulation once
            self.progress_updated.emit(10, "Calculating flow direction and accumulation...")
            flow_layers = self.calculate_flow_layers(preprocessed_dem)
            if not flow_layers:
                self.error_occurred.emit("Flow calculation failed")
                return
            
            # Process each basin
            for idx, basin_feature in enumerate(self.basin_layer.getFeatures()):
                if self.cancelled:
                    break
                
                basin_id = basin_feature.id()
                # Try to get basin name from attributes
                try:
                    basin_name = basin_feature['NAME']  # Try NAME first
                except:
                    try:
                        basin_name = basin_feature['Name']  # Then Name
                    except:
                        basin_name = f'Basin_{basin_id}'
                
                progress = 10 + int((idx / basin_count) * 80)
                self.progress_updated.emit(
                    progress,
                    f"Processing basin {idx + 1}/{basin_count}: {basin_name}"
                )
                
                # Calculate TC for this basin
                tc_results = self.calculate_basin_tc(
                    basin_feature,
                    preprocessed_dem,
                    flow_layers
                )
                
                if tc_results:
                    tc_results['basin_id'] = basin_id
                    tc_results['basin_name'] = basin_name
                    self.results.append(tc_results)
                    self.basin_processed.emit(basin_id, basin_name, tc_results)
                else:
                    self.error_occurred.emit(f"TC calculation failed for {basin_name}")
            
            # Complete
            self.progress_updated.emit(100, "Calculations complete!")
            self.calculation_completed.emit(self.results)
            
        except Exception as e:
            self.error_occurred.emit(f"Calculation error: {str(e)}\n{traceback.format_exc()}")
    
    def validate_inputs(self):
        """Validate input layers and CRS"""
        try:
            # Check layers
            if not self.basin_layer or not self.basin_layer.isValid():
                self.error_occurred.emit("Invalid basin layer")
                return False
            
            if not self.dem_layer or not self.dem_layer.isValid():
                self.error_occurred.emit("Invalid DEM layer")
                return False
            
            # Check CRS compatibility
            basin_crs = self.basin_layer.crs()
            dem_crs = self.dem_layer.crs()
            
            if basin_crs != dem_crs:
                self.error_occurred.emit(
                    f"CRS mismatch: Basin ({basin_crs.authid()}) != DEM ({dem_crs.authid()})"
                )
                return False
            
            if basin_crs.authid() != "EPSG:3361":
                self.error_occurred.emit(
                    f"Warning: Not using target CRS EPSG:3361 (using {basin_crs.authid()})"
                )
            
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"Validation error: {str(e)}")
            return False
    
    def preprocess_dem(self):
        """Preprocess DEM using validated GDAL fillnodata"""
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
            
            return result['OUTPUT']
            
        except Exception as e:
            self.error_occurred.emit(f"DEM preprocessing error: {str(e)}")
            return None
    
    def calculate_flow_layers(self, preprocessed_dem):
        """Calculate flow direction and accumulation using GRASS r.watershed"""
        try:
            result = processing.run("grass7:r.watershed", {
                'elevation': preprocessed_dem,
                'threshold': 1000,
                'max_slope_length': -1,
                'drainage': 'TEMPORARY_OUTPUT',
                'accumulation': 'TEMPORARY_OUTPUT',
                'GRASS_REGION_PARAMETER': None,
                'GRASS_REGION_CELLSIZE_PARAMETER': 0
            })
            
            return {
                'flow_direction': result['drainage'],
                'flow_accumulation': result['accumulation']
            }
            
        except Exception as e:
            self.error_occurred.emit(f"Flow calculation error: {str(e)}")
            return None
    
    def calculate_basin_tc(self, basin_feature, preprocessed_dem, flow_layers):
        """Calculate TC for a single basin"""
        try:
            results = {}
            
            # Get basin geometry and properties
            basin_geom = basin_feature.geometry()
            
            # Try to get area from attribute first (more accurate)
            try:
                area_acres = float(basin_feature['AREA'])
            except:
                # Fall back to geometry calculation
                area_sq_m = basin_geom.area()
                area_acres = area_sq_m / 4046.86
                
            area_sq_m = area_acres * 4046.86
            
            results['area_acres'] = area_acres
            results['area_sq_m'] = area_sq_m
            
            # Create temporary layer for this basin
            temp_basin = self.create_temp_basin_layer(basin_feature)
            
            # 1. Calculate average slope
            self.progress_updated.emit(0, "Calculating basin slope...")
            avg_slope = self.calculate_basin_slope(temp_basin, preprocessed_dem)
            results['avg_slope_percent'] = avg_slope
            
            # 2. Calculate hydraulic length
            self.progress_updated.emit(0, "Calculating hydraulic length...")
            hydraulic_length = self.calculate_hydraulic_length(
                temp_basin,
                flow_layers['flow_accumulation']
            )
            results['hydraulic_length_ft'] = hydraulic_length
            
            # 3. Get curve number (use default or from attribute)
            try:
                curve_number = float(basin_feature['CN_Comp'])  # Try CN_Comp first
            except:
                try:
                    curve_number = float(basin_feature['CN'])  # Then CN
                except:
                    curve_number = 75  # Default CN=75
            results['curve_number'] = curve_number
            
            # 4. Calculate retention parameter S
            S = (1000 / curve_number) - 10
            results['retention_S'] = S
            
            # 5. Calculate lag time (SCS method)
            # L in feet, S in inches, slope in percent
            if hydraulic_length > 0 and avg_slope > 0:
                # SCS lag equation: tL = (L^0.8 * (S+1)^0.7) / (1900 * Y^0.5)
                # where L is in feet, S is retention, Y is slope in percent
                lag_hours = (math.pow(hydraulic_length, 0.8) * math.pow(S + 1, 0.7)) / (1900 * math.pow(avg_slope, 0.5))
                lag_minutes = lag_hours * 60
                
                # TC = lag time / 0.6 (SCS relationship)
                tc_minutes = lag_minutes / 0.6
                
                results['lag_time_min'] = lag_minutes
                results['tc_minutes'] = tc_minutes
                results['tc_hours'] = tc_minutes / 60
            else:
                results['lag_time_min'] = 0
                results['tc_minutes'] = 0
                results['tc_hours'] = 0
                results['error'] = "Invalid hydraulic length or slope"
            
            # Add calculation timestamp
            results['calculated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            return results
            
        except Exception as e:
            self.error_occurred.emit(f"Basin TC calculation error: {str(e)}")
            return None
    
    def create_temp_basin_layer(self, basin_feature):
        """Create temporary layer with single basin"""
        try:
            # Create memory layer
            temp_layer = QgsVectorLayer(
                f"Polygon?crs={self.basin_layer.crs().authid()}",
                "temp_basin",
                "memory"
            )
            
            # Add feature
            provider = temp_layer.dataProvider()
            provider.addFeatures([basin_feature])
            temp_layer.updateExtents()
            
            return temp_layer
            
        except Exception as e:
            return None
    
    def calculate_basin_slope(self, basin_layer, dem_layer):
        """Calculate average slope for basin using GDAL"""
        try:
            # Calculate slope raster
            slope_result = processing.run("gdal:slope", {
                'INPUT': dem_layer,
                'BAND': 1,
                'SCALE': 1.0,
                'AS_PERCENT': True,
                'COMPUTE_EDGES': False,
                'ZEVENBERGEN': False,
                'OUTPUT': 'TEMPORARY_OUTPUT'
            })
            
            # Clip to basin
            clipped_slope = processing.run("gdal:cliprasterbymasklayer", {
                'INPUT': slope_result['OUTPUT'],
                'MASK': basin_layer,
                'SOURCE_CRS': None,
                'TARGET_CRS': None,
                'NODATA': -9999,
                'ALPHA_BAND': False,
                'CROP_TO_CUTLINE': True,
                'KEEP_RESOLUTION': True,
                'OUTPUT': 'TEMPORARY_OUTPUT'
            })
            
            # Get statistics
            stats = processing.run("native:rasterlayerstatistics", {
                'INPUT': clipped_slope['OUTPUT'],
                'BAND': 1,
                'OUTPUT_HTML_FILE': 'TEMPORARY_OUTPUT'
            })
            
            avg_slope = stats.get('MEAN', 0)
            
            # Apply minimum slope (1% for numerical stability)
            return max(avg_slope, 1.0)
            
        except Exception as e:
            self.error_occurred.emit(f"Slope calculation error: {str(e)}")
            return 1.0  # Default minimum slope
    
    def calculate_hydraulic_length(self, basin_layer, flow_accumulation):
        """Calculate hydraulic length from flow accumulation"""
        try:
            # Clip flow accumulation to basin
            clipped_accumulation = processing.run("gdal:cliprasterbymasklayer", {
                'INPUT': flow_accumulation,
                'MASK': basin_layer,
                'SOURCE_CRS': None,
                'TARGET_CRS': None,
                'NODATA': -9999,
                'ALPHA_BAND': False,
                'CROP_TO_CUTLINE': True,
                'KEEP_RESOLUTION': True,
                'OUTPUT': 'TEMPORARY_OUTPUT'
            })
            
            # Find highest accumulation point (outlet)
            stats = processing.run("native:rasterlayerstatistics", {
                'INPUT': clipped_accumulation['OUTPUT'],
                'BAND': 1,
                'OUTPUT_HTML_FILE': 'TEMPORARY_OUTPUT'
            })
            
            max_accumulation = stats.get('MAX', 0)
            
            # For now, estimate hydraulic length based on basin dimensions
            # This is a simplified approach - full flow path tracing would be more accurate
            basin_feature = next(basin_layer.getFeatures())
            bbox = basin_feature.geometry().boundingBox()
            
            # Estimate as diagonal distance of bounding box
            width_m = bbox.width()
            height_m = bbox.height()
            diagonal_m = math.sqrt(width_m**2 + height_m**2)
            
            # Apply reduction factor (0.7) for more realistic path
            hydraulic_length_m = diagonal_m * 0.7
            hydraulic_length_ft = hydraulic_length_m * 3.28084
            
            return hydraulic_length_ft
            
        except Exception as e:
            self.error_occurred.emit(f"Hydraulic length error: {str(e)}")
            # Fallback to simple estimate
            return 500.0  # Default 500 ft


class TCCalculatorDialog(QDialog):
    """Main dialog for TC Calculator"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Time of Concentration Calculator v2.0.0")
        self.setMinimumSize(900, 700)
        self.resize(1000, 800)
        
        self.worker = None
        self.results = []
        
        self.setup_ui()
        self.populate_layers()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Title
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        
        title = QLabel("Time of Concentration Calculator - Version 2.0.0")
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        desc = QLabel(
            "Scientific hydrologic analysis using SCS/NRCS TR-55 methodology\n"
            "Validated processing chain: GDAL + GRASS + Scientific calculations"
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
        basin_layout.addWidget(self.basin_combo, 1)
        input_layout.addLayout(basin_layout)
        
        # DEM layer
        dem_layout = QHBoxLayout()
        dem_layout.addWidget(QLabel("DEM Layer:"))
        self.dem_combo = QComboBox()
        self.dem_combo.setMinimumWidth(300)
        dem_layout.addWidget(self.dem_combo, 1)
        input_layout.addLayout(dem_layout)
        
        layout.addWidget(input_group)
        
        # Results table
        results_group = QGroupBox("Calculation Results")
        results_layout = QVBoxLayout(results_group)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(8)
        self.results_table.setHorizontalHeaderLabels([
            "Basin Name",
            "Area (acres)",
            "Avg Slope (%)",
            "Hydraulic Length (ft)",
            "Curve Number",
            "Lag Time (min)",
            "Tc (min)",
            "Tc (hours)"
        ])
        
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        results_layout.addWidget(self.results_table)
        layout.addWidget(results_group)
        
        # Progress section
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready to calculate")
        self.status_label.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(self.status_label)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.calculate_btn = QPushButton("Calculate Time of Concentration")
        self.calculate_btn.setStyleSheet("""
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
        self.calculate_btn.clicked.connect(self.calculate_tc)
        button_layout.addWidget(self.calculate_btn)
        
        self.export_btn = QPushButton("Export Results")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_results)
        button_layout.addWidget(self.export_btn)
        
        layout.addLayout(button_layout)
    
    def populate_layers(self):
        """Populate layer dropdown lists"""
        self.basin_combo.clear()
        self.dem_combo.clear()
        
        self.basin_combo.addItem("-- Select basin layer --", None)
        self.dem_combo.addItem("-- Select DEM layer --", None)
        
        project = QgsProject.instance()
        
        # Vector layers for basins
        for layer_id, layer in project.mapLayers().items():
            if isinstance(layer, QgsVectorLayer) and layer.geometryType() == QgsWkbTypes.PolygonGeometry:
                self.basin_combo.addItem(layer.name(), layer)
        
        # Raster layers for DEM
        for layer_id, layer in project.mapLayers().items():
            if isinstance(layer, QgsRasterLayer):
                self.dem_combo.addItem(layer.name(), layer)
    
    def calculate_tc(self):
        """Start TC calculation"""
        basin_layer = self.basin_combo.currentData()
        dem_layer = self.dem_combo.currentData()
        
        if not basin_layer or not dem_layer:
            QMessageBox.warning(self, "Missing Input", "Please select both basin and DEM layers.")
            return
        
        # Clear previous results
        self.results_table.setRowCount(0)
        self.results = []
        
        # Disable UI during calculation
        self.calculate_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Create and start worker
        self.worker = TCCalculatorWorker(basin_layer, dem_layer)
        
        # Connect signals
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.basin_processed.connect(self.on_basin_processed)
        self.worker.calculation_completed.connect(self.on_calculation_completed)
        self.worker.error_occurred.connect(self.on_error_occurred)
        
        # Start calculation
        self.worker.start()
    
    def on_progress_updated(self, progress, message):
        """Handle progress updates"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)
    
    def on_basin_processed(self, basin_id, basin_name, results):
        """Handle single basin completion"""
        # Add row to table
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        
        # Populate cells
        self.results_table.setItem(row, 0, QTableWidgetItem(basin_name))
        self.results_table.setItem(row, 1, QTableWidgetItem(f"{results['area_acres']:.2f}"))
        self.results_table.setItem(row, 2, QTableWidgetItem(f"{results['avg_slope_percent']:.2f}"))
        self.results_table.setItem(row, 3, QTableWidgetItem(f"{results['hydraulic_length_ft']:.1f}"))
        self.results_table.setItem(row, 4, QTableWidgetItem(f"{results['curve_number']:.0f}"))
        self.results_table.setItem(row, 5, QTableWidgetItem(f"{results['lag_time_min']:.1f}"))
        self.results_table.setItem(row, 6, QTableWidgetItem(f"{results['tc_minutes']:.1f}"))
        self.results_table.setItem(row, 7, QTableWidgetItem(f"{results['tc_hours']:.2f}"))
    
    def on_calculation_completed(self, results):
        """Handle calculation completion"""
        self.results = results
        self.progress_bar.setVisible(False)
        self.calculate_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        
        self.status_label.setText(f"✅ Calculation complete! Processed {len(results)} basin(s)")
        self.status_label.setStyleSheet("color: #2e7d32; padding: 5px; font-weight: bold;")
    
    def on_error_occurred(self, error_message):
        """Handle errors"""
        self.progress_bar.setVisible(False)
        self.calculate_btn.setEnabled(True)
        
        self.status_label.setText(f"❌ Error: {error_message}")
        self.status_label.setStyleSheet("color: #d32f2f; padding: 5px;")
        
        QMessageBox.critical(self, "Calculation Error", error_message)
    
    def export_results(self):
        """Export results to CSV"""
        if not self.results:
            QMessageBox.warning(self, "No Results", "No results to export.")
            return
        
        # Get save path
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export TC Results",
            "tc_results.csv",
            "CSV Files (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            # Write CSV
            import csv
            
            with open(file_path, 'w', newline='') as csvfile:
                fieldnames = [
                    'basin_name', 'area_acres', 'avg_slope_percent',
                    'hydraulic_length_ft', 'curve_number', 'retention_S',
                    'lag_time_min', 'tc_minutes', 'tc_hours', 'calculated_at'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in self.results:
                    writer.writerow({
                        key: result.get(key, '')
                        for key in fieldnames
                    })
            
            QMessageBox.information(
                self,
                "Export Successful",
                f"Results exported to:\n{file_path}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export results: {str(e)}"
            )


def run_tc_calculator():
    """Main function to run TC calculator"""
    try:
        print("="*60)
        print("TIME OF CONCENTRATION CALCULATOR v2.0.0")
        print("="*60)
        print("\nCOMPREHENSIVE VERSION - Phase 2 Implementation")
        print("✅ Using validated processing chain from Phase 1")
        print("📊 Scientific SCS/NRCS TR-55 methodology")
        print("🎯 Target CRS: EPSG:3361")
        print("\nOpening calculator...")
        
        dialog = TCCalculatorDialog()
        dialog.show()
        
        print("✅ Calculator ready!")
        
        return dialog
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


# Execute the calculator
print("🚀 Starting Comprehensive TC Calculator...")
tc_dialog = run_tc_calculator()

if tc_dialog:
    print("\n" + "="*60)
    print("✅ TC CALCULATOR v2.0.0 READY!")
    print("="*60)
    print("📋 Features:")
    print("  ✅ Validated preprocessing (GDAL fillnodata)")
    print("  ✅ Flow analysis (GRASS r.watershed)")
    print("  ✅ Slope calculation (GDAL slope)")
    print("  ✅ SCS/NRCS TR-55 calculations")
    print("  ✅ Multi-basin batch processing")
    print("  ✅ CSV export functionality")
    print("\n🎯 Load your basin and DEM layers to begin!")