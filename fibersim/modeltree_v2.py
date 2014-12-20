#  Adam Hughes 2011
#  Adapted from Enthought traits4.0 examples:
	#  Copyright (c) 2007, Enthought, Inc.
	#  License: BSD Style.#-- Imports --------------------------------------------------------------------

from traits.api import *

from traitsui.api \
    import Item, View, TreeEditor, TreeNode, OKCancelButtons, VSplit

from interfaces import IAdapter
from File_Finder import LiveSearch

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

class Main( HasTraits ):
    """This handles the tree and other stuff"""
    from simple_materials_adapter import BasicAdapter, SellmeirAdapter, ConstantAdapter, DrudeBulkAdapter, SopraFileAdapter, NKDelimitedAdapter

    materials_trees = Instance( MaterialList )  #An instance of the tree
    current_selection = Any()  #Used for navigating the table
   
    FileSearch = Instance(LiveSearch,())	
    FileDic=Dict  #Maintains object representations for files

    nonmetals  = List(IAdapter)
    metals  = List(IAdapter)
    soprafiles = List(IAdapter)
    nkfiles = List(IAdapter)

    def __init__(self, *args, **kwds):
      	    super(HasTraits, self).__init__(*args, **kwds)
            self.update_tree() #Necessary to make defaults work

    def _nonmetals_default(self): 
	return [
		self.BasicAdapter(),
		self.SellmeirAdapter(),
		self.ConstantAdapter(),
		]

    def _metals_default(self):
	return [
		self.DrudeBulkAdapter()
	       ]


    @on_trait_change('FileSearch.my_files')
    def update_file_dic(self):
	'''Updates file dic, and since my_files won't update redundantly, the dictionary also won't gather duplicate entries'''
    	for afile in self.FileSearch.my_files:
		full_path=afile.full_name ; base_name=afile.base_name
		extension=afile.file_ext  ; file_id=afile.fileclass  #Specifies which filetype trait object this file should fit (Sopra)

		if file_id=='Other': self.FileDic[afile]=self.NKDelimitedAdapter(thefile=full_path)
		if file_id=='Sopra': self.FileDic[afile]=self.SopraFileAdapter(thefile=full_path)

	###When entries in 'my_files' are removed, this syncs the dictionary###
	for key in self.FileDic.keys():
		if key not in self.FileSearch.my_files:
			del self.FileDic[key]

	self.soprafiles=[ self.FileDic[k] for k in self.FileDic.keys() if k.fileclass =='Sopra']
	self.nkfiles=[ self.FileDic[k] for k in self.FileDic.keys() if k.fileclass =='Other']

	self.update_tree()

    def update_tree(self): 
	self.materials_trees=MaterialList(
	        Materials   = self.nonmetals+self.metals+self.soprafiles+self.nkfiles,   #Taking in lists
	  
	        MaterialCategories = 
			[
	  	          Category(
	  	              name      = 'NonMetals',
	  	              Materials = self.nonmetals 
	  	                 ),
          	 	    Category(
          		      	name      = 'Metals',
          	     		Materials = self.metals
           			    )
  			],

		FileCategories = 
			[
	            Category(
	                name      = 'Sopra Files',
	                Materials = self.soprafiles
	                   ),
	            Category(
	                name      = 'NK Files',
	                Materials = self.nkfiles
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
