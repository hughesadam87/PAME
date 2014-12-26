""" Configuration file for various user-controlled parameters in pame application."""

import matplotlib.cm as cm

# Default Colormap of Reflectance plot
LINECMAP = cm.coolwarm #Divergent red/blue/gray middle

# Delimiter for reading in material files 
MATDELIM = '\t'
   # Might break behavior if change, but at least designed this way for consistency.  Others not tested