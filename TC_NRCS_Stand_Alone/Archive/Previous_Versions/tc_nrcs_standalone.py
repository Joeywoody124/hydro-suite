"""
Time of Concentration Calculator - SCS/NRCS Method
Standalone QGIS Python tool for calculating TC using SCS/NRCS TR-55 method
Version 1.0 - January 2025

This tool addresses the fundamental issues in the original Hydro Suite TC Calculator:
1. Proper raster layer selection for DEM
2. Correct SCS/NRCS TR-55 formula implementation 
3. DEM-based slope calculation using zonal statistics
4. Standalone operation without module dependencies

Usage: Copy and paste this entire script into QGIS Python Console
"""

import os
import csv
import math
import traceback
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QDialog, QComboBox, QLineEdit, QTextEdit,
    QProgressBar, QGroupBox, QCheckBox, QDoubleSpinBox,
    QSpinBox, QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget, QFrame
)
from qgis.PyQt.QtCore import Qt, QThread, pyqtSignal, QTimer
from qgis.PyQt.QtGui import QFont

from qgis.core import (
    QgsProject, QgsVectorLayer, QgsRasterLayer, QgsField, QgsFeature,
    QgsGeometry, QgsPointXY, QgsCoordinateReferenceSystem, QgsWkbTypes,
    QgsVectorFileWriter, QgsProcessingFeedback, Qgis, QgsMessageLog
)
from qgis.PyQt.QtCore import QVariant
from qgis import processing


