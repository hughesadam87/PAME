from __future__ import absolute_import
from traitsui.value_tree import TraitsNode

from traits.api import HasTraits, Any, Enum, List, Bool
from traitsui.api import View, Item, ValueEditor, OKCancelButtons, \
     CheckListEditor
import numpy as np
import functools

# Original value of monkeypatched method
ORIGINALTRAITNODE = TraitsNode.tno_get_children

def _RESTORE():
     """ Restore method to default behavior; othrerwise, all ValueEditors
     will remain this way.
     """
     TraitsNode.tno_get_children = ORIGINALTRAITNODE
     
def hackednode( traitsnodeobj, ndoe, hide_privates=True,  
                allowed=[int, float, np.ndarray] ):
     """ Gets the object's children.  
      self=TraitsNode object
      node=ObjectTreeNode
     """
     
     #if traitsnodeobj is None:
          #return 
     #print 'hi', traitsnodeobj, node, 'fofof\n\n\n'
     names = traitsnodeobj._get_names()
     names.sort()
     value    = traitsnodeobj.value
     node_for = traitsnodeobj.node_for
     nodes    = []
     for name in names:
          try:
               item_value = getattr( value, name, '<unknown>' )
          except Exception, excp:
               item_value = '<%s>' % excp

          if hide_privates:
              if name.startswith('_'):
                  continue #<-- skip 

          print 'checking', type(item_value)
          if type(item_value) in allowed or isinstance(item_value, HasTraits):
              nodes.append( node_for( '.' + name, item_value ) )

     return nodes   

#def set_hack(hack=1):     
     #if hack == 1: 
          #TraitsNode.tno_get_children = hack1
     #elif hack == 2:
          #TraitsNode.tno_get_children = hack2
     #else:
          #_RESTORE()

class TraitBrowser(HasTraits):
     """ View value heirarchy in traits.  Selection not working at the 
     moment, so use is limitd.  Uses monkeypatching through hackedvtree.py
     to change output style.
     """

     traits_tree = Any #<-- Instance of selected traits 
#     hack = Enum([1,2,3])
     use_default = Bool(False)
     #http://stackoverflow.com/questions/23650049/traitsui-checklisteditor-changing-the-case-of-values?rq=1      
     hide = List(editor=CheckListEditor(
                       values = ['arrays', 'scalars', 'strings', 'private'],
                        cols=4),
                    value=['strings', 'private'])
     
     traits_view = View(
 #         Item('hack'),
          Item('use_default'),
          Item('hide', show_label=False, style='custom'),
          Item('traits_tree', 
               editor=ValueEditor(), 
               show_label=False),
          title     = 'Trait Browser',
          buttons   =  OKCancelButtons,
          resizable = True,
          width=.4,
          height=.4                              
     )

     #def _hack_changed(self):
          #print 'setting hack to', self.hack
          ##TraitsNode.tno_get_children = hack1
          #set_hack(self.hack)

          ## Force Refresh view
          #self.trait_view().updated = True      
          
     def _hide_changed(self):
          """ Hide or show various attributes in ValueEditor.  Constructs
          a partial function based on values of self.hide and monkeypatches
          TraitNode.  Very hacky.
          """
          if self.use_default:
               return
          hide = self.hide
          if 'private' in hide:
               hide_privates = True
          else:
               hide_privates = False
          # Could make this more "general" with a mapper, but it's 1am
          allowed = []
          if 'strings' not in hide:
               allowed.append(basestring)
          if 'scalars' not in hide:
               allowed += [int, float]
          if 'arrays' not in hide:
               allowed.append(np.ndarray)

          # X MONKEY PATCH
          #outfcn = functools.partial(hackednode,
                                     #hide_privates = hide_privates,
                                     #allowed = allowed)
          
         #TraitsNode.tno_get_children = outfcn

                   
         #XXX
         # SINCE MONKEY PATCHING DOES WORK, JUST GOING TO CALL THIS WITH DEFAULTS
          TraitsNode.tno_get_children = hackednode
          
          # Force Refresh view
          self.trait_view().updated = True             
          
     def __use_default_changed(self):
          """ Restore ValueEditor to unchanged values. """
          if self._use_default:
               _RESTORE()
               # Force Refresh view
               self.trait_view().updated = True                

     def __init__(self, *args, **kwargs):
          super(TraitBrowser, self).__init__(*args, **kwargs)

     # No Works
     #def _current_selection_changed(self):
          #print 'woot current select'
          
if __name__ == '__main__':
     # Pass test HasTraits object in to test it
     test_object = HasTraits()
     TraitBrowser(trait_tree=test_object).configure_traits()
     
     

