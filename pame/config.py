""" Configuration file for various user-controlled parameters in pame application."""

import matplotlib.cm as cm

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