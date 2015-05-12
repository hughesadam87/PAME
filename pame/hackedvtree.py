from __future__ import absolute_import
from traitsui.value_tree import TraitsNode, IntNode

from traits.api import HasTraits, Any, Enum, List, Bool, Function, Str, \
     Property
from traitsui.api import View, Item, ValueEditor, OKCancelButtons, \
     CheckListEditor, HGroup
import numpy as np
import functools

# Disallowed types 
from chaco.api import ToolbarPlot
from pame.interfaces import IView

# Original value of monkeypatched method
ORIGINALTRAITNODE = TraitsNode.tno_get_children

def newformat(self, value):
     return repr('MESSED UP%s' % value)

IntNode.format_value = newformat


def _RESTORE():
     """ Restore method to default behavior; othrerwise, all ValueEditors
     will remain this way.
     """
     TraitsNode.tno_get_children = ORIGINALTRAITNODE
     
def arraynode( parentnode, node, hide_privates=True,  
                allowed=[np.ndarray, HasTraits] ):
     """ Gets the object's children.  
      self=TraitsNode object
      node=ObjectTreeNode
     """
     
     names = parentnode._get_names()
     names.sort()
     value    = parentnode.value
     node_for = parentnode.node_for
     nodes    = []
     for name in names:
          try:
               item_value = getattr( value, name, '<unknown>' )
          except Exception, excp:
               item_value = '<%s>' % excp

          if hide_privates:
              if name.startswith('_'):
                  continue #<-- skip 

          if type(item_value) in allowed or isinstance(item_value, HasTraits):

              # Disallowed trait types like Plot
              if isinstance(item_value, ToolbarPlot) or isinstance(item_value, IView):
                   continue
 
              nodes.append( node_for( '.' + name, item_value ) )

     return nodes   

def numericnode( parentnode, node, hide_privates=True,  
                allowed=[int, float] ):
     """ Gets the object's children.  
      self=TraitsNode object
      node=ObjectTreeNode
     """
     
     names = parentnode._get_names()
     names.sort()
     value    = parentnode.value
     node_for = parentnode.node_for
     nodes    = []
     from traitsui.value_tree import IntNode
     for name in names: #<- name is trait name, value is actual valu in program
          try:
               item_value = getattr( value, name, '<unknown>' )
          except Exception, excp:
               item_value = '<%s>' % excp

          if hide_privates:
              if name.startswith('_'):
                  continue #<-- skip 

          if type(item_value) in allowed or isinstance(item_value, HasTraits):
               print name, item_value, node_for, value
               newnode = node_for( '.' + name, item_value ) 
               nodes.append( newnode )
               label = newnode.label
               # What is the method that actually sets the value?

             #  if isinstance(newnode, IntNode):
             #       newnode.label='Int(%s)' % value
             #  print newnode
               
               
     return nodes   

class TraitBrowser(HasTraits):
     """ View value heirarchy in traits.  Selection not working at the 
     moment, so use is limitd.  Uses monkeypatching through hackedvtree.py
     to change output style.
     """

     traits_tree = Any #<-- Instance of stack 
     use_default = Bool(False)
     monkeyfunction = Function

     # For display/view only
     _allowed = Str #<-- defined in subclasses
     _infostr = Property(Str, depends_on='use_default')
     
     def _get__infostr(self):
          """ View message. """
          if not self.use_default:
               return 'Showing %s Traits only' % self._allowed
          return 'Showing Everything'
     
     traits_view = View(
          HGroup(
               Item('use_default', label='Show All Traits'),
               Item('_infostr', style='readonly', show_label=False)
               ),
          Item('traits_tree', 
               editor=ValueEditor(), 
               show_label=False),
          title     = 'Trait Browser',
          buttons   =  OKCancelButtons,
          resizable = True,
          width=.4,
          height=.4                              
     )
     
     def __init__(self, *args, **kwargs):
          super(TraitBrowser, self).__init__(*args, **kwargs)
          TraitsNode.tno_get_children = self.monkeyfunction               
     
          
     #def _hide_changed(self):
          #""" Hide or show various attributes in ValueEditor.  Constructs
          #a partial function based on values of self.hide and monkeypatches
          #TraitNode.  Very hacky.
          #"""
          #if self.use_default:
               #return
          
          #hide = self.hide
          #if 'private' in hide:
               #hide_privates = True
          #else:
               #hide_privates = False
          ## Could make this more "general" with a mapper, but it's 1am
          #allowed = []
          #if 'strings' not in hide:
               #allowed.append(basestring)
          #if 'scalars' not in hide:
               #allowed += [int, float]
          #if 'arrays' not in hide:
               #allowed.append(np.ndarray)

          # X MONKEY PATCH
          # http://stackoverflow.com/questions/28185336/monkey-patching-with-a-partial-function
          #outfcn = functools.partial(hackednode,
                                     #hide_privates = hide_privates,
                                     #allowed = allowed)
          
          #TraitsNode.tno_get_children = outfcn

                   
         ##XXX
         ## SINCE MONKEY PATCHING DOES WORK, JUST GOING TO CALL THIS WITH DEFAULTS
          #TraitsNode.tno_get_children = self.monkeyfunction
          
          ##Force Refresh view
          #self.trait_view().updated = True             
          
     def _use_default_changed(self):
          """ Restore ValueEditor to unchanged values. """
          if self.use_default:
               _RESTORE()
          else:
               TraitsNode.tno_get_children = self.monkeyfunction               
           # Force Refresh view
          self.trait_view().updated = True                


class ArrayBrowser(TraitBrowser):
     """ Display only array and Traits. """
     _allowed = 'Array'

     def _monkeyfunction_default(self):
          return arraynode
     
class NumericBrowser(TraitBrowser):
     """ Display only int, floats and Traits """
     _allowed = 'Numerical (int/float)'    
     
     def _monkeyfunction_default(self):
          return numericnode    

