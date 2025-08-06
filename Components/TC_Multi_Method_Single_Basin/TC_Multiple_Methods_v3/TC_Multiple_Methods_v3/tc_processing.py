"""
Time of Concentration Processing Module - MULTIPLE METHODS VERSION
Version 3.0.0 - Implements Kirpich, FAA, SCS/NRCS Lag Time, and Kerby methods
Professional-grade implementation with comparative analysis
"""
import os
import csv
import math
import statistics
import traceback
from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict, List, Any, Union
from dataclasses import dataclass

from qgis.core import (
    QgsProject, QgsRasterLayer, QgsVectorLayer,
    QgsField, QgsFeature, QgsGeometry, QgsPoint,
    QgsMessageLog, Qgis, QgsProcessingFeedback,
    QgsApplication, QgsPointXY, QgsWkbTypes,
    QgsProcessingContext, QgsCoordinateReferenceSystem,
    QgsCoordinateTransform, QgsRasterDataProvider,
    QgsSpatialIndex, QgsProcessing, QgsFeatureRequest,
    QgsProcessingException, QgsProcessingAlgorithm,
    QgsVectorDataProvider
)

# QGIS 3.40 Compatibility: PyQt6/PyQt5 handling
try:
    from PyQt6.QtCore import QVariant
    from PyQt6.QtWidgets import QProgressBar
    PYQT_VERSION = 6
except ImportError:
    try:
        from PyQt5.QtCore import QVariant
        from PyQt5.QtWidgets import QProgressBar
        PYQT_VERSION = 5
    except ImportError:
        QVariant = None
        QProgressBar = None
        PYQT_VERSION = 0

# QGIS 3.40 Compatibility: QgsRaster import handling
try:
    from qgis.core import QgsRaster
    _ = QgsRaster.IdentifyFormatValue
    QGSRASTER_AVAILABLE = True
except (ImportError, AttributeError):
    try:
        from qgis.core import QgsRasterIdentifyFormat
        class QgsRaster:
            IdentifyFormatValue = QgsRasterIdentifyFormat.IdentifyFormatValue
        QGSRASTER_AVAILABLE = True
    except ImportError:
        class QgsRaster:
            IdentifyFormatValue = 1
        QGSRASTER_AVAILABLE = False


def safe_log_message(message: str, level=None):
    """Safely log message with QGIS 3.40 compatibility"""
    try:
        if level is None:
            if hasattr(Qgis, 'MessageLevel'):
                level = Qgis.MessageLevel.Info
            else:
                level = Qgis.Info
        QgsMessageLog.logMessage(message, "TC Calculator Multi", level)
    except Exception:
        try:
            QgsMessageLog.logMessage(message, "TC Calculator Multi", 0)  # Info level
        except:
            print(f"TC Calculator Multi: {message}")  # Last resort


class TCProcessingError(Exception):
    """Custom exception for TC processing errors"""
    pass


@dataclass
class TCParameters:
    """Container for all parameters needed for TC calculations"""
    flow_length_ft: float
    elevation_diff_ft: float
    slope_ft_ft: float
    upstream_elev_ft: float
    downstream_elev_ft: float
    
    # Optional parameters with defaults
    curve_number: Optional[float] = 70.0  # SCS method
    runoff_coefficient: Optional[float] = 0.5  # FAA method
    roughness_coefficient: Optional[float] = 0.3  # Kerby method
    
    def __post_init__(self):
        """Validate parameters after initialization"""
        if self.flow_length_ft <= 0:
            raise ValueError("Flow length must be positive")
        if self.slope_ft_ft <= 0:
            raise ValueError("Slope must be positive")
        if self.curve_number and not (30 <= self.curve_number <= 98):
            raise ValueError("Curve number must be between 30 and 98")
        if self.runoff_coefficient and not (0.1 <= self.runoff_coefficient <= 0.95):
            raise ValueError("Runoff coefficient must be between 0.1 and 0.95")


@dataclass
class TCResults:
    """Container for Time of Concentration results from all methods"""
    subbasin_id: Any
    parameters: TCParameters
    
    # Individual method results (minutes)
    tc_kirpich_min: Optional[float] = None
    tc_faa_min: Optional[float] = None
    tc_scs_min: Optional[float] = None
    tc_kerby_min: Optional[float] = None
    
    # Comparative analysis
    tc_average_min: Optional[float] = None
    tc_std_dev_min: Optional[float] = None
    tc_recommended_min: Optional[float] = None
    
    def calculate_statistics(self, selected_methods: List[str]):
        """Calculate comparative statistics for selected methods"""
        valid_results = []
        
        method_map = {
            'kirpich': self.tc_kirpich_min,
            'faa': self.tc_faa_min,
            'scs': self.tc_scs_min,
            'kerby': self.tc_kerby_min
        }
        
        for method in selected_methods:
            tc_value = method_map.get(method)
            if tc_value is not None and tc_value > 0:
                valid_results.append(tc_value)
        
        if len(valid_results) >= 2:
            self.tc_average_min = statistics.mean(valid_results)
            self.tc_std_dev_min = statistics.stdev(valid_results) if len(valid_results) > 1 else 0.0
            
            # Recommended value: median for robustness
            self.tc_recommended_min = statistics.median(valid_results)
        elif len(valid_results) == 1:
            self.tc_average_min = valid_results[0]
            self.tc_std_dev_min = 0.0
            self.tc_recommended_min = valid_results[0]


