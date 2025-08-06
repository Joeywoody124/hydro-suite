"""
Enhanced GUI dialog for Time of Concentration plugin - MULTI-METHOD VERSION
Version 3.0.0 - Supports Kirpich, FAA, SCS/NRCS, and Kerby methods
Features method selection, parameter configuration, and comparative analysis
PEP8 compliant with comprehensive error handling
"""
import os
import traceback
import sys
import importlib.util
from typing import Optional, List, Dict

from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFileDialog, QMessageBox, QProgressBar, QGroupBox,
    QCheckBox, QComboBox, QTabWidget, QWidget,
    QTextEdit, QSizePolicy, QDialogButtonBox, QSpinBox,
    QDoubleSpinBox, QFrame, QScrollArea, QGridLayout,
    QButtonGroup, QRadioButton
)
from qgis.PyQt.QtCore import Qt, QSettings
from qgis.PyQt.QtGui import QFont, QPalette, QColor
from qgis.gui import QgsMapLayerComboBox, QgsFieldComboBox, QgsProjectionSelectionWidget
from qgis.core import (
    QgsMapLayerProxyModel, QgsMessageLog, Qgis,
    QgsProject, QgsCoordinateReferenceSystem,
    QgsCoordinateTransform, QgsVectorLayer,
    QgsApplication, QgsFieldProxyModel
)


