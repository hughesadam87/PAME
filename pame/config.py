""" Configuration file for various user-controlled parameters in pame application."""

import matplotlib.cm as cm
from pame import image_dir
import os.path as op

# Material names assigned dynamically 
AUTONAME = True

# Scikit-Spectra compatibility
SKSPEC_INSTALLED = True
try:
   import skspec
except ImportError:
   SKSPEC_INSTALLED = False
   
LINEWIDTH = 2
MARKERSIZE = 3

# Default Colormap of Reflectance plot
LINECMAP = cm.coolwarm #Divergent red/blue/gray middle
LINECMAP_LAMBDA = cm.jet
LINECOLOR = 'red'

# Delimiter for reading in material files 
MATDELIM = '\t'
   # Might break behavior if change, but at least designed this way for consistency.  
   # Others not tested
   
# Material databases to use by default
USESOPRA = True
USERIINFO = True#True #slows performance it's so large

# Spectral parameters IN NANOMETERS (MUST BE IN NANOMETERS, CAN CONVERT
# IN PROGRAM)
xstart = 300 
xend = 700
xpoints = 100

# Simulation
# ----------
SIMFOLDER = op.join( op.abspath('.'),'Simulations') #Default save folder for sims (smart to have this way?)
SIMPREFIX = 'Layersim'
SIMPARSERBACKEND = 'pandas' #pandas or skspec
MAXSTEPS = 50
# File extension
SIMEXT = '.mpickle'

SAVEDEPTH = ['light', 'medium', 'heavy']

# Complex numbers
# ---------------
ABOUTZERO = 1e-12 # Error values, below which values are 0s 
# what is min floating poitn precision

# Image displayed when complex plot not found
IMG_NOCOMPLEX_PATH = op.join(image_dir, 'bereal.jpg')


