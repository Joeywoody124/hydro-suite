"""
Simple syntax validation for tc_nrcs_standalone.py
"""

import ast
import sys

def validate_python_syntax(file_path):
    """Validate Python syntax without importing QGIS modules"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        # Parse the AST to check syntax
        ast.parse(source_code)
        print(f"✅ Syntax validation passed for {file_path}")
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax error in {file_path}:")
        print(f"   Line {e.lineno}: {e.text}")
        print(f"   Error: {e.msg}")
        return False
        
    except Exception as e:
        print(f"❌ Validation error: {str(e)}")
        return False

if __name__ == "__main__":
    # Validate the main script
    result = validate_python_syntax("tc_nrcs_standalone.py")
    
    if result:
        print("\n✅ Script is ready for use in QGIS!")
        print("📋 Next steps:")
        print("1. Open QGIS 3.40+")
        print("2. Open Python Console (Plugins > Python Console)")
        print("3. Copy and paste the entire tc_nrcs_standalone.py script")
        print("4. Press Enter to run")
    else:
        print("\n❌ Please fix syntax errors before using")
        
    sys.exit(0 if result else 1)