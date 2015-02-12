#  Adam Hughes 2011
#  Adapted from Enthought traits4.0 examples:
        #  Copyright (c) 2007, Enthought, Inc.
        #  License: BSD Style.#-- Imports --------------------------------------------------------------------

from traits.api import *

from traitsui.api \
     import Item, View, TreeEditor, TreeNode, OKCancelButtons, VSplit

from interfaces import IAdapter
from nano_materials_adapter import *


# COULD COMBINE THIS WITH COMPOSITE PROBABLY, SAME EXACT THING
class Category ( HasTraits ):
    """ Defines a Category with Materials. """

    name      = Str( '<unknown>' )
    Materials = List( IAdapter )

class MaterialList ( HasTraits ):
    """ Defines a Materials with MaterialCategories and Materials. """
    name        = Str( '<unknown>' )
    MaterialCategories = List( Category )
    Materials   = List( IAdapter )

# Create an empty view for objects that have no data to display:
no_view = View()

# Define the TreeEditor used to display the hierarchy:
tree_editor = TreeEditor(
    nodes = [


        TreeNode( node_for  = [ MaterialList ],
                  auto_open = False,
                  children  = 'Materials',
                  label     = '=Composite Materials',
                  view      = no_view,
                  add       = [ IAdapter ]
                  ),
        TreeNode( node_for  = [ Category ],
                  auto_open = True,
                  children  = 'Materials',
                  label     = 'name',
                  view      = View( [ 'name' ] ),
                  add       = [ IAdapter ]
                  ),
        TreeNode( node_for  = [ IAdapter ],
                  auto_open = True,
                  label     = 'name',
                  view      = View( [ 'name', 
                                      'source', 
                                      'notes',
                                      'preview', 
                                      'matobject', 
                                      'apikey' ] )     #TRAITS FROM IADAPTER OBJECT
                  )
        ],
    selection_mode='single',
    selected='current_selection',
)

class NanoMain( HasTraits ):
    """This handles the tree and other stuff"""

    materials_trees = Instance( MaterialList )  #An instance of the tree
    current_selection = Any()  #Used for navigating the table

    general=List(IAdapter) 

    def __init__(self, *args, **kwds):
        super(NanoMain, self).__init__(*args, **kwds)
        self.update_tree() #Necessary to make defaults work

    def _general_default(self): 
        return [
            NanoSphereAdapter(),
            NanoSphereShellAdapter(),
        ]

    def update_tree(self): 
        self.materials_trees=MaterialList(
            Materials   = self.general,

            MaterialCategories = 
            [
                Category(
                    name      = 'NanoSpheres',
                    Materials = self.general 
                    ),
                ],

        )

    view = View(
        Item( name       = 'materials_trees',
              editor     = tree_editor,
              show_label = False,
              ),
        title     = 'Nano Materials Parser',
        buttons   =  OKCancelButtons,
        resizable = True,
        style     = 'custom',
        width=.8,
        height=.8,
    )




# Run the demo (if invoked from the command line):
if __name__ == '__main__':
    NanoMain().configure_traits()