class TCCalculationWorker(QThread):
    """Worker thread for TC calculations to prevent GUI freezing"""
    
    progress_updated = pyqtSignal(int, str)
    calculation_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, subbasin_layer, subbasin_field, cn_field, dem_layer, 
                 flow_length_field=None, default_cn=75, min_slope=0.5):
        super().__init__()
        self.subbasin_layer = subbasin_layer
        self.subbasin_field = subbasin_field
        self.cn_field = cn_field
        self.dem_layer = dem_layer
        self.flow_length_field = flow_length_field
        self.default_cn = default_cn
        self.min_slope = min_slope
        
    def run(self):
        """Execute TC calculations in background thread"""
        try:
            results = {}
            total_features = self.subbasin_layer.featureCount()
            
            self.progress_updated.emit(5, "Preparing slope analysis...")
            
            # Get DEM statistics for all subbasins at once using zonal statistics
            slope_data = self.calculate_slopes_batch(self.subbasin_layer, self.dem_layer)
            
            self.progress_updated.emit(20, f"Processing {total_features} subbasins...")
            
            for i, feature in enumerate(self.subbasin_layer.getFeatures()):
                try:
                    subbasin_id = feature[self.subbasin_field] if self.subbasin_field else f"Basin_{feature.id()}"
                    
                    # Get CN value
                    cn_value = self.get_cn_value(feature)
                    
                    # Get flow length
                    length_ft = self.get_flow_length(feature)
                    
                    # Get slope from batch calculation
                    slope_percent = slope_data.get(feature.id(), self.min_slope)
                    
                    # Calculate TC using SCS/NRCS TR-55 method
                    tc_minutes = self.calculate_tc_scs_tr55(length_ft, slope_percent, cn_value)
                    
                    results[subbasin_id] = {
                        'feature_id': feature.id(),
                        'cn_value': cn_value,
                        'length_ft': length_ft,
                        'slope_percent': slope_percent,
                        'tc_minutes': tc_minutes,
                        'tc_hours': tc_minutes / 60.0
                    }
                    
                except Exception as e:
                    self.progress_updated.emit(-1, f"Error processing basin {subbasin_id}: {str(e)}")
                    continue
                
                # Update progress
                progress = 20 + int((i + 1) / total_features * 70)
                self.progress_updated.emit(progress, f"Processed {i + 1}/{total_features} subbasins")
            
            self.progress_updated.emit(95, "Finalizing results...")
            self.calculation_completed.emit(results)
            
        except Exception as e:
            self.error_occurred.emit(f"Calculation error: {str(e)}\n{traceback.format_exc()}")
    
    def calculate_slopes_batch(self, subbasin_layer, dem_layer):
        """Calculate slopes for all subbasins using zonal statistics"""
        self.progress_updated.emit(10, "Running zonal statistics on DEM...")
        
        try:
            # Use QGIS processing algorithm for zonal statistics
            result = processing.run("native:zonalstatisticsfb", {
                'INPUT': dem_layer,
                'ZONES': subbasin_layer,
                'ZONES_BAND': 1,
                'STATISTICS': [2, 3],  # Min (2) and Max (3) elevation
                'OUTPUT': 'TEMPORARY_OUTPUT'
            })
            
            temp_layer = result['OUTPUT']
            slopes = {}
            
            # Calculate slope for each feature
            for feature in temp_layer.getFeatures():
                try:
                    min_elev = feature['_min']
                    max_elev = feature['_max']
                    
                    if min_elev is not None and max_elev is not None and min_elev != max_elev:
                        # Get geometry to calculate flow length for slope calculation
                        geom = feature.geometry()
                        bbox = geom.boundingBox()
                        
                        # Estimate flow length as diagonal of bounding box
                        length_m = math.sqrt(bbox.width()**2 + bbox.height()**2)
                        
                        if length_m > 0:
                            elevation_diff = abs(max_elev - min_elev)
                            slope_percent = (elevation_diff / length_m) * 100
                            
                            # Apply minimum slope threshold
                            slope_percent = max(slope_percent, self.min_slope)
                        else:
                            slope_percent = self.min_slope
                    else:
                        slope_percent = self.min_slope
                        
                    slopes[feature.id()] = slope_percent
                    
                except Exception as e:
                    slopes[feature.id()] = self.min_slope
                    self.progress_updated.emit(-1, f"Warning: Using default slope for feature {feature.id()}")
            
            return slopes
            
        except Exception as e:
            self.progress_updated.emit(-1, f"Error in slope calculation: {str(e)}")
            # Return default slopes for all features
            slopes = {}
            for feature in subbasin_layer.getFeatures():
                slopes[feature.id()] = self.min_slope
            return slopes
    
    def get_cn_value(self, feature):
        """Get curve number value from feature"""
        try:
            if self.cn_field and feature[self.cn_field] is not None:
                cn_value = float(feature[self.cn_field])
                # Validate CN range
                if 30 <= cn_value <= 98:
                    return cn_value
                else:
                    self.progress_updated.emit(-1, f"Warning: CN value {cn_value} out of range, using default")
            return self.default_cn
        except:
            return self.default_cn
    
    def get_flow_length(self, feature):
        """Get flow length from feature or estimate from geometry"""
        try:
            # Try to get from field first
            if self.flow_length_field and feature[self.flow_length_field] is not None:
                length_value = float(feature[self.flow_length_field])
                if length_value > 0:
                    return length_value
            
            # Estimate from geometry - use longest dimension of bounding box
            geom = feature.geometry()
            bbox = geom.boundingBox()
            
            # Convert to feet (assuming input is in meters)
            length_m = max(bbox.width(), bbox.height())
            length_ft = length_m * 3.28084
            
            return max(length_ft, 100.0)  # Minimum 100 ft
            
        except Exception as e:
            return 1000.0  # Default 1000 ft
    
    def calculate_tc_scs_tr55(self, length_ft, slope_percent, cn):
        """
        Calculate Time of Concentration using SCS/NRCS TR-55 method
        
        This is the CORRECT formula from TR-55, not the simplified version
        in the original code.
        
        Formula:
        1. Calculate retention parameter: S = (1000/CN) - 10
        2. Calculate lag time: L = (l^0.8 * (S + 1)^0.7) / (1900 * Y^0.5)
        3. Calculate TC: Tc = L / 0.6
        
        Where:
        - l = flow length (ft)
        - S = retention parameter
        - Y = average watershed slope (%)
        - L = lag time (hours)
        - Tc = time of concentration (hours)
        """
        try:
            # Validate inputs
            if length_ft <= 0 or slope_percent <= 0 or cn <= 0:
                return 0.0
            
            # Ensure CN is in valid range
            cn = max(30, min(98, cn))
            
            # Step 1: Calculate retention parameter
            S = (1000.0 / cn) - 10.0
            
            # Step 2: Calculate lag time in hours (TR-55 equation)
            lag_hours = (length_ft**0.8 * (S + 1)**0.7) / (1900 * slope_percent**0.5)
            
            # Step 3: Convert lag to time of concentration
            # TR-55 uses Tc = Lag / 0.6 (or Tc = 1.67 * Lag)
            tc_hours = lag_hours / 0.6
            
            # Convert to minutes
            tc_minutes = tc_hours * 60
            
            # Apply reasonable bounds (5 minutes to 24 hours)
            tc_minutes = max(5.0, min(tc_minutes, 1440.0))
            
            return tc_minutes
            
        except Exception as e:
            # Return a reasonable default if calculation fails
            return 60.0  # 1 hour default


