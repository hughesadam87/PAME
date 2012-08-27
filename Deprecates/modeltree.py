#  Copyright (c) 2007, Enthought, Inc.
#  License: BSD Style.

"""
Demonstrates using the TreeEditor to display a hierarchically organized data
structure.

In this case, the tree has the following hierarchy:
  - Main
    - Materials
      - MaterialCategory
        - Material
"""

# Imports:
from traits.api \
    import HasTraits, Str, Regex, List, Instance, Any, Button, DelegatesTo

from traitsui.api \
    import Item, View, TreeEditor, TreeNode, OKCancelButtons

from interfaces import IAdapter
from File_Finder import LiveSearch
from adapter import *


class Material ( HasTraits ):
    """ Defines a Materials Material. """

    adapter=Instance(IAdapter)
    name=DelegatesTo('adapter')
    source=DelegatesTo('adapter')
    notes=DelegatesTo('adapter')
    matobject=DelegatesTo('adapter')
    preview=DelegatesTo('adapter')


class MaterialCategory ( HasTraits ):
    """ Defines a MaterialCategory with Materials. """

    name      = Str( '<unknown>' )
    Materials = List( Material )

class MaterialList ( HasTraits ):
    """ Defines a Materials with MaterialCategories and Materials. """

    name        = Str( '<unknown>' )
    MaterialCategories = List( MaterialCategory )
    Materials   = List( Material )

# Create an empty view for objects that have no data to display:
no_view = View()

# Define the TreeEditor used to display the hierarchy:
tree_editor = TreeEditor(
    nodes = [
        TreeNode( node_for  = [ MaterialList ],
                  auto_open = True,
                  children  = 'MaterialCategories',   #Trait
                  label     = '=Material Models',
                  view      = no_view,
                  add       = [ MaterialCategory ],
        ),
        TreeNode( node_for  = [ MaterialList ],
                  auto_open = True,
                  children  = 'Materials',
                  label     = '=All Materials',
                  view      = no_view,
                  add       = [ Material ]
        ),
        TreeNode( node_for  = [ MaterialCategory ],
                  auto_open = True,
                  children  = 'Materials',
                  label     = 'name',
                  view      = View( [ 'name' ] ),
                  add       = [ Material ]
        ),
        TreeNode( node_for  = [ Material ],
                  auto_open = True,
                  label     = 'name',
                  view      = View( [ 'adapter.name', 'source', 'notes', 'preview', 'matobject' ] )     #CHANGE HERE WHEN PUT IN MATERIALS
        )
    ],
	selection_mode='extended',
	selected='current_selection',
)

class Main ( HasTraits ):
    """ Defines a business Main."""

    allmaterials = Instance( MaterialList )  #An instance of the tree
    FileSearch = Instance(LiveSearch,())	

    current_selection = Any()  #Used for navigating the table

    basic  = Material( adapter=BasicAdapter() )

    def _allmaterials_default(self): 
	return MaterialList(
	        Materials   = [self.basic],   #Defines the two objects that are understood by the tree editor, Materials and departmetns
	        MaterialCategories = [
	            MaterialCategory(
	                name      = 'Basic',
	                Materials = [ self.basic ]
	                   ),
           	    MaterialCategory(
                	name      = 'Metals',
               		Materials = [ ]
           			    )
        			    ]
    			   )

    view = View(
        Item( name       = 'allmaterials',
              editor     = tree_editor,
              show_label = False,

        ),
	Item('current_selection', show_label=False, style='custom'),
        title     = 'Materials Structure',
        buttons   =  OKCancelButtons,
        resizable = True,
        style     = 'custom',
        width     = .3,
        height    = .3
    )




# Run the demo (if invoked from the command line):
if __name__ == '__main__':
	Main().configure_traits()