class TCMethodBase(ABC):
    """Abstract base class for Time of Concentration calculation methods"""
    
    def __init__(self, parameters: TCParameters):
        self.parameters = parameters
    
    @abstractmethod
    def calculate(self) -> float:
        """Calculate time of concentration in minutes"""
        pass
    
    @property
    @abstractmethod
    def method_name(self) -> str:
        """Return the method name"""
        pass
    
    @property
    @abstractmethod
    def reference(self) -> str:
        """Return the method reference/citation"""
        pass


class KirpichMethod(TCMethodBase):
    """Kirpich equation implementation (1940)"""
    
    def calculate(self) -> float:
        """
        Kirpich equation: TC = 0.0078 × L^0.77 / S^0.385
        Where: TC = minutes, L = flow length (feet), S = slope (ft/ft)
        """
        L = self.parameters.flow_length_ft
        S = max(self.parameters.slope_ft_ft, 0.001)  # Minimum slope protection
        
        tc_minutes = 0.0078 * (L ** 0.77) / (S ** 0.385)
        return max(tc_minutes, 5.0)  # Minimum 5 minutes
    
    @property
    def method_name(self) -> str:
        return "Kirpich"
    
    @property
    def reference(self) -> str:
        return "Kirpich, Z.P. (1940). Time of concentration of small agricultural watersheds. Civil Engineering, 10(6), 362."


class FAAMethod(TCMethodBase):
    """Federal Aviation Administration method implementation (1965)"""
    
    def calculate(self) -> float:
        """
        FAA equation: TC = 1.8 × (1.1 - C) × √(L) / √(S)
        Where: TC = minutes, C = runoff coefficient, L = length (feet), S = slope (ft/ft)
        
        Note: The original FAA method from AC 150/5320-5B uses:
        TC = 1.8 × (1.1 - C) × √(L/1000) / √(S)
        where L is in feet and the 1000 factor normalizes the length
        """
        L = self.parameters.flow_length_ft
        S = max(self.parameters.slope_ft_ft, 0.001)  # Minimum slope protection
        C = self.parameters.runoff_coefficient or 0.5  # Default runoff coefficient
        
        # Ensure runoff coefficient is within valid range
        C = max(0.1, min(0.95, C))
        
        # Use the corrected FAA formula with length normalization
        # This matches the original FAA Advisory Circular AC 150/5320-5B
        tc_minutes = 1.8 * (1.1 - C) * math.sqrt(L / 1000.0) / math.sqrt(S)
        
        return max(tc_minutes, 5.0)  # Minimum 5 minutes
    
    @property
    def method_name(self) -> str:
        return "FAA"
    
    @property
    def reference(self) -> str:
        return "Federal Aviation Administration (1965). Airport Drainage Design. FAA Advisory Circular AC 150/5320-5B."


class SCSLagTimeMethod(TCMethodBase):
    """SCS/NRCS Lag Time method implementation (1972)"""
    
    def calculate(self) -> float:
        """
        SCS Lag Time equation: Tlag = (L^0.8 × (1000/CN - 9)^0.7) / (1900 × √S)
        Time of Concentration: TC = 1.67 × Tlag
        Where: L = length (feet), CN = curve number, S = slope (%)
        """
        L = self.parameters.flow_length_ft
        S_percent = self.parameters.slope_ft_ft * 100  # Convert to percent
        S_percent = max(S_percent, 0.1)  # Minimum slope protection
        CN = self.parameters.curve_number or 70.0  # Default curve number
        
        # Ensure curve number is within valid range
        CN = max(30, min(98, CN))
        
        # Calculate lag time in hours
        numerator = (L ** 0.8) * ((1000.0 / CN - 9.0) ** 0.7)
        denominator = 1900.0 * math.sqrt(S_percent)
        
        tlag_hours = numerator / denominator
        tc_minutes = 1.67 * tlag_hours * 60.0  # Convert to minutes
        
        return max(tc_minutes, 5.0)  # Minimum 5 minutes
    
    @property
    def method_name(self) -> str:
        return "SCS/NRCS"
    
    @property
    def reference(self) -> str:
        return "USDA-SCS (1972). National Engineering Handbook, Section 4: Hydrology. Chapter 15."