class TCCalculatorDialog(QDialog):
    """Main dialog for Time of Concentration Calculator"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Time of Concentration Calculator - SCS/NRCS TR-55 Method")
        self.setMinimumSize(800, 600)
        self.resize(900, 700)
        
        # Results storage
        self.results = {}
        self.output_dir = ""
        
        self.setup_ui()
        self.populate_layers()
        
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Title and description
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        
        title_label = QLabel("Time of Concentration Calculator")
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        desc_label = QLabel(
            "Calculate Time of Concentration using SCS/NRCS TR-55 method with actual CN values and DEM slope analysis"
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; margin: 10px; font-style: italic;")
        desc_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc_label)
        
        # Create tab widget
        tab_widget = QTabWidget()
        
        # Configuration tab
        config_tab = self.create_config_tab()
        tab_widget.addTab(config_tab, "Configuration")
        
        # Results tab
        results_tab = self.create_results_tab()
        tab_widget.addTab(results_tab, "Results")
        
        layout.addWidget(tab_widget)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(self.status_label)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        validate_btn = QPushButton("Validate Inputs")
        validate_btn.clicked.connect(self.validate_inputs)
        button_layout.addWidget(validate_btn)
        
        button_layout.addStretch()
        
        self.calculate_btn = QPushButton("Calculate Time of Concentration")
        self.calculate_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                padding: 10px 20px;
                background-color: #17a2b8;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.calculate_btn.clicked.connect(self.run_calculation)
        button_layout.addWidget(self.calculate_btn)
        
        layout.addLayout(button_layout)
        
    def create_config_tab(self):
        """Create configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Input Data Section
        input_group = QGroupBox("Input Data")
        input_layout = QVBoxLayout(input_group)
        
        # Subbasin layer selection
        subbasin_layout = QHBoxLayout()
        subbasin_layout.addWidget(QLabel("Subbasin Layer:"))
        self.subbasin_combo = QComboBox()
        self.subbasin_combo.setMinimumWidth(300)
        self.subbasin_combo.currentTextChanged.connect(self.on_subbasin_layer_changed)
        subbasin_layout.addWidget(self.subbasin_combo, 1)
        input_layout.addLayout(subbasin_layout)
        
        # Subbasin ID field
        id_layout = QHBoxLayout()
        id_layout.addWidget(QLabel("Basin ID Field:"))
        self.id_field_combo = QComboBox()
        self.id_field_combo.setMinimumWidth(200)
        id_layout.addWidget(self.id_field_combo, 1)
        id_layout.addStretch()
        input_layout.addLayout(id_layout)
        
        # CN field selection
        cn_layout = QHBoxLayout()
        cn_layout.addWidget(QLabel("CN Field:"))
        self.cn_field_combo = QComboBox()
        self.cn_field_combo.setMinimumWidth(200)
        cn_layout.addWidget(self.cn_field_combo, 1)
        cn_layout.addStretch()
        input_layout.addLayout(cn_layout)
        
        # Flow length field (optional)
        length_layout = QHBoxLayout()
        length_layout.addWidget(QLabel("Flow Length Field (optional):"))
        self.length_field_combo = QComboBox()
        self.length_field_combo.setMinimumWidth(200)
        length_layout.addWidget(self.length_field_combo, 1)
        length_layout.addStretch()
        input_layout.addLayout(length_layout)
        
        # DEM layer selection
        dem_layout = QHBoxLayout()
        dem_layout.addWidget(QLabel("DEM Layer:"))
        self.dem_combo = QComboBox()
        self.dem_combo.setMinimumWidth(300)
        dem_layout.addWidget(self.dem_combo, 1)
        input_layout.addLayout(dem_layout)
        
        layout.addWidget(input_group)
        
        # Parameters Section
        params_group = QGroupBox("Parameters")
        params_layout = QVBoxLayout(params_group)
        
        # Default CN value
        cn_default_layout = QHBoxLayout()
        cn_default_layout.addWidget(QLabel("Default CN (if field missing):"))
        self.default_cn_spin = QSpinBox()
        self.default_cn_spin.setRange(30, 98)
        self.default_cn_spin.setValue(75)
        cn_default_layout.addWidget(self.default_cn_spin)
        cn_default_layout.addStretch()
        params_layout.addLayout(cn_default_layout)
        
        # Minimum slope
        slope_layout = QHBoxLayout()
        slope_layout.addWidget(QLabel("Minimum Slope (%):"))
        self.min_slope_spin = QDoubleSpinBox()
        self.min_slope_spin.setRange(0.1, 10.0)
        self.min_slope_spin.setValue(0.5)
        self.min_slope_spin.setSingleStep(0.1)
        self.min_slope_spin.setDecimals(2)
        slope_layout.addWidget(self.min_slope_spin)
        slope_layout.addStretch()
        params_layout.addLayout(slope_layout)
        
        layout.addWidget(params_group)
        
        # Output Section
        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout(output_group)
        
        # Output directory
        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(QLabel("Output Directory:"))
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("Select output directory...")
        output_dir_layout.addWidget(self.output_dir_edit, 1)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_output_dir)
        output_dir_layout.addWidget(browse_btn)
        
        output_layout.addLayout(output_dir_layout)
        
        layout.addWidget(output_group)
        
        layout.addStretch()
        return widget
    
    def create_results_tab(self):
        """Create results display tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setAlternatingRowColors(True)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.results_table)
        
        # Summary statistics
        self.summary_label = QLabel("Run calculation to see results...")
        self.summary_label.setStyleSheet("color: #666; font-style: italic; padding: 10px;")
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)
        
        return widget
    
    def populate_layers(self):
        """Populate layer dropdown lists"""
        # Clear existing items
        self.subbasin_combo.clear()
        self.dem_combo.clear()
        
        # Add default items
        self.subbasin_combo.addItem("-- Select subbasin layer --", None)
        self.dem_combo.addItem("-- Select DEM layer --", None)
        
        # Get layers from project
        project = QgsProject.instance()
        
        # Vector layers for subbasins
        for layer_id, layer in project.mapLayers().items():
            if isinstance(layer, QgsVectorLayer) and layer.geometryType() == QgsWkbTypes.PolygonGeometry:
                self.subbasin_combo.addItem(layer.name(), layer)
        
        # Raster layers for DEM - THIS IS THE KEY FIX
        for layer_id, layer in project.mapLayers().items():
            if isinstance(layer, QgsRasterLayer):
                self.dem_combo.addItem(layer.name(), layer)
        
        self.update_status()
    
    def on_subbasin_layer_changed(self):
        """Handle subbasin layer selection change"""
        layer = self.subbasin_combo.currentData()
        
        # Clear field combos
        self.id_field_combo.clear()
        self.cn_field_combo.clear()
        self.length_field_combo.clear()
        
        if layer and isinstance(layer, QgsVectorLayer):
            # Populate field combos
            self.id_field_combo.addItem("-- Select ID field --", None)
            self.cn_field_combo.addItem("-- Select CN field --", None)
            self.length_field_combo.addItem("-- No flow length field --", None)
            
            for field in layer.fields():
                field_name = field.name()
                self.id_field_combo.addItem(field_name, field_name)
                self.cn_field_combo.addItem(field_name, field_name)
                self.length_field_combo.addItem(field_name, field_name)
                
                # Auto-select common field names
                if field_name.lower() in ['cn_comp', 'cn', 'curve_number']:
                    self.cn_field_combo.setCurrentText(field_name)
                elif field_name.lower() in ['name', 'id', 'basin_id', 'subbasin']:
                    self.id_field_combo.setCurrentText(field_name)
        
        self.update_status()
    
    def browse_output_dir(self):
        """Browse for output directory"""
        dir_path = QFileDialog.getExistingDirectory(
            self, 
            "Select Output Directory",
            self.output_dir_edit.text() or os.path.expanduser("~")
        )
        
        if dir_path:
            self.output_dir_edit.setText(dir_path)
            self.output_dir = dir_path
            self.update_status()
    
    def update_status(self):
        """Update status message"""
        issues = []
        
        if not self.subbasin_combo.currentData():
            issues.append("subbasin layer")
        elif not self.id_field_combo.currentData():
            issues.append("basin ID field")
        elif not self.cn_field_combo.currentData():
            issues.append("CN field")
            
        if not self.dem_combo.currentData():
            issues.append("DEM layer")
            
        if not self.output_dir_edit.text():
            issues.append("output directory")
        
        if issues:
            self.status_label.setText(f"Please select: {', '.join(issues)}")
            self.status_label.setStyleSheet("color: #d32f2f; padding: 5px;")
            self.calculate_btn.setEnabled(False)
        else:
            self.status_label.setText("✅ Ready to calculate")
            self.status_label.setStyleSheet("color: #2e7d32; padding: 5px;")
            self.calculate_btn.setEnabled(True)
    
    def validate_inputs(self):
        """Validate all inputs and show detailed feedback"""
        messages = []
        errors = []
        
        # Check subbasin layer
        subbasin_layer = self.subbasin_combo.currentData()
        if not subbasin_layer:
            errors.append("No subbasin layer selected")
        elif not isinstance(subbasin_layer, QgsVectorLayer):
            errors.append("Invalid subbasin layer")
        else:
            count = subbasin_layer.featureCount()
            messages.append(f"✅ Subbasin layer: {subbasin_layer.name()} ({count} features)")
            
            # Check fields
            id_field = self.id_field_combo.currentData()
            cn_field = self.cn_field_combo.currentData()
            
            if not id_field:
                errors.append("No basin ID field selected")
            else:
                messages.append(f"✅ Basin ID field: {id_field}")
                
            if not cn_field:
                errors.append("No CN field selected")
            else:
                messages.append(f"✅ CN field: {cn_field}")
                
                # Check CN values
                cn_values = []
                for feature in subbasin_layer.getFeatures():
                    try:
                        cn_val = feature[cn_field]
                        if cn_val is not None:
                            cn_values.append(float(cn_val))
                    except:
                        continue
                        
                if cn_values:
                    min_cn = min(cn_values)
                    max_cn = max(cn_values)
                    avg_cn = sum(cn_values) / len(cn_values)
                    messages.append(f"📊 CN range: {min_cn:.0f} - {max_cn:.0f} (avg: {avg_cn:.1f})")
                else:
                    messages.append("⚠️ No valid CN values found - will use default")
        
        # Check DEM layer
        dem_layer = self.dem_combo.currentData()
        if not dem_layer:
            errors.append("No DEM layer selected")
        elif not isinstance(dem_layer, QgsRasterLayer):
            errors.append("Invalid DEM layer")
        else:
            messages.append(f"✅ DEM layer: {dem_layer.name()}")
            
            # Check if layers have compatible CRS
            if subbasin_layer and subbasin_layer.crs() != dem_layer.crs():
                messages.append("⚠️ Warning: Subbasin and DEM layers have different CRS")
        
        # Check output directory
        output_dir = self.output_dir_edit.text()
        if not output_dir:
            errors.append("No output directory selected")
        elif not os.path.exists(output_dir):
            errors.append("Output directory does not exist")
        elif not os.access(output_dir, os.W_OK):
            errors.append("Output directory is not writable")
        else:
            messages.append(f"✅ Output directory: {output_dir}")
        
        # Show results
        if errors:
            error_text = "❌ Validation Errors:\n" + "\n".join(f"• {error}" for error in errors)
            if messages:
                error_text += "\n\n✅ Valid Settings:\n" + "\n".join(f"• {msg}" for msg in messages)
            QMessageBox.warning(self, "Validation Failed", error_text)
        else:
            success_text = "✅ All inputs validated successfully!\n\n" + "\n".join(f"• {msg}" for msg in messages)
            QMessageBox.information(self, "Validation Successful", success_text)
    
    def run_calculation(self):
        """Run the TC calculation"""
        # Final validation
        subbasin_layer = self.subbasin_combo.currentData()
        id_field = self.id_field_combo.currentData()
        cn_field = self.cn_field_combo.currentData()
        length_field = self.length_field_combo.currentData() if self.length_field_combo.currentText() != "-- No flow length field --" else None
        dem_layer = self.dem_combo.currentData()
        output_dir = self.output_dir_edit.text()
        
        if not all([subbasin_layer, id_field, cn_field, dem_layer, output_dir]):
            QMessageBox.warning(self, "Missing Inputs", "Please complete all required inputs before calculating.")
            return
        
        # Disable UI during calculation
        self.calculate_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Create and start worker thread
        self.worker = TCCalculationWorker(
            subbasin_layer=subbasin_layer,
            subbasin_field=id_field,
            cn_field=cn_field,
            dem_layer=dem_layer,
            flow_length_field=length_field,
            default_cn=self.default_cn_spin.value(),
            min_slope=self.min_slope_spin.value()
        )
        
        # Connect signals
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.calculation_completed.connect(self.on_calculation_completed)
        self.worker.error_occurred.connect(self.on_calculation_error)
        
        # Start calculation
        self.worker.start()
    
    def on_progress_updated(self, progress, message):
        """Handle progress updates"""
        if progress >= 0:
            self.progress_bar.setValue(progress)
        self.status_label.setText(message)
    
    def on_calculation_completed(self, results):
        """Handle calculation completion"""
        self.results = results
        self.progress_bar.setVisible(False)
        self.calculate_btn.setEnabled(True)
        
        if not results:
            QMessageBox.warning(self, "No Results", "No valid results were generated. Please check your inputs.")
            return
        
        # Update results display
        self.update_results_display()
        
        # Create output files
        try:
            self.create_output_files()
            self.status_label.setText(f"✅ Calculation completed! {len(results)} basins processed.")
            self.status_label.setStyleSheet("color: #2e7d32; padding: 5px;")
            
            # Show completion message
            self.show_completion_message()
            
        except Exception as e:
            QMessageBox.critical(self, "Output Error", f"Calculation completed but error creating outputs:\n{str(e)}")
    
    def on_calculation_error(self, error_message):
        """Handle calculation errors"""
        self.progress_bar.setVisible(False)
        self.calculate_btn.setEnabled(True)
        self.status_label.setText("❌ Calculation failed")
        self.status_label.setStyleSheet("color: #d32f2f; padding: 5px;")
        
        QMessageBox.critical(self, "Calculation Error", error_message)
    
    def update_results_display(self):
        """Update the results table"""
        if not self.results:
            return
        
        # Setup table
        self.results_table.setRowCount(len(self.results))
        headers = ['Basin ID', 'CN', 'Length (ft)', 'Slope (%)', 'TC (min)', 'TC (hr)']
        self.results_table.setColumnCount(len(headers))
        self.results_table.setHorizontalHeaderLabels(headers)
        
        # Populate data
        tc_values = []
        
        for row, (basin_id, data) in enumerate(self.results.items()):
            self.results_table.setItem(row, 0, QTableWidgetItem(str(basin_id)))
            self.results_table.setItem(row, 1, QTableWidgetItem(f"{data['cn_value']:.0f}"))
            self.results_table.setItem(row, 2, QTableWidgetItem(f"{data['length_ft']:.0f}"))
            self.results_table.setItem(row, 3, QTableWidgetItem(f"{data['slope_percent']:.2f}"))
            self.results_table.setItem(row, 4, QTableWidgetItem(f"{data['tc_minutes']:.1f}"))
            self.results_table.setItem(row, 5, QTableWidgetItem(f"{data['tc_hours']:.2f}"))
            
            tc_values.append(data['tc_minutes'])
        
        # Resize columns
        self.results_table.resizeColumnsToContents()
        
        # Update summary
        if tc_values:
            min_tc = min(tc_values)
            max_tc = max(tc_values)
            avg_tc = sum(tc_values) / len(tc_values)
            
            summary = f"""
