from traits.api import Any, Enum, Dict, List, DelegatesTo, HasTraits, \
     Bool, Instance
from traitsui.api import Item, View, HGroup, VGroup
from interfaces import IView, ICompositeView
import utils as pamutils

class PlotSelector(HasTraits):
   """ Scans selected layer material for instances of IView and enumerates
   them with dropdown selection.  Allows users to choose which views of a 
   selected material they want to observe.
   """
   b_app = Any
   stack = DelegatesTo('b_app')
   stack_shortname = List #<-- can't be property because of Delgation
   selected_layer = Enum(values='stack') #<-- make shortname
   sync = Bool(True)
   
   plot_dict = Dict # Property(Dict, depends_on='selected_layer')
   _plot_list = List 
   plot_list = Enum(values='_plot_list') 
   selected_plot = Instance(IView)
   
   # Necessary to have some default or view wont' render correctly
   def _selected_plot_default(self):
      return self.selected_layer.material.mview
   
   def _selected_layer_changed(self):
      self.plot_dict = pamutils.flatten_traitobject(
                        self.selected_layer.material,
                        IView) #<--- Types plots shown
      
      self._plot_list = sorted(self.plot_dict.keys())
#      print len(self._plot_list), len(set(self._plot_list)), 'OWOWWO'
      self.stack_shortname = [s.__repr__()[0:10] for s in self.stack]
   
   def _plot_list_changed(self):
      self.selected_plot = self.plot_dict[self.plot_list]
      
   traits_view = View(
                      HGroup(
                         Item('selected_layer', show_label=False, style='simple'),
                         Item('plot_list', show_label=False, style='simple'),
                         Item('sync')                         
                         ),
                     Item('selected_plot', show_label=False, style='custom'),
                     )

