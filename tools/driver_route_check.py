"""Compatibility entry point: current navigation checks supersede the legacy ORS-only fixture."""
import os,sys,runpy
from pathlib import Path
if len(sys.argv)>1:os.environ['MAP_LEAFLET']=sys.argv[1]
runpy.run_path(str(Path(__file__).with_name('navigation_ui_check.py')),run_name='__main__')
