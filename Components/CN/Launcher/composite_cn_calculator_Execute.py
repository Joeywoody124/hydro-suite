# Clear any previous imports
import sys
if 'composite_cn_calculator' in sys.modules:
    del sys.modules['composite_cn_calculator']

# Add path and import
sys.path.insert(0, r'E:/CLAUDE_Workspace/Claude/Report_Files/Codebase/Finished_Code/CN')

try:
    from composite_cn_calculator import main
    main()
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()