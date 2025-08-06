# Quick Launcher for Composite CN Calculator v2.2 - Server Version
# Copy and paste this into QGIS Python Console

import sys; sys.path.insert(0, r'C:\JBC\Bragg Consulting\JBC - Share\Resources\Software\QGIS_Templates\Python_Hydro_Scripts\CN'); exec('if "composite_cn_calculator" in sys.modules: del sys.modules["composite_cn_calculator"]'); from composite_cn_calculator import main; main()
