import os
import sys

this_dir_path = os.path.dirname(os.path.abspath(__file__))
base_path = os.path.dirname(this_dir_path)
if this_dir_path not in sys.path:
    sys.path.insert(0, this_dir_path)
if base_path not in sys.path:
    sys.path.insert(0, base_path)
from AST import *