<b>Calculation Summary:</b><br>
• Method: SCS/NRCS TR-55<br>
• Basins processed: {len(self.results)}<br>
• TC range: {min_tc:.1f} - {max_tc:.1f} minutes<br>
• Average TC: {avg_tc:.1f} minutes ({avg_tc/60:.2f} hours)
            """
            self.summary_label.setText(summary)
            self.summary_label.setStyleSheet("color: #333; padding: 10px;")
    
    def create_output_files(self):
        """Create output CSV and shapefile"""
        if not self.results or not self.output_dir:
            return
        
        output_dir = self.output_dir_edit.text()
        
        # Create CSV file
        csv_path = os.path.join(output_dir, "tc_calculations_scs_nrcs.csv")
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'Basin_ID', 'CN_Value', 'Flow_Length_ft', 'Avg_Slope_pct', 
                'TC_minutes', 'TC_hours'
            ])
            
            # Data rows
            for basin_id, data in self.results.items():
                writer.writerow([
                    basin_id,
                    round(data['cn_value'], 0),
                    round(data['length_ft'], 2),
                    round(data['slope_percent'], 3),
                    round(data['tc_minutes'], 2),
                    round(data['tc_hours'], 3)
                ])
        
        # Create shapefile with TC results
        self.create_output_shapefile(output_dir)
    
    def create_output_shapefile(self, output_dir):
        """Create output shapefile with TC fields added"""
        subbasin_layer = self.subbasin_combo.currentData()
        id_field = self.id_field_combo.currentData()
        
        # Create output layer
        crs = subbasin_layer.crs()
        output_layer = QgsVectorLayer(f"Polygon?crs={crs.authid()}", "subbasins_tc", "memory")
        output_provider = output_layer.dataProvider()
        
        # Copy original fields and add TC fields
        original_fields = list(subbasin_layer.fields())
        new_fields = original_fields + [
            QgsField("TC_CN", QVariant.Double, "double", 6, 0),
            QgsField("TC_Length", QVariant.Double, "double", 12, 2),
            QgsField("TC_Slope", QVariant.Double, "double", 8, 3),
            QgsField("TC_Minutes", QVariant.Double, "double", 10, 2),
            QgsField("TC_Hours", QVariant.Double, "double", 8, 3)
        ]
        
        output_provider.addAttributes(new_fields)
        output_layer.updateFields()
        
        # Add features with TC data
        output_features = []
        
        for orig_feature in subbasin_layer.getFeatures():
            basin_id = orig_feature[id_field] if id_field else f"Basin_{orig_feature.id()}"
            
            new_feature = QgsFeature()
            new_feature.setGeometry(orig_feature.geometry())
            
            # Copy original attributes
            attributes = list(orig_feature.attributes())
            
            # Add TC data if available
            if basin_id in self.results:
                data = self.results[basin_id]
                attributes.extend([
                    data['cn_value'],
                    data['length_ft'],
                    data['slope_percent'],
                    data['tc_minutes'],
                    data['tc_hours']
                ])
            else:
                attributes.extend([None, None, None, None, None])
            
            new_feature.setAttributes(attributes)
            output_features.append(new_feature)
        
        output_provider.addFeatures(output_features)
        
        # Save shapefile
        shp_path = os.path.join(output_dir, "subbasins_tc_scs_nrcs.shp")
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "ESRI Shapefile"
        options.fileEncoding = "UTF-8"
        
        error = QgsVectorFileWriter.writeAsVectorFormatV3(
            output_layer, shp_path, QgsProject.instance().transformContext(), options
        )
        
        if error[0] != QgsVectorFileWriter.NoError:
            raise ValueError(f"Error saving shapefile: {error[1]}")
    
    def show_completion_message(self):
        """Show completion dialog"""
        processed_count = len(self.results)
        output_dir = self.output_dir_edit.text()
        
        tc_values = [data['tc_minutes'] for data in self.results.values()]
        avg_tc = sum(tc_values) / len(tc_values) if tc_values else 0
        
        message = f"""