class KerbyMethod(TCMethodBase):
    """Kerby equation implementation for overland flow"""
    
    def calculate(self) -> float:
        """
        Kerby equation: TC = 1.44 × (n × L / √S)^0.467
        Where: TC = minutes, n = roughness coefficient, L = length (feet), S = slope (ft/ft)
        """
        L = self.parameters.flow_length_ft
        S = max(self.parameters.slope_ft_ft, 0.001)  # Minimum slope protection
        n = self.parameters.roughness_coefficient or 0.3  # Default roughness
        
        # Ensure roughness coefficient is within reasonable range
        n = max(0.02, min(0.8, n))
        
        tc_minutes = 1.44 * ((n * L / math.sqrt(S)) ** 0.467)
        return max(tc_minutes, 5.0)  # Minimum 5 minutes
    
    @property
    def method_name(self) -> str:
        return "Kerby"
    
    @property
    def reference(self) -> str:
        return "Kerby, W.S. (1959). Time of concentration for overland flow. Civil Engineering, 29(3), 174."


class TCMethodFactory:
    """Factory for creating TC calculation method instances"""
    
    @staticmethod
    def create_method(method_name: str, parameters: TCParameters) -> TCMethodBase:
        """Create a TC method instance"""
        methods = {
            'kirpich': KirpichMethod,
            'faa': FAAMethod,
            'scs': SCSLagTimeMethod,
            'kerby': KerbyMethod
        }
        
        if method_name.lower() not in methods:
            raise ValueError(f"Unknown TC method: {method_name}")
        
        return methods[method_name.lower()](parameters)
    
    @staticmethod
    def get_available_methods() -> List[str]:
        """Get list of available method names"""
        return ['kirpich', 'faa', 'scs', 'kerby']