class TimeOfConcentrationDialog(QDialog):
    """Enhanced dialog for Time of Concentration calculations with multiple methods"""
    
    def __init__(self, parent=None, iface=None):
        super(TimeOfConcentrationDialog, self).__init__(parent)
        self.iface = iface
        self.csv_path = None
        self.settings = QSettings()
        self.tc_calculator = None
        
        # Method selection tracking
        self.selected_methods = ['kirpich', 'faa']  # Default methods
        
        # Load the processing module
        self._load_processing_module()
        
        # Initialize UI
        self.initUI()
        
        # Restore previous settings
        self._restore_settings()
        
    def _load_processing_module(self):
        """Load the enhanced tc_processing module dynamically"""
        try:
            plugin_dir = os.path.dirname(__file__)
            tc_module_path = os.path.join(plugin_dir, "tc_processing.py")
            
            if not os.path.exists(tc_module_path):
                QgsMessageLog.logMessage(
                    f"tc_processing.py not found at: {tc_module_path}", 
                    "TC Calculator Multi", 
                    Qgis.Critical
                )
                return
            
            # Force remove any cached module first
            module_name = "tc_processing"
            if module_name in sys.modules:
                del sys.modules[module_name]
                QgsMessageLog.logMessage(
                    "Removed cached tc_processing module", 
                    "TC Calculator Multi", 
                    Qgis.Info
                )
            
            # Load the module
            spec = importlib.util.spec_from_file_location("tc_processing", tc_module_path)
            tc_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(tc_module)
            
            # Get the calculator class
            if hasattr(tc_module, 'TimeOfConcentrationCalculator'):
                self.tc_calculator = tc_module.TimeOfConcentrationCalculator()
                
                # Verify multi-method capability
                if hasattr(self.tc_calculator, 'calculate_tc_for_subbasins'):
                    # Check method signature for multi-method support
                    import inspect
                    sig = inspect.signature(self.tc_calculator.calculate_tc_for_subbasins)
                    if 'selected_methods' in sig.parameters:
                        QgsMessageLog.logMessage(
                            "✅ Multi-method TC Calculator loaded successfully", 
                            "TC Calculator Multi", 
                            Qgis.Info
                        )
                    else:
                        QgsMessageLog.logMessage(
                            "⚠️ Loaded calculator does not support multi-method capability", 
                            "TC Calculator Multi", 
                            Qgis.Warning
                        )
                else:
                    QgsMessageLog.logMessage(
                        "✗ TimeOfConcentrationCalculator missing required methods", 
                        "TC Calculator Multi", 
                        Qgis.Critical
                    )
                    
            else:
                QgsMessageLog.logMessage(
                    "TimeOfConcentrationCalculator class not found in module", 
                    "TC Calculator Multi", 
                    Qgis.Critical
                )
                
        except Exception as e:
            QgsMessageLog.logMessage(
                f"Error loading tc_processing module: {str(e)}", 
                "TC Calculator Multi", 
                Qgis.Critical
            )
    
    def initUI(self):
        """Initialize the enhanced user interface"""
        self.setWindowTitle('Time of Concentration Calculator - Multiple Methods v3.0')
        self.setMinimumWidth(600)
        self.setMinimumHeight(700)
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Header section
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Box)
        header_layout = QVBoxLayout()
        
        title_label = QLabel('Time of Concentration Calculator')
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_label)
        
        subtitle_label = QLabel('Multiple Methods: Kirpich • FAA • SCS/NRCS • Kerby')
        subtitle_font = QFont()
        subtitle_font.setPointSize(10)
        subtitle_font.setItalic(True)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #666666;")
        header_layout.addWidget(subtitle_label)
        
        header_frame.setLayout(header_layout)
        main_layout.addWidget(header_frame)
        
        # Create tab widget for organized interface
        self.tab_widget = QTabWidget()
        
        # === METHODS TAB ===
        methods_tab = self._create_methods_tab()
        self.tab_widget.addTab(methods_tab, "Methods")
        
        # === INPUTS TAB ===
        inputs_tab = self._create_inputs_tab()
        self.tab_widget.addTab(inputs_tab, "Inputs")
        
        # === PARAMETERS TAB ===
        parameters_tab = self._create_parameters_tab()
        self.tab_widget.addTab(parameters_tab, "Parameters")
        
        # === ADVANCED TAB ===
        advanced_tab = self._create_advanced_tab()
        self.tab_widget.addTab(advanced_tab, "Advanced")
        
        # === LOG TAB ===
        log_tab = self._create_log_tab()
        self.tab_widget.addTab(log_tab, "Log")
        
        main_layout.addWidget(self.tab_widget)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.help_button = QPushButton('Help')
        self.help_button.clicked.connect(self._show_help)
        button_layout.addWidget(self.help_button)
        
        self.method_info_button = QPushButton('Method Info')
        self.method_info_button.clicked.connect(self._show_method_info)
        button_layout.addWidget(self.method_info_button)
        
        button_layout.addStretch()
        
        self.validate_button = QPushButton('Validate Inputs')
        self.validate_button.clicked.connect(self._validate_inputs)
        button_layout.addWidget(self.validate_button)
        
        self.run_button = QPushButton('Run Analysis')
        self.run_button.clicked.connect(self.run_analysis)
        self.run_button.setDefault(True)
        # Make run button prominent
        self.run_button.setStyleSheet("""
            QPushButton {
                background-color: #2E7D32;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """)
        button_layout.addWidget(self.run_button)
        
        self.close_button = QPushButton('Close')
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
        # Connect signals
        self._connect_signals()
        
    def _create_methods_tab(self) -> QWidget:
        """Create the methods selection tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Method selection group
        methods_group = QGroupBox("Select Calculation Methods")
        methods_layout = QVBoxLayout()
        
        # Create method checkboxes with descriptions
        self.kirpich_check = QCheckBox("Kirpich (1940)")
        self.kirpich_check.setChecked(True)
        self.kirpich_check.stateChanged.connect(self._update_selected_methods)
        kirpich_desc = QLabel("   Rural watersheds with well-defined channels")
        kirpich_desc.setStyleSheet("color: #666666; font-size: 10px;")
        methods_layout.addWidget(self.kirpich_check)
        methods_layout.addWidget(kirpich_desc)
        
        self.faa_check = QCheckBox("FAA Method (1965)")
        self.faa_check.setChecked(True)
        self.faa_check.stateChanged.connect(self._update_selected_methods)
        faa_desc = QLabel("   Federal Aviation Administration - widely used for urban areas")
        faa_desc.setStyleSheet("color: #666666; font-size: 10px;")
        methods_layout.addWidget(self.faa_check)
        methods_layout.addWidget(faa_desc)
        
        self.scs_check = QCheckBox("SCS/NRCS Lag Time (1972)")
        self.scs_check.setChecked(False)
        self.scs_check.stateChanged.connect(self._update_selected_methods)
        scs_desc = QLabel("   Natural Resources Conservation Service - natural watersheds")
        scs_desc.setStyleSheet("color: #666666; font-size: 10px;")
        methods_layout.addWidget(self.scs_check)
        methods_layout.addWidget(scs_desc)
        
        self.kerby_check = QCheckBox("Kerby Equation")
        self.kerby_check.setChecked(False)
        self.kerby_check.stateChanged.connect(self._update_selected_methods)
        kerby_desc = QLabel("   Overland flow on natural surfaces with retardance")
        kerby_desc.setStyleSheet("color: #666666; font-size: 10px;")
        methods_layout.addWidget(self.kerby_check)
        methods_layout.addWidget(kerby_desc)
        
        methods_group.setLayout(methods_layout)
        layout.addWidget(methods_group)
        
        # Quick selection buttons
        quick_select_group = QGroupBox("Quick Selection")
        quick_layout = QHBoxLayout()
        
        urban_button = QPushButton("Urban Project (Kirpich + FAA)")
        urban_button.clicked.connect(lambda: self._quick_select_methods(['kirpich', 'faa']))
        quick_layout.addWidget(urban_button)
        
        rural_button = QPushButton("Rural Project (Kirpich + SCS)")
        rural_button.clicked.connect(lambda: self._quick_select_methods(['kirpich', 'scs']))
        quick_layout.addWidget(rural_button)
        
        all_button = QPushButton("All Methods")
        all_button.clicked.connect(lambda: self._quick_select_methods(['kirpich', 'faa', 'scs', 'kerby']))
        quick_layout.addWidget(all_button)
        
        quick_select_group.setLayout(quick_layout)
        layout.addWidget(quick_select_group)
        
        # Results configuration
        results_group = QGroupBox("Results Options")
        results_layout = QVBoxLayout()
        
        self.comparative_analysis_check = QCheckBox("Include comparative analysis (average, std dev, recommended)")
        self.comparative_analysis_check.setChecked(True)
        self.comparative_analysis_check.setToolTip(
            "Calculate statistical comparison when multiple methods are selected"
        )
        results_layout.addWidget(self.comparative_analysis_check)
        
        self.add_to_layer_check = QCheckBox('Add results as attributes to subbasin layer')
        self.add_to_layer_check.setChecked(True)
        results_layout.addWidget(self.add_to_layer_check)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def _create_inputs_tab(self) -> QWidget:
        """Create the inputs tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Input layers group
        input_group = QGroupBox("Input Layers")
        input_layout = QVBoxLayout()
        
        # DEM Selection
        dem_layout = QVBoxLayout()
        dem_layout.addWidget(QLabel('Select DEM Raster Layer:'))
        self.dem_combo = QgsMapLayerComboBox()
        self.dem_combo.setFilters(QgsMapLayerProxyModel.RasterLayer)
        dem_layout.addWidget(self.dem_combo)
        input_layout.addLayout(dem_layout)
        
        # Subbasin Selection
        subbasin_layout = QVBoxLayout()
        subbasin_layout.addWidget(QLabel('Select Subbasin Polygon Layer:'))
        self.subbasin_combo = QgsMapLayerComboBox()
        self.subbasin_combo.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.subbasin_combo.layerChanged.connect(self._on_subbasin_layer_changed)
        subbasin_layout.addWidget(self.subbasin_combo)
        input_layout.addLayout(subbasin_layout)
        
        # ID Field Selection
        id_field_layout = QHBoxLayout()
        id_field_layout.addWidget(QLabel('Subbasin ID Field (optional):'))
        self.id_field_combo = QgsFieldComboBox()
        self.id_field_combo.setAllowEmptyFieldName(True)
        self.id_field_combo.setFilters(QgsFieldProxyModel.String | QgsFieldProxyModel.Int)
        id_field_layout.addWidget(self.id_field_combo)
        input_layout.addLayout(id_field_layout)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # Output group
        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout()
        
        # Output CSV
        csv_layout = QHBoxLayout()
        self.csv_button = QPushButton('Select Output CSV Location...')
        self.csv_button.clicked.connect(self.select_output_csv)
        csv_layout.addWidget(self.csv_button)
        
        self.csv_label = QLabel('No file selected')
        self.csv_label.setWordWrap(True)
        csv_layout.addWidget(self.csv_label)
        
        output_layout.addLayout(csv_layout)
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # Layer information display
        info_group = QGroupBox("Layer Information")
        info_layout = QVBoxLayout()
        
        self.dem_info_label = QLabel('DEM: Not selected')
        self.subbasin_info_label = QLabel('Subbasin: Not selected')
        self.crs_info_label = QLabel('CRS: Not checked')
        
        info_layout.addWidget(self.dem_info_label)
        info_layout.addWidget(self.subbasin_info_label)
        info_layout.addWidget(self.crs_info_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def _create_parameters_tab(self) -> QWidget:
        """Create the parameters configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Parameter explanation
        explanation_label = QLabel(
            "Configure parameters for different TC methods. "
            "Default values are provided based on typical conditions, "
            "but you can adjust them based on local knowledge."
        )
        explanation_label.setWordWrap(True)
        explanation_label.setStyleSheet("color: #666666; font-style: italic; padding: 10px;")
        layout.addWidget(explanation_label)
        
        # SCS/NRCS Parameters
        scs_group = QGroupBox("SCS/NRCS Method Parameters")
        scs_layout = QGridLayout()
        
        scs_layout.addWidget(QLabel("Curve Number (CN):"), 0, 0)
        self.curve_number_spin = QSpinBox()
        self.curve_number_spin.setRange(30, 98)
        self.curve_number_spin.setValue(70)
        self.curve_number_spin.setToolTip(
            "SCS Curve Number (30-98)\n"
            "• Urban residential: 75\n"
            "• Agricultural: 65\n"
            "• Forest: 55\n"
            "• Mixed: 70 (default)"
        )
        scs_layout.addWidget(self.curve_number_spin, 0, 1)
        
        cn_preset_combo = QComboBox()
        cn_preset_combo.addItems([
            "Custom", "Urban Residential (75)", "Urban Commercial (85)", 
            "Agricultural (65)", "Forest (55)", "Grassland (60)", "Mixed (70)"
        ])
        cn_preset_combo.currentTextChanged.connect(self._update_curve_number_preset)
        scs_layout.addWidget(cn_preset_combo, 0, 2)
        
        scs_group.setLayout(scs_layout)
        layout.addWidget(scs_group)
        
        # FAA Method Parameters
        faa_group = QGroupBox("FAA Method Parameters")
        faa_layout = QGridLayout()
        
        faa_layout.addWidget(QLabel("Runoff Coefficient (C):"), 0, 0)
        self.runoff_coeff_spin = QDoubleSpinBox()
        self.runoff_coeff_spin.setRange(0.1, 0.95)
        self.runoff_coeff_spin.setSingleStep(0.05)
        self.runoff_coeff_spin.setDecimals(2)
        self.runoff_coeff_spin.setValue(0.50)
        self.runoff_coeff_spin.setToolTip(
            "FAA Runoff Coefficient (0.1-0.95)\n"
            "• Concrete/Asphalt: 0.85-0.90\n"
            "• Urban areas: 0.60-0.80\n"
            "• Agricultural: 0.30\n"
            "• Forest: 0.20\n"
            "• Mixed: 0.50 (default)"
        )
        faa_layout.addWidget(self.runoff_coeff_spin, 0, 1)
        
        c_preset_combo = QComboBox()
        c_preset_combo.addItems([
            "Custom", "Concrete (0.85)", "Urban Dense (0.80)", "Urban Residential (0.60)",
            "Agricultural (0.30)", "Forest (0.20)", "Mixed (0.50)"
        ])
        c_preset_combo.currentTextChanged.connect(self._update_runoff_coeff_preset)
        faa_layout.addWidget(c_preset_combo, 0, 2)
        
        faa_group.setLayout(faa_layout)
        layout.addWidget(faa_group)
        
        # Kerby Method Parameters
        kerby_group = QGroupBox("Kerby Method Parameters")
        kerby_layout = QGridLayout()
        
        kerby_layout.addWidget(QLabel("Roughness Coefficient (n):"), 0, 0)
        self.roughness_spin = QDoubleSpinBox()
        self.roughness_spin.setRange(0.02, 0.80)
        self.roughness_spin.setSingleStep(0.05)
        self.roughness_spin.setDecimals(2)
        self.roughness_spin.setValue(0.30)
        self.roughness_spin.setToolTip(
            "Manning's Roughness Coefficient (0.02-0.80)\n"
            "• Concrete: 0.02\n"
            "• Short grass: 0.15\n"
            "• Dense grass: 0.24\n"
            "• Light brush: 0.40\n"
            "• Dense brush: 0.60\n"
            "• Mixed: 0.30 (default)"
        )
        kerby_layout.addWidget(self.roughness_spin, 0, 1)
        
        n_preset_combo = QComboBox()
        n_preset_combo.addItems([
            "Custom", "Concrete (0.02)", "Short Grass (0.15)", "Dense Grass (0.24)",
            "Light Brush (0.40)", "Dense Brush (0.60)", "Mixed (0.30)"
        ])
        n_preset_combo.currentTextChanged.connect(self._update_roughness_preset)
        kerby_layout.addWidget(n_preset_combo, 0, 2)
        
        kerby_group.setLayout(kerby_layout)
        layout.addWidget(kerby_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def _create_advanced_tab(self) -> QWidget:
        """Create the advanced options tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # CRS handling group
        crs_group = QGroupBox("Coordinate Reference System")
        crs_layout = QVBoxLayout()
        
        # CRS info labels
        self.dem_crs_label = QLabel('DEM CRS: Not selected')
        self.subbasin_crs_label = QLabel('Subbasin CRS: Not selected')
        crs_layout.addWidget(self.dem_crs_label)
        crs_layout.addWidget(self.subbasin_crs_label)
        
        # Auto-reproject checkbox
        self.auto_reproject_check = QCheckBox('Automatically handle CRS mismatches')
        self.auto_reproject_check.setChecked(False)
        self.auto_reproject_check.setToolTip(
            'When checked, layers will be reprojected on-the-fly if needed.\n'
            'This may affect performance for large datasets.'
        )
        crs_layout.addWidget(self.auto_reproject_check)
        
        crs_group.setLayout(crs_layout)
        layout.addWidget(crs_group)
        
        # Processing options
        processing_group = QGroupBox("Processing Options")
        processing_layout = QVBoxLayout()
        
        self.use_hydrologic_check = QCheckBox('Use hydrologic flow path analysis (recommended)')
        self.use_hydrologic_check.setChecked(True)
        self.use_hydrologic_check.setToolTip(
            'When checked, attempts to use proper hydrologic analysis.\n'
            'When unchecked, uses simplified geometric approach.'
        )
        processing_layout.addWidget(self.use_hydrologic_check)
        
        processing_group.setLayout(processing_layout)
        layout.addWidget(processing_group)
        
        # Validation group
        validation_group = QGroupBox("Validation Options")
        validation_layout = QVBoxLayout()
        
        self.validate_geometries_check = QCheckBox('Validate and fix geometries before processing')
        self.validate_geometries_check.setChecked(True)
        validation_layout.addWidget(self.validate_geometries_check)
        
        self.skip_invalid_check = QCheckBox('Skip invalid features instead of stopping')
        self.skip_invalid_check.setChecked(True)
        validation_layout.addWidget(self.skip_invalid_check)
        
        validation_group.setLayout(validation_layout)
        layout.addWidget(validation_group)
        
        # DEM sampling group
        dem_group = QGroupBox("DEM Sampling Options")
        dem_layout = QVBoxLayout()
        
        sample_radius_layout = QHBoxLayout()
        sample_radius_layout.addWidget(QLabel('Initial sampling radius (meters):'))
        self.sample_radius_spin = QSpinBox()
        self.sample_radius_spin.setRange(1, 100)
        self.sample_radius_spin.setValue(10)
        self.sample_radius_spin.setToolTip(
            'Radius for sampling nearby points when exact point sampling fails'
        )
        sample_radius_layout.addWidget(self.sample_radius_spin)
        sample_radius_layout.addStretch()
        dem_layout.addLayout(sample_radius_layout)
        
        dem_group.setLayout(dem_layout)
        layout.addWidget(dem_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def _create_log_tab(self) -> QWidget:
        """Create the log tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier", 9))
        layout.addWidget(QLabel('Processing Log:'))
        layout.addWidget(self.log_text)
        
        # Log controls
        log_controls = QHBoxLayout()
        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.clicked.connect(self.log_text.clear)
        log_controls.addWidget(clear_log_btn)
        log_controls.addStretch()
        
        layout.addLayout(log_controls)
        tab.setLayout(layout)
        return tab
    
    def _connect_signals(self):
        """Connect UI signals"""
        # Connect signals for updating info labels
        self.dem_combo.layerChanged.connect(self._update_layer_info)
        self.subbasin_combo.layerChanged.connect(self._update_layer_info)
        
    def _update_selected_methods(self):
        """Update the list of selected methods"""
        self.selected_methods = []
        
        if self.kirpich_check.isChecked():
            self.selected_methods.append('kirpich')
        if self.faa_check.isChecked():
            self.selected_methods.append('faa')
        if self.scs_check.isChecked():
            self.selected_methods.append('scs')
        if self.kerby_check.isChecked():
            self.selected_methods.append('kerby')
        
        # Update comparative analysis checkbox availability
        self.comparative_analysis_check.setEnabled(len(self.selected_methods) > 1)
        
        QgsMessageLog.logMessage(
            f"Selected methods updated: {', '.join(self.selected_methods)}", 
            "TC Calculator Multi", 
            Qgis.Info
        )
    
    def _quick_select_methods(self, methods: List[str]):
        """Quick select specific method combinations"""
        # Reset all checkboxes
        self.kirpich_check.setChecked('kirpich' in methods)
        self.faa_check.setChecked('faa' in methods)
        self.scs_check.setChecked('scs' in methods)
        self.kerby_check.setChecked('kerby' in methods)
        
        # Update will be triggered by checkbox state changes
    
    def _update_curve_number_preset(self, text: str):
        """Update curve number based on preset selection"""
        presets = {
            "Urban Residential (75)": 75,
            "Urban Commercial (85)": 85,
            "Agricultural (65)": 65,
            "Forest (55)": 55,
            "Grassland (60)": 60,
            "Mixed (70)": 70
        }
        if text in presets:
            self.curve_number_spin.setValue(presets[text])
    
    def _update_runoff_coeff_preset(self, text: str):
        """Update runoff coefficient based on preset selection"""
        presets = {
            "Concrete (0.85)": 0.85,
            "Urban Dense (0.80)": 0.80,
            "Urban Residential (0.60)": 0.60,
            "Agricultural (0.30)": 0.30,
            "Forest (0.20)": 0.20,
            "Mixed (0.50)": 0.50
        }
        if text in presets:
            self.runoff_coeff_spin.setValue(presets[text])
    
    def _update_roughness_preset(self, text: str):
        """Update roughness coefficient based on preset selection"""
        presets = {
            "Concrete (0.02)": 0.02,
            "Short Grass (0.15)": 0.15,
            "Dense Grass (0.24)": 0.24,
            "Light Brush (0.40)": 0.40,
            "Dense Brush (0.60)": 0.60,
            "Mixed (0.30)": 0.30
        }
        if text in presets:
            self.roughness_spin.setValue(presets[text])
    
    def _on_subbasin_layer_changed(self, layer):
        """Handle subbasin layer change"""
        # Update field combo box
        self.id_field_combo.setLayer(layer)
        
        # Try to auto-select an ID field
        if layer:
            field_names = [field.name().lower() for field in layer.fields()]
            for candidate in ['id', 'fid', 'objectid', 'name', 'basin_id', 'subbasin_id']:
                if candidate in field_names:
                    idx = field_names.index(candidate)
                    actual_name = layer.fields()[idx].name()
                    self.id_field_combo.setField(actual_name)
                    break
    
    def _update_layer_info(self):
        """Update layer information display"""
        # DEM info
        if self.dem_combo.currentLayer():
            dem_layer = self.dem_combo.currentLayer()
            dem_crs = dem_layer.crs()
            self.dem_info_label.setText(f'DEM: {dem_layer.name()} ({dem_layer.bandCount()} bands)')
            self.dem_crs_label.setText(f'DEM CRS: {dem_crs.authid()} - {dem_crs.description()}')
        else:
            self.dem_info_label.setText('DEM: Not selected')
            self.dem_crs_label.setText('DEM CRS: Not selected')
            
        # Subbasin info
        if self.subbasin_combo.currentLayer():
            subbasin_layer = self.subbasin_combo.currentLayer()
            subbasin_crs = subbasin_layer.crs()
            feature_count = subbasin_layer.featureCount()
            self.subbasin_info_label.setText(f'Subbasin: {subbasin_layer.name()} ({feature_count} features)')
            self.subbasin_crs_label.setText(f'Subbasin CRS: {subbasin_crs.authid()} - {subbasin_crs.description()}')
        else:
            self.subbasin_info_label.setText('Subbasin: Not selected')
            self.subbasin_crs_label.setText('Subbasin CRS: Not selected')
        
        # CRS compatibility check
        if self.dem_combo.currentLayer() and self.subbasin_combo.currentLayer():
            dem_crs = self.dem_combo.currentLayer().crs()
            subbasin_crs = self.subbasin_combo.currentLayer().crs()
            
            if dem_crs == subbasin_crs:
                self.crs_info_label.setText('CRS: ✓ Compatible')
                self.crs_info_label.setStyleSheet("color: green;")
            else:
                self.crs_info_label.setText('CRS: ⚠ Mismatch detected')
                self.crs_info_label.setStyleSheet("color: orange;")
        else:
            self.crs_info_label.setText('CRS: Not checked')
            self.crs_info_label.setStyleSheet("color: #666666;")
    
    def select_output_csv(self):
        """Handle output CSV selection"""
        # Get last used directory
        last_dir = self.settings.value('TCCalculatorMulti/lastOutputDir', '')
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            'Save Multi-Method TC Results CSV', 
            last_dir, 
            'CSV files (*.csv);;All files (*.*)'
        )
        
        if file_path:
            # Add .csv extension if not present
            if not file_path.lower().endswith('.csv'):
                file_path += '.csv'
                
            self.csv_path = file_path
            self.csv_label.setText(os.path.basename(file_path))
            
            # Save directory for next time
            self.settings.setValue('TCCalculatorMulti/lastOutputDir', os.path.dirname(file_path))
    
    def _validate_inputs(self):
        """Validate all inputs and show detailed results"""
        messages = []
        warnings = []
        errors = []
        
        # Check method selection
        if not self.selected_methods:
            errors.append("No calculation methods selected")
        else:
            messages.append(f"✓ Selected methods: {', '.join(self.selected_methods)}")
        
        # Check DEM layer
        if not self.dem_combo.currentLayer():
            errors.append("No DEM layer selected")
        else:
            dem_layer = self.dem_combo.currentLayer()
            if not dem_layer.isValid():
                errors.append("Selected DEM layer is invalid")
            else:
                messages.append(f"✓ DEM layer: {dem_layer.name()}")
                if dem_layer.bandCount() > 1:
                    warnings.append(f"DEM has {dem_layer.bandCount()} bands - will use band 1")
        
        # Check subbasin layer
        if not self.subbasin_combo.currentLayer():
            errors.append("No subbasin layer selected")
        else:
            subbasin_layer = self.subbasin_combo.currentLayer()
            if not subbasin_layer.isValid():
                errors.append("Selected subbasin layer is invalid")
            else:
                feature_count = subbasin_layer.featureCount()
                messages.append(f"✓ Subbasin layer: {subbasin_layer.name()} ({feature_count} features)")
                
                # Check for invalid geometries
                invalid_count = 0
                for feature in subbasin_layer.getFeatures():
                    if not feature.geometry() or not feature.geometry().isGeosValid():
                        invalid_count += 1
                
                if invalid_count > 0:
                    if self.skip_invalid_check.isChecked():
                        warnings.append(f"{invalid_count} features have invalid geometries and will be skipped")
                    else:
                        errors.append(f"{invalid_count} features have invalid geometries")
        
        # Check CRS compatibility
        if self.dem_combo.currentLayer() and self.subbasin_combo.currentLayer():
            dem_crs = self.dem_combo.currentLayer().crs()
            subbasin_crs = self.subbasin_combo.currentLayer().crs()
            
            if dem_crs != subbasin_crs:
                if self.auto_reproject_check.isChecked():
                    warnings.append(
                        f"CRS mismatch will be handled automatically:\n"
                        f"  DEM: {dem_crs.authid()}\n"
                        f"  Subbasins: {subbasin_crs.authid()}"
                    )
                else:
                    errors.append(
                        f"CRS mismatch detected:\n"
                        f"  DEM: {dem_crs.authid()}\n"
                        f"  Subbasins: {subbasin_crs.authid()}\n"
                        f"Enable auto-reprojection or reproject layers manually"
                    )
            else:
                messages.append(f"✓ Both layers use the same CRS: {dem_crs.authid()}")
        
        # Check output
        if not self.csv_path:
            errors.append("No output CSV file selected")
        else:
            messages.append(f"✓ Output CSV: {self.csv_path}")
            
            # Check if directory exists and is writable
            output_dir = os.path.dirname(self.csv_path)
            if not os.path.exists(output_dir):
                errors.append(f"Output directory does not exist: {output_dir}")
            elif not os.access(output_dir, os.W_OK):
                errors.append(f"Output directory is not writable: {output_dir}")
        
        # Check processing module
        if not self.tc_calculator:
            errors.append("Multi-method processing module not loaded properly")
        else:
            messages.append("✓ Multi-method processing module loaded successfully")
        
        # Parameter validation
        param_warnings = self._validate_parameters()
        warnings.extend(param_warnings)
        
        # Show results
        result_text = ""
        
        if messages:
            result_text += "Valid inputs:\n" + "\n".join(messages) + "\n\n"
        
        if warnings:
            result_text += "Warnings:\n" + "\n".join(warnings) + "\n\n"
        
        if errors:
            result_text += "Errors:\n" + "\n".join(errors)
            QMessageBox.critical(self, "Validation Failed", result_text)
            return False
        else:
            if warnings:
                QMessageBox.warning(self, "Validation Passed with Warnings", result_text)
            else:
                QMessageBox.information(self, "Validation Passed", result_text)
            return True
    
    def _validate_parameters(self) -> List[str]:
        """Validate method parameters and return warnings"""
        warnings = []
        
        # SCS method parameter checks
        if 'scs' in self.selected_methods:
            cn = self.curve_number_spin.value()
            if cn < 40:
                warnings.append(f"Curve Number {cn} is very low - check if appropriate for your watershed")
            elif cn > 90:
                warnings.append(f"Curve Number {cn} is very high - typical for highly impervious areas")
        
        # FAA method parameter checks
        if 'faa' in self.selected_methods:
            c = self.runoff_coeff_spin.value()
            if c < 0.2:
                warnings.append(f"Runoff Coefficient {c} is very low - check if appropriate for your land use")
            elif c > 0.8:
                warnings.append(f"Runoff Coefficient {c} is very high - typical for urban areas")
        
        # Kerby method parameter checks
        if 'kerby' in self.selected_methods:
            n = self.roughness_spin.value()
            if n < 0.1:
                warnings.append(f"Roughness Coefficient {n} is very low - typical for smooth surfaces")
            elif n > 0.5:
                warnings.append(f"Roughness Coefficient {n} is very high - typical for dense vegetation")
        
        return warnings
    
    def run_analysis(self):
        """Run the multi-method time of concentration analysis"""
        # Clear log
        self.log_text.clear()
        self._add_log("=== Starting Multi-Method Time of Concentration Analysis ===")
        self._add_log(f"Version: 3.0.0")
        self._add_log(f"Selected methods: {', '.join(self.selected_methods)}")
        
        # Validate inputs
        if not self._validate_inputs():
            return
        
        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Disable buttons during processing
        self.run_button.setEnabled(False)
        self.validate_button.setEnabled(False)
        
        try:
            # Get selected layers
            dem_layer = self.dem_combo.currentLayer()
            subbasin_layer = self.subbasin_combo.currentLayer()
            
            # Get selected ID field
            id_field = self.id_field_combo.currentField() if self.id_field_combo.currentField() else None
            
            # Get method parameters
            curve_number = self.curve_number_spin.value()
            runoff_coefficient = self.runoff_coeff_spin.value()
            roughness_coefficient = self.roughness_spin.value()
            
            # Check if calculator is loaded
            if not self.tc_calculator:
                raise Exception("Multi-method processing module not loaded")
            
            self._add_log(f"DEM Layer: {dem_layer.name()}")
            self._add_log(f"Subbasin Layer: {subbasin_layer.name()}")
            self._add_log(f"ID Field: {id_field if id_field else 'Auto-detect'}")
            self._add_log(f"Output CSV: {self.csv_path}")
            self._add_log(f"Parameters: CN={curve_number}, C={runoff_coefficient}, n={roughness_coefficient}")
            
            # Add detailed layer information for debugging
            self._add_log(f"DEM CRS: {dem_layer.crs().authid()}")
            self._add_log(f"DEM Extent: {dem_layer.extent()}")
            self._add_log(f"DEM Band count: {dem_layer.bandCount()}")
            self._add_log(f"Subbasin CRS: {subbasin_layer.crs().authid()}")
            self._add_log(f"Subbasin Feature count: {subbasin_layer.featureCount()}")
            self._add_log(f"Subbasin Extent: {subbasin_layer.extent()}")
            
            # Run the multi-method processing
            self._add_log("Starting multi-method TC calculation...")
            success = self.tc_calculator.calculate_tc_for_subbasins(
                dem_layer=dem_layer,
                subbasin_layer=subbasin_layer,
                output_csv=self.csv_path,
                selected_methods=self.selected_methods,
                id_field=id_field,
                curve_number=curve_number,
                runoff_coefficient=runoff_coefficient,
                roughness_coefficient=roughness_coefficient,
                progress_bar=self.progress_bar
            )
            
            if success:
                self._add_log("=== MULTI-METHOD ANALYSIS COMPLETED SUCCESSFULLY! ===")
                
                # Show success message
                method_list = ', '.join([m.title() for m in self.selected_methods])
                msg = f'Multi-method Time of Concentration calculation completed successfully.\n\n'
                msg += f'Methods used: {method_list}\n'
                msg += f'Results saved to: {self.csv_path}\n\n'
                
                if self.add_to_layer_check.isChecked():
                    msg += 'Results have been added as attributes to the subbasin layer.\n'
                    msg += 'Fields include comparative analysis (average, recommended TC).'
                    # Refresh the layer
                    subbasin_layer.triggerRepaint()
                    # Refresh attribute table if open
                    if hasattr(self.iface, 'actionOpenTable'):
                        self.iface.actionOpenTable().trigger()
                
                QMessageBox.information(self, 'Multi-Method Analysis Complete', msg)
                
                # Switch to log tab to show results
                self.tab_widget.setCurrentIndex(4)  # Log tab
                
            else:
                self._add_log("=== ANALYSIS FAILED! ===")
                self._add_log("Check the error messages above for details.")
                QMessageBox.warning(
                    self, 
                    'Analysis Failed', 
                    'Multi-method Time of Concentration calculation failed.\n'
                    'Please check the log tab for details.'
                )
                self.tab_widget.setCurrentIndex(4)  # Log tab
                
        except Exception as e:
            self._add_log(f"=== CRITICAL ERROR ===")
            self._add_log(f"ERROR: {str(e)}")
            self._add_log(f"Error type: {type(e).__name__}")
            self._add_log(f"Full traceback:")
            self._add_log(traceback.format_exc())
            
            QMessageBox.critical(
                self, 
                'Critical Error', 
                f'A critical error occurred during multi-method processing:\n{str(e)}\n\n'
                'Please check the log tab for detailed information.'
            )
            self.tab_widget.setCurrentIndex(4)  # Log tab
            
        finally:
            # Re-enable buttons
            self.run_button.setEnabled(True)
            self.validate_button.setEnabled(True)
            self.progress_bar.setVisible(False)
    
    def _add_log(self, message: str):
        """Add message to log"""
        self.log_text.append(message)
        QgsMessageLog.logMessage(message, "TC Calculator Multi", Qgis.Info)
        
        # Process events to update GUI
        QgsApplication.processEvents()
    
    def _show_help(self):
        """Show comprehensive help dialog"""
        help_text = """
        <h2>Time of Concentration Calculator - Multiple Methods v3.0</h2>
        
        <h3>Overview</h3>
        <p>This advanced tool calculates time of concentration for watershed subbasins using multiple established methods for comparison and validation.</p>
        
        <h3>Available Methods</h3>
        <ul>
            <li><b>Kirpich (1940):</b> TC = 0.0078 × L^0.77 / S^0.385<br>
                <i>Best for: Rural watersheds with well-defined channels</i></li>
            <li><b>FAA (1965):</b> TC = 1.8 × (1.1 - C) × √L / √S<br>
                <i>Best for: Urban areas, widely accepted by regulatory agencies</i></li>
            <li><b>SCS/NRCS (1972):</b> Tlag = (L^0.8 × (1000/CN - 9)^0.7) / (1900 × √S), TC = 1.67 × Tlag<br>
                <i>Best for: Natural watersheds, NRCS compliance</i></li>
            <li><b>Kerby:</b> TC = 1.44 × (n × L / √S)^0.467<br>
                <i>Best for: Overland flow on natural surfaces</i></li>
        </ul>
        
        <h3>Required Inputs</h3>
        <ul>
            <li><b>DEM Raster Layer:</b> Digital Elevation Model in any projected coordinate system</li>
            <li><b>Subbasin Polygon Layer:</b> Watershed subbasins as polygons</li>
            <li><b>Output CSV:</b> Location to save comprehensive results</li>
            <li><b>Method Selection:</b> Choose one or more calculation methods</li>
        </ul>
        
        <h3>Method Parameters</h3>
        <ul>
            <li><b>Curve Number (SCS method):</b> 30-98, based on soil type and land use</li>
            <li><b>Runoff Coefficient (FAA method):</b> 0.1-0.95, based on surface characteristics</li>
            <li><b>Roughness Coefficient (Kerby method):</b> 0.02-0.8, Manning's n for surface</li>
        </ul>
        
        <h3>Output Features</h3>
        <ul>
            <li><b>Individual Method Results:</b> TC values from each selected method</li>
            <li><b>Comparative Analysis:</b> Average, standard deviation, recommended TC</li>
            <li><b>Parameter Documentation:</b> All input parameters saved with results</li>
            <li><b>Comprehensive CSV:</b> Complete results for reporting and analysis</li>
        </ul>
        
        <h3>Quick Start</h3>
        <ol>
            <li>Load DEM and subbasin layers in QGIS</li>
            <li>Select appropriate methods for your project type</li>
            <li>Configure parameters or use defaults</li>
            <li>Validate inputs to check for issues</li>
            <li>Run analysis and review comparative results</li>
        </ol>
        
        <h3>Professional Features</h3>
        <ul>
            <li><b>Method Validation:</b> Compare results across multiple approved methods</li>
            <li><b>Regulatory Compliance:</b> FAA and SCS/NRCS methods for official projects</li>
            <li><b>Automated Processing:</b> Batch processing of multiple subbasins</li>
            <li><b>Quality Assurance:</b> Built-in validation and error checking</li>
            <li><b>Documentation:</b> Complete audit trail of parameters and results</li>
        </ul>
        """
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Multi-Method TC Calculator - Help")
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(help_text)
        msg_box.exec_()
    
    def _show_method_info(self):
        """Show detailed method information and selection guidance"""
        method_info = """
        <h2>TC Method Selection Guide</h2>
        
        <h3>🏛️ Kirpich Method (1940)</h3>
        <p><b>Equation:</b> TC = 0.0078 × L^0.77 / S^0.385</p>
        <p><b>Best for:</b> Rural watersheds with well-defined channels</p>
        <p><b>Advantages:</b> Simple, widely accepted, good for natural channels</p>
        <p><b>Limitations:</b> Developed for rural areas, may underestimate urban TC</p>
        
        <h3>✈️ FAA Method (1965)</h3>
        <p><b>Equation:</b> TC = 1.8 × (1.1 - C) × √L / √S</p>
        <p><b>Best for:</b> Urban areas, airport drainage design</p>
        <p><b>Advantages:</b> Accounts for surface characteristics via runoff coefficient</p>
        <p><b>Limitations:</b> Requires good estimate of runoff coefficient</p>
        
        <h3>🌾 SCS/NRCS Lag Time Method (1972)</h3>
        <p><b>Equation:</b> Tlag = (L^0.8 × (1000/CN - 9)^0.7) / (1900 × √S)</p>
        <p><b>Then:</b> TC = 1.67 × Tlag</p>
        <p><b>Best for:</b> Natural watersheds, NRCS compliance projects</p>
        <p><b>Advantages:</b> Widely accepted by NRCS, accounts for soil and land use</p>
        <p><b>Limitations:</b> Requires curve number determination</p>
        
        <h3>🌿 Kerby Method</h3>
        <p><b>Equation:</b> TC = 1.44 × (n × L / √S)^0.467</p>
        <p><b>Best for:</b> Overland flow on natural surfaces</p>
        <p><b>Advantages:</b> Specifically designed for overland flow conditions</p>
        <p><b>Limitations:</b> Mainly for overland flow, not channelized flow</p>
        
        <h3>📊 Comparative Analysis Benefits</h3>
        <ul>
            <li><b>Validation:</b> Multiple methods provide confidence in results</li>
            <li><b>Sensitivity Analysis:</b> See how different approaches affect TC</li>
            <li><b>Regulatory Compliance:</b> Use appropriate method for project requirements</li>
            <li><b>Documentation:</b> Show multiple methods were considered</li>
        </ul>
        
        <h3>💡 Selection Recommendations</h3>
        <ul>
            <li><b>Urban Projects:</b> Kirpich + FAA</li>
            <li><b>Rural/Agricultural:</b> Kirpich + SCS</li>
            <li><b>NRCS Projects:</b> SCS required, Kirpich for comparison</li>
            <li><b>Research/Analysis:</b> All methods for comprehensive comparison</li>
        </ul>
        """
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("TC Method Information")
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(method_info)
        msg_box.exec_()
    
    def _save_settings(self):
        """Save dialog settings"""
        self.settings.setValue('TCCalculatorMulti/selectedMethods', ','.join(self.selected_methods))
        self.settings.setValue('TCCalculatorMulti/curveNumber', self.curve_number_spin.value())
        self.settings.setValue('TCCalculatorMulti/runoffCoeff', self.runoff_coeff_spin.value())
        self.settings.setValue('TCCalculatorMulti/roughnessCoeff', self.roughness_spin.value())
        self.settings.setValue('TCCalculatorMulti/comparativeAnalysis', self.comparative_analysis_check.isChecked())
        self.settings.setValue('TCCalculatorMulti/useHydrologic', self.use_hydrologic_check.isChecked())
        self.settings.setValue('TCCalculatorMulti/autoReproject', self.auto_reproject_check.isChecked())
        self.settings.setValue('TCCalculatorMulti/validateGeometries', self.validate_geometries_check.isChecked())
        self.settings.setValue('TCCalculatorMulti/skipInvalid', self.skip_invalid_check.isChecked())
        self.settings.setValue('TCCalculatorMulti/addToLayer', self.add_to_layer_check.isChecked())
        self.settings.setValue('TCCalculatorMulti/sampleRadius', self.sample_radius_spin.value())
    
    def _restore_settings(self):
        """Restore saved settings"""
        # Restore method selection
        saved_methods = self.settings.value('TCCalculatorMulti/selectedMethods', 'kirpich,faa').split(',')
        self.kirpich_check.setChecked('kirpich' in saved_methods)
        self.faa_check.setChecked('faa' in saved_methods)
        self.scs_check.setChecked('scs' in saved_methods)
        self.kerby_check.setChecked('kerby' in saved_methods)
        
        # Restore parameters
        self.curve_number_spin.setValue(
            self.settings.value('TCCalculatorMulti/curveNumber', 70, type=int)
        )
        self.runoff_coeff_spin.setValue(
            self.settings.value('TCCalculatorMulti/runoffCoeff', 0.50, type=float)
        )
        self.roughness_spin.setValue(
            self.settings.value('TCCalculatorMulti/roughnessCoeff', 0.30, type=float)
        )
        
        # Restore checkboxes
        self.comparative_analysis_check.setChecked(
            self.settings.value('TCCalculatorMulti/comparativeAnalysis', True, type=bool)
        )
        self.use_hydrologic_check.setChecked(
            self.settings.value('TCCalculatorMulti/useHydrologic', True, type=bool)
        )
        self.auto_reproject_check.setChecked(
            self.settings.value('TCCalculatorMulti/autoReproject', False, type=bool)
        )
        self.validate_geometries_check.setChecked(
            self.settings.value('TCCalculatorMulti/validateGeometries', True, type=bool)
        )
        self.skip_invalid_check.setChecked(
            self.settings.value('TCCalculatorMulti/skipInvalid', True, type=bool)
        )
        self.add_to_layer_check.setChecked(
            self.settings.value('TCCalculatorMulti/addToLayer', True, type=bool)
        )
        self.sample_radius_spin.setValue(
            self.settings.value('TCCalculatorMulti/sampleRadius', 10, type=int)
        )
    
    def closeEvent(self, event):
        """Handle dialog close event"""
        self._save_settings()
        event.accept()
