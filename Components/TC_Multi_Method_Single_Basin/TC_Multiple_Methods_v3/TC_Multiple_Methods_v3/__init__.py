"""
Time of Concentration Calculator - Multiple Methods Plugin
Version 3.0.0 - Professional multi-method TC calculator

This plugin initializes the Time of Concentration Calculator with support for
multiple established hydraulic engineering methods.
"""

def classFactory(iface):
    """Load the Time of Concentration plugin"""
    from .time_of_concentration import TimeOfConcentrationPlugin
    return TimeOfConcentrationPlugin(iface)