class TimeOfConcentrationCalculator:
    """Main class for Time of Concentration calculations with multiple methods"""
    
    # SHAPEFILE-COMPATIBLE field names (≤10 characters)
    FIELD_FLOW_LENGTH_FT = 'flow_ft'
    FIELD_ELEV_DIFF_FT = 'elev_ft'
    FIELD_SLOPE_FT_FT = 'slope_ff'
    FIELD_UPSTREAM_ELEV_FT = 'up_elev'
    FIELD_DOWNSTREAM_ELEV_FT = 'dn_elev'
    
    # Method-specific result fields
    FIELD_TC_KIRPICH = 'tc_kir'
    FIELD_TC_FAA = 'tc_faa'
    FIELD_TC_SCS = 'tc_scs'
    FIELD_TC_KERBY = 'tc_kerby'
    
    # Comparative analysis fields
    FIELD_TC_AVERAGE = 'tc_avg'
    FIELD_TC_STD_DEV = 'tc_std'
    FIELD_TC_RECOMMENDED = 'tc_rec'
    
    # Parameter fields
    FIELD_CURVE_NUMBER = 'curve_n'
    FIELD_RUNOFF_COEFF = 'runoff_c'
    FIELD_ROUGHNESS_N = 'rough_n'
    
    # Conversion constants
    METERS_TO_FEET = 3.28084
    FEET_TO_METERS = 0.3048
    
    def __init__(self):
        """Initialize the calculator with QGIS 3.40 compatibility"""
        safe_log_message("=== TC Calculator Multi-Method v3.0.0 ===")
        safe_log_message("Available methods: Kirpich, FAA, SCS/NRCS, Kerby")
        self.coordinate_transform = None
        
    def calculate_tc_for_subbasins(
        self,
        dem_layer: QgsRasterLayer,
        subbasin_layer: QgsVectorLayer,
        output_csv: str,
        selected_methods: List[str] = None,
        id_field: Optional[str] = None,
        curve_number: float = 70.0,
        runoff_coefficient: float = 0.5,
        roughness_coefficient: float = 0.3,
        progress_bar: Optional[QProgressBar] = None
    ) -> bool:
        """
        Main processing function with multiple TC calculation methods
        """
        if selected_methods is None:
            selected_methods = ['kirpich', 'faa']  # Default methods
            
        safe_log_message(f"=== STARTING MULTI-METHOD TC CALCULATION (v3.0.0) ===")
        safe_log_message(f"Selected methods: {', '.join(selected_methods)}")
        
        try:
            # STEP 1: Input validation
            safe_log_message("STEP 1: Input validation")
            self._validate_inputs(dem_layer, subbasin_layer, selected_methods)
            safe_log_message("✓ Input validation passed")
            
            # STEP 2: Coordinate transformation setup
            safe_log_message("STEP 2: Coordinate transformation setup")
            crs_compatible = self._setup_coordinate_transform(dem_layer, subbasin_layer)
            if not crs_compatible:
                safe_log_message("CRS mismatch detected - using coordinate transformation")
            safe_log_message("✓ Coordinate transformation setup completed")
            
            # STEP 3: Add output fields for all methods
            safe_log_message("STEP 3: Adding output fields for selected methods")
            self._add_output_fields_multi_method(subbasin_layer, selected_methods)
            safe_log_message("✓ Output fields added successfully")
            
            # STEP 4: Process subbasins with multiple methods
            safe_log_message("STEP 4: Processing subbasins with multiple methods")
            results = self._process_subbasins_multi_method(
                dem_layer, 
                subbasin_layer, 
                selected_methods,
                id_field,
                curve_number,
                runoff_coefficient,
                roughness_coefficient,
                progress_bar
            )
            safe_log_message(f"✓ Processed {len(results) if results else 0} subbasins")
            
            # STEP 5: Save comprehensive results
            if results:
                self._save_results_to_csv_multi_method(results, output_csv, selected_methods)
                safe_log_message(f"SUCCESS: {len(results)} subbasins processed with {len(selected_methods)} methods")
                return True
            else:
                safe_log_message("No results generated")
                return False
                
        except Exception as e:
            safe_log_message(f"PROCESSING FAILED: {str(e)}")
            safe_log_message(f"Full traceback: {traceback.format_exc()}")
            
            # Try to rollback any changes
            try:
                if subbasin_layer.isEditable():
                    subbasin_layer.rollBack()
            except:
                pass
                
            return False
    
    def _validate_inputs(self, dem_layer: QgsRasterLayer, subbasin_layer: QgsVectorLayer, selected_methods: List[str]) -> None:
        """Validate input layers and selected methods"""
        if not dem_layer or not dem_layer.isValid():
            raise TCProcessingError("Invalid DEM layer")
            
        if not subbasin_layer or not subbasin_layer.isValid():
            raise TCProcessingError("Invalid subbasin layer")
            
        if subbasin_layer.featureCount() == 0:
            raise TCProcessingError("Subbasin layer contains no features")
        
        available_methods = TCMethodFactory.get_available_methods()
        for method in selected_methods:
            if method.lower() not in available_methods:
                raise TCProcessingError(f"Unknown method: {method}")
        
        safe_log_message(f"  DEM: {dem_layer.name()}, CRS: {dem_layer.crs().authid()}")
        safe_log_message(f"  Subbasin: {subbasin_layer.name()}, CRS: {subbasin_layer.crs().authid()}")
        safe_log_message(f"  Methods: {', '.join(selected_methods)}")
        
    def _setup_coordinate_transform(self, dem_layer: QgsRasterLayer, subbasin_layer: QgsVectorLayer) -> bool:
        """Set up coordinate transformation if layers have different CRS"""
        dem_crs = dem_layer.crs()
        subbasin_crs = subbasin_layer.crs()
        
        if dem_crs != subbasin_crs:
            safe_log_message(f"  CRS mismatch - DEM: {dem_crs.authid()}, Subbasins: {subbasin_crs.authid()}")
            
            try:
                self.coordinate_transform = QgsCoordinateTransform(
                    subbasin_crs, 
                    dem_crs, 
                    QgsProject.instance()
                )
                safe_log_message(f"  Coordinate transformation: {subbasin_crs.authid()} → {dem_crs.authid()}")
                return False
            except Exception as e:
                raise TCProcessingError(f"Cannot set up coordinate transformation: {str(e)}")
        else:
            self.coordinate_transform = None
            return True
    
    def _add_output_fields_multi_method(self, layer: QgsVectorLayer, selected_methods: List[str]) -> None:
        """Add output fields for all selected methods with shapefile compatibility"""
        try:
            safe_log_message("  Checking existing fields...")
            
            provider = layer.dataProvider()
            existing_fields = [field.name() for field in layer.fields()]
            safe_log_message(f"  Current field count: {len(existing_fields)}")
            
            # Base field definitions (always needed)
            field_definitions = [
                (self.FIELD_FLOW_LENGTH_FT, QVariant.Double, 10, 2, "Flow length (ft)"),
                (self.FIELD_ELEV_DIFF_FT, QVariant.Double, 10, 2, "Elevation diff (ft)"),
                (self.FIELD_SLOPE_FT_FT, QVariant.Double, 10, 6, "Slope (ft/ft)"),
                (self.FIELD_UPSTREAM_ELEV_FT, QVariant.Double, 10, 2, "Upstream elev (ft)"),
                (self.FIELD_DOWNSTREAM_ELEV_FT, QVariant.Double, 10, 2, "Downstream elev (ft)")
            ]
            
            # Add method-specific fields
            method_fields = {
                'kirpich': (self.FIELD_TC_KIRPICH, "TC Kirpich (min)"),
                'faa': (self.FIELD_TC_FAA, "TC FAA (min)"),
                'scs': (self.FIELD_TC_SCS, "TC SCS (min)"),
                'kerby': (self.FIELD_TC_KERBY, "TC Kerby (min)")
            }
            
            for method in selected_methods:
                if method.lower() in method_fields:
                    field_name, description = method_fields[method.lower()]
                    field_definitions.append((field_name, QVariant.Double, 10, 2, description))
            
            # Add comparative analysis fields if multiple methods selected
            if len(selected_methods) > 1:
                field_definitions.extend([
                    (self.FIELD_TC_AVERAGE, QVariant.Double, 10, 2, "TC Average (min)"),
                    (self.FIELD_TC_STD_DEV, QVariant.Double, 10, 3, "TC Std Dev (min)"),
                    (self.FIELD_TC_RECOMMENDED, QVariant.Double, 10, 2, "TC Recommended (min)")
                ])
            
            # Add parameter fields
            parameter_fields = []
            if 'scs' in [m.lower() for m in selected_methods]:
                parameter_fields.append((self.FIELD_CURVE_NUMBER, QVariant.Int, 3, 0, "Curve Number"))
            if 'faa' in [m.lower() for m in selected_methods]:
                parameter_fields.append((self.FIELD_RUNOFF_COEFF, QVariant.Double, 5, 3, "Runoff Coeff"))
            if 'kerby' in [m.lower() for m in selected_methods]:
                parameter_fields.append((self.FIELD_ROUGHNESS_N, QVariant.Double, 5, 3, "Roughness n"))
            
            field_definitions.extend(parameter_fields)
            
            # Check which fields need to be added
            fields_to_add = []
            for field_name, field_type, length, precision, description in field_definitions:
                field_exists = False
                for existing_field in existing_fields:
                    if existing_field == field_name or existing_field.startswith(field_name[:6]):
                        field_exists = True
                        safe_log_message(f"  Field '{field_name}' exists as '{existing_field}'")
                        break
                
                if not field_exists:
                    field = QgsField(field_name, field_type)
                    field.setLength(length)
                    field.setPrecision(precision)
                    fields_to_add.append((field, field_name, description))
                    safe_log_message(f"  Will add: '{field_name}' - {description}")
            
            if fields_to_add:
                safe_log_message(f"  Adding {len(fields_to_add)} new fields...")
                
                qgs_fields = [field_tuple[0] for field_tuple in fields_to_add]
                result = provider.addAttributes(qgs_fields)
                
                if result:
                    layer.updateFields()
                    safe_log_message(f"  ✓ Fields added successfully")
                else:
                    raise TCProcessingError("Failed to add attributes to layer")
            else:
                safe_log_message("  No new fields needed - using existing fields")
                
        except Exception as e:
            safe_log_message(f"Error adding output fields: {str(e)}")
            raise TCProcessingError(f"Failed to add output fields: {str(e)}")
    
    def _process_subbasins_multi_method(
        self,
        dem_layer: QgsRasterLayer,
        subbasin_layer: QgsVectorLayer,
        selected_methods: List[str],
        id_field: Optional[str],
        curve_number: float,
        runoff_coefficient: float,
        roughness_coefficient: float,
        progress_bar: Optional[QProgressBar]
    ) -> List[TCResults]:
        """Process all subbasins with multiple TC calculation methods"""
        results = []
        feature_count = subbasin_layer.featureCount()
        
        safe_log_message(f"  Processing {feature_count} subbasins with {len(selected_methods)} methods...")
        
        # Start editing the layer
        if not subbasin_layer.startEditing():
            raise TCProcessingError("Could not start editing subbasin layer")
        
        try:
            for current, feature in enumerate(subbasin_layer.getFeatures()):
                # Update progress
                if progress_bar:
                    progress_bar.setValue(int((current / feature_count) * 100))
                
                # Get subbasin ID
                subbasin_id = self._get_feature_id(feature, id_field)
                safe_log_message(f"  Processing subbasin {subbasin_id} ({current+1}/{feature_count})")
                
                # Skip invalid geometries
                if not feature.geometry() or not feature.geometry().isGeosValid():
                    safe_log_message(f"    Skipping - invalid geometry")
                    continue
                
                try:
                    # Calculate TC for this feature using multiple methods
                    result = self._calculate_tc_for_feature_multi_method(
                        feature,
                        dem_layer,
                        subbasin_id,
                        selected_methods,
                        curve_number,
                        runoff_coefficient,
                        roughness_coefficient
                    )
                    
                    if result:
                        results.append(result)
                        
                        # Log method results
                        method_results = []
                        if result.tc_kirpich_min:
                            method_results.append(f"Kirpich: {result.tc_kirpich_min:.2f}")
                        if result.tc_faa_min:
                            method_results.append(f"FAA: {result.tc_faa_min:.2f}")
                        if result.tc_scs_min:
                            method_results.append(f"SCS: {result.tc_scs_min:.2f}")
                        if result.tc_kerby_min:
                            method_results.append(f"Kerby: {result.tc_kerby_min:.2f}")
                        
                        safe_log_message(f"    TC results: {', '.join(method_results)} minutes")
                        if result.tc_recommended_min:
                            safe_log_message(f"    Recommended: {result.tc_recommended_min:.2f} minutes")
                        
                        # Update feature attributes
                        self._update_feature_attributes_multi_method(subbasin_layer, feature, result, selected_methods)
                    else:
                        safe_log_message(f"    Failed to calculate TC")
                        
                except Exception as e:
                    safe_log_message(f"    Error: {str(e)}")
                    continue
            
            # Commit changes
            if not subbasin_layer.commitChanges():
                raise TCProcessingError("Failed to commit changes to subbasin layer")
                
            if progress_bar:
                progress_bar.setValue(100)
                
        except Exception as e:
            subbasin_layer.rollBack()
            raise e
            
        return results
    
    def _get_feature_id(self, feature: QgsFeature, id_field: Optional[str]) -> Any:
        """Get feature identifier"""
        if id_field and id_field in [field.name() for field in feature.fields()]:
            return feature[id_field]
        
        # Try common ID field names
        for field_name in ['Name', 'name', 'ID', 'id', 'FID', 'fid']:
            if field_name in [field.name() for field in feature.fields()]:
                return feature[field_name]
        
        # Fall back to feature ID
        return feature.id()
    
    def _calculate_tc_for_feature_multi_method(
        self,
        feature: QgsFeature,
        dem_layer: QgsRasterLayer,
        subbasin_id: Any,
        selected_methods: List[str],
        curve_number: float,
        runoff_coefficient: float,
        roughness_coefficient: float
    ) -> Optional[TCResults]:
        """Calculate TC for a single feature using multiple methods"""
        geometry = feature.geometry()
        
        # Calculate geometric flow path
        flow_path_result = self._calculate_geometric_flow_path(geometry)
        
        if not flow_path_result:
            safe_log_message(f"    Could not calculate flow path")
            return None
        
        flow_path, upstream_point, downstream_point = flow_path_result
        
        # Transform points to DEM CRS if needed
        upstream_point_transformed = self._transform_point(upstream_point)
        downstream_point_transformed = self._transform_point(downstream_point)
        
        # Get elevations
        upstream_elev = self._sample_dem_at_point(dem_layer, upstream_point_transformed)
        downstream_elev = self._sample_dem_at_point(dem_layer, downstream_point_transformed)
        
        if upstream_elev is None or downstream_elev is None:
            safe_log_message(f"    Could not obtain elevations")
            return None
        
        # Ensure upstream is higher than downstream
        if upstream_elev < downstream_elev:
            upstream_elev, downstream_elev = downstream_elev, upstream_elev
        
        # Convert to feet and create parameters
        flow_length_ft = flow_path.length() * self.METERS_TO_FEET
        upstream_elev_ft = upstream_elev * self.METERS_TO_FEET
        downstream_elev_ft = downstream_elev * self.METERS_TO_FEET
        elevation_diff_ft = upstream_elev_ft - downstream_elev_ft
        
        # Ensure minimum values
        flow_length_ft = max(flow_length_ft, 1.0)
        elevation_diff_ft = max(elevation_diff_ft, 0.1)
        
        slope_ft_ft = elevation_diff_ft / flow_length_ft
        
        # Create parameters object
        try:
            parameters = TCParameters(
                flow_length_ft=flow_length_ft,
                elevation_diff_ft=elevation_diff_ft,
                slope_ft_ft=slope_ft_ft,
                upstream_elev_ft=upstream_elev_ft,
                downstream_elev_ft=downstream_elev_ft,
                curve_number=curve_number,
                runoff_coefficient=runoff_coefficient,
                roughness_coefficient=roughness_coefficient
            )
        except ValueError as e:
            safe_log_message(f"    Parameter validation error: {str(e)}")
            return None
        
        # Create results object
        results = TCResults(subbasin_id=subbasin_id, parameters=parameters)
        
        # Calculate TC using selected methods
        for method_name in selected_methods:
            try:
                method = TCMethodFactory.create_method(method_name, parameters)
                tc_value = method.calculate()
                
                # Store result in appropriate field
                if method_name.lower() == 'kirpich':
                    results.tc_kirpich_min = round(tc_value, 2)
                elif method_name.lower() == 'faa':
                    results.tc_faa_min = round(tc_value, 2)
                elif method_name.lower() == 'scs':
                    results.tc_scs_min = round(tc_value, 2)
                elif method_name.lower() == 'kerby':
                    results.tc_kerby_min = round(tc_value, 2)
                    
                safe_log_message(f"      {method.method_name}: {tc_value:.2f} minutes")
                
            except Exception as e:
                safe_log_message(f"      Error calculating {method_name}: {str(e)}")
                continue
        
        # Calculate comparative statistics
        results.calculate_statistics(selected_methods)
        
        return results
    
    def _transform_point(self, point: QgsPointXY) -> QgsPointXY:
        """Transform point coordinates if transformation is set up"""
        if self.coordinate_transform:
            try:
                return self.coordinate_transform.transform(point)
            except Exception:
                return point
        return point
    
    def _calculate_geometric_flow_path(self, geometry: QgsGeometry) -> Optional[Tuple[QgsGeometry, QgsPointXY, QgsPointXY]]:
        """Calculate flow path using geometric approach - QGIS 3.40 compatible"""
        if geometry.type() != QgsWkbTypes.PolygonGeometry:
            return None
        
        # Get boundary points using QGIS 3.40 compatible methods
        try:
            vertex_iterator = geometry.vertices()
            points = list(vertex_iterator)
            
            # Convert to QgsPointXY
            xy_points = []
            for vertex in points:
                xy_points.append(QgsPointXY(vertex.x(), vertex.y()))
                
        except Exception as e:
            safe_log_message(f"    Error extracting geometry vertices: {str(e)}")
            return None
        
        if len(xy_points) < 2:
            safe_log_message(f"    Insufficient points: {len(xy_points)}")
            return None
        
        safe_log_message(f"    Extracted {len(xy_points)} boundary points")
        
        # Find the two most distant points
        max_distance = 0
        point1 = None
        point2 = None
        
        for i in range(len(xy_points)):
            for j in range(i + 1, len(xy_points)):
                dist = xy_points[i].distance(xy_points[j])
                if dist > max_distance:
                    max_distance = dist
                    point1 = xy_points[i]
                    point2 = xy_points[j]
        
        if point1 is None or point2 is None:
            safe_log_message(f"    Could not find two distinct points")
            return None
        
        safe_log_message(f"    Max distance between points: {max_distance:.2f}m")
        
        # Create flow path line
        flow_path = QgsGeometry.fromPolylineXY([point1, point2])
        
        # Determine upstream/downstream based on Y coordinate (higher Y = upstream)
        if point1.y() > point2.y():
            upstream_point = point1
            downstream_point = point2
        else:
            upstream_point = point2
            downstream_point = point1
        
        return flow_path, upstream_point, downstream_point
    
    def _sample_dem_at_point(self, dem_layer: QgsRasterLayer, point: QgsPointXY) -> Optional[float]:
        """Sample DEM elevation at a specific point"""
        try:
            provider = dem_layer.dataProvider()
            
            # Try the identify method
            identify_result = provider.identify(point, QgsRaster.IdentifyFormatValue)
            
            if identify_result.isValid():
                results = identify_result.results()
                if results and 1 in results:
                    value = results[1]
                    nodata = provider.sourceNoDataValue(1)
                    
                    if value is not None and value != nodata and not math.isnan(value):
                        return float(value)
            
            # Try sampling nearby points if exact point fails
            return self._sample_nearby_points(dem_layer, point)
            
        except Exception:
            return None
    
    def _sample_nearby_points(self, dem_layer: QgsRasterLayer, center_point: QgsPointXY, radius: float = 50.0) -> Optional[float]:
        """Sample DEM using nearby points within radius"""
        provider = dem_layer.dataProvider()
        
        offsets = [
            (0, 0), (radius, 0), (0, radius), (-radius, 0), (0, -radius),
            (radius, radius), (-radius, radius), (-radius, -radius), (radius, -radius)
        ]
        
        valid_values = []
        
        for dx, dy in offsets:
            sample_point = QgsPointXY(center_point.x() + dx, center_point.y() + dy)
            
            try:
                identify_result = provider.identify(sample_point, QgsRaster.IdentifyFormatValue)
                
                if identify_result.isValid():
                    results = identify_result.results()
                    if results and 1 in results:
                        value = results[1]
                        nodata = provider.sourceNoDataValue(1)
                        
                        if value is not None and value != nodata and not math.isnan(value):
                            valid_values.append(float(value))
                            
            except Exception:
                continue
        
        if valid_values:
            return sum(valid_values) / len(valid_values)
        
        return None
    
    def _update_feature_attributes_multi_method(self, layer: QgsVectorLayer, feature: QgsFeature, result: TCResults, selected_methods: List[str]) -> None:
        """Update feature attributes with results from multiple methods"""
        fields = layer.fields()
        
        # Create field mapping for all possible fields
        field_map = {
            # Base parameters
            self.FIELD_FLOW_LENGTH_FT: result.parameters.flow_length_ft,
            self.FIELD_ELEV_DIFF_FT: result.parameters.elevation_diff_ft,
            self.FIELD_SLOPE_FT_FT: result.parameters.slope_ft_ft,
            self.FIELD_UPSTREAM_ELEV_FT: result.parameters.upstream_elev_ft,
            self.FIELD_DOWNSTREAM_ELEV_FT: result.parameters.downstream_elev_ft,
            
            # Method results
            self.FIELD_TC_KIRPICH: result.tc_kirpich_min,
            self.FIELD_TC_FAA: result.tc_faa_min,
            self.FIELD_TC_SCS: result.tc_scs_min,
            self.FIELD_TC_KERBY: result.tc_kerby_min,
            
            # Comparative analysis
            self.FIELD_TC_AVERAGE: result.tc_average_min,
            self.FIELD_TC_STD_DEV: result.tc_std_dev_min,
            self.FIELD_TC_RECOMMENDED: result.tc_recommended_min,
            
            # Parameters
            self.FIELD_CURVE_NUMBER: result.parameters.curve_number,
            self.FIELD_RUNOFF_COEFF: result.parameters.runoff_coefficient,
            self.FIELD_ROUGHNESS_N: result.parameters.roughness_coefficient
        }
        
        # Update only fields that exist and have values
        for field_name, value in field_map.items():
            if value is not None:
                # Look for exact match first
                layer_field_idx = fields.indexFromName(field_name)
                if layer_field_idx >= 0:
                    layer.changeAttributeValue(feature.id(), layer_field_idx, value)
                    continue
                
                # Look for truncated match
                for field_idx in range(fields.count()):
                    layer_field_name = fields[field_idx].name()
                    if layer_field_name.startswith(field_name[:6]):
                        layer.changeAttributeValue(feature.id(), field_idx, value)
                        break
    
    def _save_results_to_csv_multi_method(self, results: List[TCResults], output_path: str, selected_methods: List[str]) -> None:
        """Save comprehensive results to CSV file"""
        if not results:
            raise TCProcessingError("No results to save")
        
        # Create comprehensive CSV headers
        headers = [
            'Subbasin_ID',
            'Flow_Length_ft',
            'Elevation_Diff_ft',
            'Slope_ft_per_ft',
            'Upstream_Elevation_ft',
            'Downstream_Elevation_ft'
        ]
        
        # Add method-specific headers
        method_headers = {
            'kirpich': 'TC_Kirpich_min',
            'faa': 'TC_FAA_min',
            'scs': 'TC_SCS_min',
            'kerby': 'TC_Kerby_min'
        }
        
        for method in selected_methods:
            if method.lower() in method_headers:
                headers.append(method_headers[method.lower()])
        
        # Add comparative analysis headers if multiple methods
        if len(selected_methods) > 1:
            headers.extend([
                'TC_Average_min',
                'TC_StdDev_min',
                'TC_Recommended_min'
            ])
        
        # Add parameter headers
        parameter_headers = []
        if 'scs' in [m.lower() for m in selected_methods]:
            parameter_headers.append('Curve_Number')
        if 'faa' in [m.lower() for m in selected_methods]:
            parameter_headers.append('Runoff_Coefficient')
        if 'kerby' in [m.lower() for m in selected_methods]:
            parameter_headers.append('Roughness_n')
        
        headers.extend(parameter_headers)
        
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                
                # Write data
                for result in results:
                    row = {
                        'Subbasin_ID': result.subbasin_id,
                        'Flow_Length_ft': result.parameters.flow_length_ft,
                        'Elevation_Diff_ft': result.parameters.elevation_diff_ft,
                        'Slope_ft_per_ft': result.parameters.slope_ft_ft,
                        'Upstream_Elevation_ft': result.parameters.upstream_elev_ft,
                        'Downstream_Elevation_ft': result.parameters.downstream_elev_ft
                    }
                    
                    # Add method results
                    method_values = {
                        'kirpich': result.tc_kirpich_min,
                        'faa': result.tc_faa_min,
                        'scs': result.tc_scs_min,
                        'kerby': result.tc_kerby_min
                    }
                    
                    for method in selected_methods:
                        if method.lower() in method_headers and method.lower() in method_values:
                            header = method_headers[method.lower()]
                            value = method_values[method.lower()]
                            if value is not None:
                                row[header] = value
                    
                    # Add comparative analysis
                    if len(selected_methods) > 1:
                        if result.tc_average_min is not None:
                            row['TC_Average_min'] = result.tc_average_min
                        if result.tc_std_dev_min is not None:
                            row['TC_StdDev_min'] = result.tc_std_dev_min
                        if result.tc_recommended_min is not None:
                            row['TC_Recommended_min'] = result.tc_recommended_min
                    
                    # Add parameters
                    if 'Curve_Number' in headers and result.parameters.curve_number:
                        row['Curve_Number'] = result.parameters.curve_number
                    if 'Runoff_Coefficient' in headers and result.parameters.runoff_coefficient:
                        row['Runoff_Coefficient'] = result.parameters.runoff_coefficient
                    if 'Roughness_n' in headers and result.parameters.roughness_coefficient:
                        row['Roughness_n'] = result.parameters.roughness_coefficient
                    
                    writer.writerow(row)
            
            safe_log_message(f"  Comprehensive results saved to: {output_path}")
            safe_log_message(f"  Methods included: {', '.join(selected_methods)}")
            
        except Exception as e:
            raise TCProcessingError(f"Failed to save CSV file: {str(e)}")


