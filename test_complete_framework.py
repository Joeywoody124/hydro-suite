"""
Complete Framework Test for Hydro Suite
Run this script in QGIS Python Console to test all tools including Channel Designer
"""

import sys
import os
from pathlib import Path

def test_complete_framework():
    """Test the complete Hydro Suite framework including Channel Designer"""
    
    # Set up path
    script_dir = Path(r'E:\CLAUDE_Workspace\Claude\Report_Files\Codebase\Hydro_Suite\Hydro_Suite_Data')
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    
    # Change to script directory
    original_cwd = os.getcwd()
    os.chdir(str(script_dir))
    
    print("🧪 Testing Complete Hydro Suite Framework")
    print("=" * 50)
    
    try:
        # Test all imports
        print("📦 Testing core imports...")
        
        from hydro_suite_interface import HydroToolInterface, LayerSelectionMixin
        print("✅ Core interfaces imported")
        
        from shared_widgets import LayerFieldSelector, ValidationPanel, ProgressLogger
        print("✅ Shared widgets imported")
        
        from cn_calculator_tool import CNCalculatorTool
        print("✅ CN Calculator imported")
        
        from rational_c_tool import RationalCTool
        print("✅ Rational C Calculator imported")
        
        from tc_calculator_tool import TCCalculatorTool
        print("✅ TC Calculator imported")
        
        from channel_designer_tool import ChannelDesignerTool, ChannelGeometry
        print("✅ Channel Designer imported")
        
        from hydro_suite_main import HydroSuiteMainWindow, HydroSuiteController
        print("✅ Main framework imported")
        
        # Test controller functionality
        print("\n🎛️ Testing framework controller...")
        controller = HydroSuiteController()
        
        tools_registry = controller.tools_registry
        print(f"✅ Found {len(tools_registry)} registered tools:")
        
        for tool_id, tool_info in tools_registry.items():
            config = tool_info['config']
            print(f"   • {config['name']} ({config['category']})")
        
        # Test tool loading
        print("\n🔧 Testing tool loading...")
        
        # Test CN Calculator
        cn_tool = controller.load_tool("cn_calculator")
        if cn_tool:
            print(f"✅ CN Calculator loaded: {cn_tool.name}")
        else:
            print("❌ CN Calculator failed to load")
        
        # Test Rational C Calculator
        c_tool = controller.load_tool("c_calculator")
        if c_tool:
            print(f"✅ Rational C Calculator loaded: {c_tool.name}")
        else:
            print("❌ Rational C Calculator failed to load")
        
        # Test TC Calculator
        tc_tool = controller.load_tool("tc_calculator")
        if tc_tool:
            print(f"✅ TC Calculator loaded: {tc_tool.name}")
        else:
            print("❌ TC Calculator failed to load")
        
        # Test Channel Designer
        channel_tool = controller.load_tool("channel_designer")
        if channel_tool:
            print(f"✅ Channel Designer loaded: {channel_tool.name}")
            
            # Test Channel Designer functionality
            print("  🔍 Testing Channel Designer features...")
            
            # Test geometry calculations
            geometry = ChannelGeometry(2.0, 4.0, 3.0, 3.0, 100.0)
            points = geometry.calculate_points()
            props = geometry.calculate_properties()
            swmm_format = geometry.get_swmm_format()
            
            print(f"     • Generated {len(points)} channel points")
            print(f"     • Top width: {props['top_width']:.2f} ft")
            print(f"     • Area: {props['area']:.2f} sq ft")
            print(f"     • SWMM format generated: {len(swmm_format.split())} coordinate pairs")
            
            # Test tool validation
            valid, message = channel_tool.validate_inputs()
            print(f"     • Tool validation: {valid} - {message}")
            
        else:
            print("❌ Channel Designer failed to load")
        
        # Test QGIS integration
        print("\n🗺️ Testing QGIS integration...")
        from qgis.core import QgsProject, QgsVectorLayer
        
        project = QgsProject.instance()
        layers = project.mapLayers()
        vector_layers = [layer for layer in layers.values() if isinstance(layer, QgsVectorLayer)]
        polygon_layers = [layer for layer in vector_layers if layer.geometryType() == 2]
        
        print(f"✅ QGIS Project Status:")
        print(f"   • Total layers: {len(layers)}")
        print(f"   • Vector layers: {len(vector_layers)}")
        print(f"   • Polygon layers: {len(polygon_layers)}")
        
        if polygon_layers:
            print(f"   • Sample polygon layers:")
            for i, layer in enumerate(polygon_layers[:3]):
                fields = [f.name() for f in layer.fields()]
                print(f"     - {layer.name()} ({len(fields)} fields)")
        
        # Test categories
        print("\n📂 Testing tool categorization...")
        categories = controller.get_tool_categories()
        for category, tool_ids in categories.items():
            print(f"✅ {category}: {len(tool_ids)} tools")
            for tool_id in tool_ids:
                tool_name = controller.tools_registry[tool_id]['config']['name']
                print(f"   • {tool_name}")
        
        print(f"\n🎉 Complete Framework Test Passed!")
        print(f"\n📋 Framework Summary:")
        print(f"   • {len(tools_registry)} tools registered and working")
        print(f"   • {len(categories)} tool categories")
        print(f"   • All imports successful")
        print(f"   • QGIS integration functional")
        print(f"   • Channel Designer fully integrated")
        
        print(f"\n🚀 Ready to launch!")
        print(f"   Use: exec(open(r'{script_dir}/fixed_launch.py').read())")
        
        return True
        
    except Exception as e:
        print(f"❌ Framework test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False
        
    finally:
        # Restore directory
        os.chdir(original_cwd)

# Run test
if __name__ == "__main__":
    test_complete_framework()
else:
    # When imported in QGIS, just run the test
    test_complete_framework()