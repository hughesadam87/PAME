from traits.api import HasTraits, Instance, DelegatesTo, Str, Enum, Property, \
		       Array, Dict, Int, cached_property, on_trait_change, implements,\
		       List, Str, Range, DelegatesTo, Button
from traitsui.api import Item, View, HGroup, VGroup, Group, Include
from chaco.api import ArrayPlotData, ToolbarPlot, LabelAxis, LinePlot
from chaco.tools.api import BetterSelectingZoom, PanTool
from enable.api import ComponentEditor
from ct_interfaces import IPlot, IRunStorage

###
from numpy import array

class Test(HasTraits)
