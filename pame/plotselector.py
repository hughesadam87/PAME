from traits.api import Any, Enum, Dict, List, DelegatesTo, HasTraits, \
     Bool, Instance, on_trait_change
from traitsui.api import Item, View, HGroup, VGroup
from interfaces import IView, ICompositeView
import utils as pamutils
from layer_editor import SHARED_LAYEREDITOR

class PlotSelector(HasTraits):
   """ Scans selected layer material for instances of IView and enumerates
   them with dropdown selection.  Allows users to choose which views of a 
   selected material they want to observe.
   """
   layereditor = Instance(HasTraits, SHARED_LAYEREDITOR) #DelegatesTo('b_app')
   stack = DelegatesTo('layereditor')
   selected_layer = Enum(values='stack') #<-- make shortname
   sync = Bool(True)
   
   plot_dict = Dict # Property(Dict, depends_on='selected_layer')
   _plot_list = List 
   plot_list = Enum(values='_plot_list') 
   selected_plot = Instance(IView)

   @on_trait_change('layereditor.selected_layer')
   def _syncup(self):
      if self.sync:
         if self.layereditor.selected_layer is not None: # init case
            self.selected_layer  = self.layereditor.selected_layer 
          
   # Necessary to have some default or view wont' render correctly
   def _selected_plot_default(self):
      return self.selected_layer.material.mview
   
   def _selected_layer_changed(self):
      self.plot_dict = pamutils.flatten_traitobject(
                        self.selected_layer.material,
                        IView) #<--- Types plots shown
      
      # Special sorting for objects of form [a, a.b, b.c.e]...
      # http://stackoverflow.com/questions/28156414/sorting-strings-in-python-that-have-a-hierarchical-alphabetical-order
      _plot_list = self.plot_dict.keys()
      _plot_list.sort(key=lambda v: (len(v.split('.')), v.split('.')))# 
      self._plot_list = _plot_list
      
      # Force redraw of selected plot when plot list is updated
      self.selected_plot = self.plot_dict[self._plot_list[0]]
   
   def _plot_list_changed(self):
      self.selected_plot = self.plot_dict[self.plot_list]
      
   traits_view = View(
                      HGroup(
                         Item('sync'),                     
                         Item('selected_layer', show_label=False, style='simple'),
                         Item('plot_list', show_label=False, style='simple'),
                         ),
                     Item('selected_plot', show_label=False, style='custom'),
                     )

