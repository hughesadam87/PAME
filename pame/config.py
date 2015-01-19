""" Configuration file for various user-controlled parameters in pame application."""

import matplotlib.cm as cm
from pame import image_dir
import os.path as op

LINEWIDTH = 2
MARKERSIZE = 3

# Default Colormap of Reflectance plot
LINECMAP = cm.coolwarm #Divergent red/blue/gray middle
LINECOLOR = 'red'

# Delimiter for reading in material files 
MATDELIM = '\t'
   # Might break behavior if change, but at least designed this way for consistency.  
   # Others not tested
   
# Material databases to use by default
USESOPRA = True
USERIINFO = True #slows performance

# Spectral parameters
xstart = 400 
xend = 700
xpoints = 5
xunit = 'Nanometers'

# Simulation
# ----------

# File extension
SIMEXT = '.mdat'

SAVEDEPTH = ['light', 'medium', 'heavy']

# Complex numbers
# ---------------
ABOUTZERO = 0.00000001 # Error values, below which values are 0s

# Image displayed when complex plot not found
IMG_NOCOMPLEX_PATH = op.join(image_dir, 'bereal.jpg')


