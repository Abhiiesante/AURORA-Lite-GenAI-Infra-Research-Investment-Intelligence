import importlib
import sys

# Re-export the real aurora package for apps.api.aurora.* imports
real = importlib.import_module('aurora')
globals().update(real.__dict__)