# Estimate parameter functions for enhanced automation
def estimate_curve_number_from_land_use(land_use_type: str = 'mixed') -> float:
    """Estimate curve number based on land use type"""
    cn_map = {
        'urban_residential': 75,
        'urban_commercial': 85,
        'urban_industrial': 90,
        'agricultural': 65,
        'forest': 55,
        'grassland': 60,
        'mixed': 70,
        'default': 70
    }
    return cn_map.get(land_use_type.lower(), 70)


def estimate_runoff_coefficient_from_land_use(land_use_type: str = 'mixed') -> float:
    """Estimate runoff coefficient based on land use type"""
    c_map = {
        'concrete': 0.85,
        'asphalt': 0.90,
        'urban_dense': 0.80,
        'urban_residential': 0.60,
        'commercial': 0.75,
        'industrial': 0.80,
        'agricultural': 0.30,
        'forest': 0.20,
        'grassland': 0.25,
        'mixed': 0.50,
        'default': 0.50
    }
    return c_map.get(land_use_type.lower(), 0.50)


def estimate_roughness_coefficient_from_land_cover(land_cover_type: str = 'mixed') -> float:
    """Estimate Manning's roughness coefficient based on land cover"""
    n_map = {
        'concrete': 0.02,
        'asphalt': 0.02,
        'gravel': 0.05,
        'short_grass': 0.15,
        'dense_grass': 0.24,
        'light_brush': 0.40,
        'dense_brush': 0.60,
        'forest': 0.80,
        'mixed': 0.30,
        'default': 0.30
    }
    return n_map.get(land_cover_type.lower(), 0.30)
