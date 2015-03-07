from traits.api import Any, Enum, Dict, List, DelegatesTo, HasTraits, \
     Bool, Instance, on_trait_change, Property, Button
from traitsui.api import Item, View, HGroup, VGroup
from interfaces import IView, ICompositeView
import utils as pamutils
from layer_editor import SHARED_LAYEREDITOR


# Probably could be done with less code.  Simply want to keep a mapping
# to stack, and mask values and curren plots.  Probably need an intelligently
# placed dictionary, or migrate the "stackmask" eg layer name shortcuts
# onto layereditor itself...
class PlotSelector(HasTraits):
   """ Scans selected layer material for instances of IView and enumerates
   them with dropdown selection.  Allows users to choose which views of a 
   selected material they want to observe.
   """
   layereditor = Instance(HasTraits, SHARED_LAYEREDITOR) #DelegatesTo('b_app')
   selected_index = DelegatesTo('layereditor')
   stack = DelegatesTo('layereditor')
   stackmask = Property(List, depends_on='stack')
   selected_layer_mask = Enum(values='stackmask') #<-- make shortname
   #sync = Bool(False)
   refresh = Button
   
   plot_dict = Dict # Property(Dict, depends_on='selected_layer')
   _plot_list = List 
   plot_list = Enum(values='_plot_list') 
   selected_plot = Instance(IView)

               
   def __init__(self, *args, **kwargs):
      super(PlotSelector, self).__init__(*args, **kwargs)
      self.redraw_current()
      # Set first plot to selected stack index
      self.selected_layer_mask = self.stackmask[self.selected_index] 

   def _get_stackmask(self):
      return ["Layer %s: %s" % (i, layer.name) for (i, layer) in enumerate(self.stack)]

   @on_trait_change('layereditor.selected_layer')
   def _syncup(self):
      if self.layereditor.selected_layer is not None: # init case
         self.selected_layer_mask = self.stackmask[self.layereditor.selected_index]
              
   def _plot_list_changed(self):
      self.selected_plot = self.plot_dict[self.plot_list]

   
   @on_trait_change('layereditor.selected_layer.material._dummydraw')
   def _update(self):
      """ User changes a material in one of the plots, refreshes all."""
      self.redraw_current()

   def _selected_layer_mask_changed(self):
      self.redraw_current()
   
   def _refresh_fired(self):
      self.redraw_current()
   
   def redraw_current(self):
      """ Update available plots.  Old way, used to dynamically search for
      IView traits, but now materials themselves encapsulate this.  
      """
      self.selected_layer = self.stack[self.stackmask.index(self.selected_layer_mask)]
      self.plot_dict = self.selected_layer.material.allview_requested()
      
      # Special sorting for objects of form [a, a.b, b.c.e]...
      # http://stackoverflow.com/questions/28156414/sorting-strings-in-python-that-have-a-hierarchical-alphabetical-order
      _plot_list = self.plot_dict.keys()
      _plot_list.sort(key=lambda v: (len(v.split('.')), v.split('.')))# 
      self._plot_list = _plot_list
      
      # Force redraw of selected plot when plot list is updated
      self.selected_plot = self.plot_dict[self._plot_list[0]]
   
      
   traits_view = View(
                      HGroup(
#                         Item('sync'),                     
                         Item('refresh', label='REFRESH', show_label=False),
                         Item('selected_layer_mask', show_label=False, style='simple'),
                         Item('plot_list', show_label=False, style='simple'),
                         ),
                     Item('selected_plot', show_label=False, style='custom'),
                     )

