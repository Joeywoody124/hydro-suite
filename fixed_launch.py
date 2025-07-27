"""
Fixed launcher that properly handles QGIS Python console imports
"""

import sys
import os
import importlib.util

def load_hydro_suite():
    print("🔧 Fixed Hydro Suite Launcher")
    print("=" * 50)
    
    # Define the directory
    script_dir = r'E:\CLAUDE_Workspace\Claude\Report_Files\Codebase\Hydro_Suite\Hydro_Suite_Data'
    
    print(f"Loading from: {script_dir}")
    
    # Method 1: Add to sys.path and refresh
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    
    # Method 2: Use importlib to load modules directly
    def load_module_from_file(module_name, file_path):
        """Load a module directly from file path"""
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None:
            raise ImportError(f"Could not load spec for {module_name}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    
    try:
        # Load modules in dependency order
        print("Loading shared_widgets...")
        shared_widgets = load_module_from_file(
            'shared_widgets', 
            os.path.join(script_dir, 'shared_widgets.py')
        )
        print("✅ shared_widgets loaded")
        
        print("Loading hydro_suite_interface...")
        hydro_suite_interface = load_module_from_file(
            'hydro_suite_interface',
            os.path.join(script_dir, 'hydro_suite_interface.py')
        )
        print("✅ hydro_suite_interface loaded")
        
        print("Loading cn_calculator_tool...")
        cn_calculator_tool = load_module_from_file(
            'cn_calculator_tool',
            os.path.join(script_dir, 'cn_calculator_tool.py')
        )
        print("✅ cn_calculator_tool loaded")
        
        print("Loading rational_c_tool...")
        rational_c_tool = load_module_from_file(
            'rational_c_tool',
            os.path.join(script_dir, 'rational_c_tool.py')
        )
        print("✅ rational_c_tool loaded")
        
        print("Loading tc_calculator_tool...")
        tc_calculator_tool = load_module_from_file(
            'tc_calculator_tool',
            os.path.join(script_dir, 'tc_calculator_tool.py')
        )
        print("✅ tc_calculator_tool loaded")
        
        print("Loading channel_designer_tool...")
        channel_designer_tool = load_module_from_file(
            'channel_designer_tool',
            os.path.join(script_dir, 'channel_designer_tool.py')
        )
        print("✅ channel_designer_tool loaded")
        
        print("Loading hydro_suite_main...")
        hydro_suite_main = load_module_from_file(
            'hydro_suite_main',
            os.path.join(script_dir, 'hydro_suite_main.py')
        )
        print("✅ hydro_suite_main loaded")
        
        # Now launch the application
        print("\n🚀 Launching Hydro Suite...")
        
        # Create and show the main window
        global hydro_suite_window
        try:
            if 'hydro_suite_window' in globals() and hydro_suite_window:
                hydro_suite_window.close()
                hydro_suite_window.deleteLater()
        except:
            pass
        
        # Get the main window class
        HydroSuiteMainWindow = hydro_suite_main.HydroSuiteMainWindow
        
        hydro_suite_window = HydroSuiteMainWindow()
        hydro_suite_window.show()
        
        print("✅ Hydro Suite launched successfully!")
        print("\n📋 Usage Instructions:")
        print("1. Select a tool from the left panel")
        print("2. Configure your input layers and fields")
        print("3. Watch the validation panel for ✅ status")
        print("4. Click 'Run' when all inputs are valid")
        
        return hydro_suite_window
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(f"Traceback:\n{traceback.format_exc()}")
        return None

# Launch the application
load_hydro_suite()