"""
Hydro Suite QGIS Plugin
A comprehensive hydrological analysis toolbox for QGIS
"""

def classFactory(iface):
    """Load HydroSuite class from file hydro_suite.py"""
    from .hydro_suite import HydroSuite
    return HydroSuite(iface)