Time of Concentration Calculation Completed!

📊 Results Summary:
• Method: SCS/NRCS TR-55 (Correct Implementation)
• Processed: {processed_count} subbasins
• Average TC: {avg_tc:.1f} minutes ({avg_tc/60:.2f} hours)
• Output directory: {output_dir}

📁 Output Files Created:
• tc_calculations_scs_nrcs.csv - Detailed results
• subbasins_tc_scs_nrcs.shp - Shapefile with TC fields

Would you like to load the results into QGIS?
"""
        
        reply = QMessageBox.question(
            self,
            "Calculation Complete",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            # Load result layer into QGIS
            shp_path = os.path.join(output_dir, "subbasins_tc_scs_nrcs.shp")
            if os.path.exists(shp_path):
                result_layer = QgsVectorLayer(shp_path, "Subbasins with TC (SCS/NRCS)", "ogr")
                if result_layer.isValid():
                    QgsProject.instance().addMapLayer(result_layer)
                    self.status_label.setText("✅ Results loaded into QGIS project")


def run_tc_calculator():
    """Main function to run the TC Calculator"""
    try:
        # Check if we're in QGIS
        if 'qgis' not in globals():
            print("This tool must be run from within QGIS Python Console")
            return
        
        # Create and show dialog
        dialog = TCCalculatorDialog()
        dialog.exec_()
        
    except Exception as e:
        print(f"Error running TC Calculator: {str(e)}")
        print(traceback.format_exc())


# Auto-run if script is executed directly
if __name__ == "__main__":
    print("="*60)
    print("TIME OF CONCENTRATION CALCULATOR - SCS/NRCS TR-55 METHOD")
    print("="*60)
    print("\nFeatures:")
    print("✅ Proper raster layer selection for DEM")
    print("✅ Correct SCS/NRCS TR-55 formula implementation")
    print("✅ DEM-based slope calculation using zonal statistics")
    print("✅ Reads actual CN values from shapefile fields")
    print("✅ Standalone operation - no external dependencies")
    print("✅ CSV and shapefile output with TC results")
    print("\nStarting calculator...")
    
    run_tc_calculator()