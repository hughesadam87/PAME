""" Configuration file for various user-controlled parameters in pame application."""

import matplotlib.cm as cm

# Default Colormap of Reflectance plot
LINECMAP = cm.coolwarm #Divergent red/blue/gray middle

# Delimiter for reading in material files 
MATDELIM = '\t'
   # Might break behavior if change, but at least designed this way for consistency.  
   # Others not tested
   
# Material databases to use by default
USESOPRA = True
USERIINFO = True #slows performance

# Spectral parameters
xstart = 300 
xend = 800
xpoints = 100 
xunit = 'Nanometers'
