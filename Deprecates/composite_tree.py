#  Adam Hughes 2011
#  Adapted from Enthought traits4.0 examples:
	#  Copyright (c) 2007, Enthought, Inc.
	#  License: BSD Style.#-- Imports --------------------------------------------------------------------

from traits.api import *

from traitsui.api \
    import Item, View, TreeEditor, TreeNode, OKCancelButtons, VSplit

from interfaces import IAdapter
from File_Finder import LiveSearch
from adapter import *

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
                  auto_open = True,
                  children  = 'MaterialCategories',   #Trait
                  label     = '=Models',
                  view      = no_view,
                  add       = [ Category ],
        ),

        TreeNode( node_for  = [ MaterialList ],
                  auto_open = True,
                  children  = 'FileCategories',   #Trait
                  label     = '=Files',
                  view      = no_view,
                  add       = [ Category ],
        ),

        TreeNode( node_for  = [ MaterialList ],
                  auto_open = False,
                  children  = 'Materials',
                  label     = '=All Materials',
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
                  view      = View( [ 'name', 'source', 'notes', 'preview', 'matobject', 'thefile' ] )     #TRAITS FROM IADAPTER OBJECT
        )
    ],
	selection_mode='extended',
	selected='current_selection',
)

class Main ( HasTraits ):
    """This handles the tree and other stuff"""

    materials_trees = Instance( MaterialList )  #An instance of the tree
    current_selection = Any()  #Used for navigating the table
   
    composites=List(IAdapter) 

    def __init__(self, *args, **kwds):
      	    super(HasTraits, self).__init__(*args, **kwds)
            self.update_tree() #Necessary to make defaults work

    def _composites_default(self): 
	return [
		CompositeAdapter(),
		]

    def update_tree(self): 
	self.materials_trees=MaterialList(
	        Materials   = self.composites
	  
	        MaterialCategories = 
			[
	  	          Category(
	  	              name      = 'Composite Materials',
	  	              Materials = self.composites 
	  	                 ),
  			],

    	 )

    view = View(
	VSplit(
        Item( name       = 'materials_trees',
              editor     = tree_editor,
              show_label = False,

        ),
	Item('FileSearch', show_label=False),
	),
        title     = 'Materials Parser',
        buttons   =  OKCancelButtons,
        resizable = True,
        style     = 'custom',
	width=.8,
	height=.8,
    )




# Run the demo (if invoked from the command line):
if __name__ == '__main__':
	Main().configure_traits()
