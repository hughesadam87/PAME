""" Tree to store files by catgeory (model, bulk etc...).  Dictionary maps entries
in tree to list of files stored in "my_list" in File_Finder.  Also stores models and
other default objects.
"""

from traits.api import *

from traitsui.api \
     import Item, View, TreeEditor, TreeNode, OKCancelButtons, VSplit

from interfaces import IAdapter
from File_Finder import LiveSearch

from simple_materials_adapter import BasicAdapter, SellmeirAdapter, ConstantAdapter, \
    DrudeBulkAdapter, SopraFileAdapter, XNKFileAdapter

from yamlmaterials import YamlAdapter

from pame import data_dir     
#http://code.enthought.com/projects/traits/docs/html/TUIUG/factories_advanced_extra.html

# Instances
class Category ( HasTraits ):
    """ Defines a Category with Materials. """

    name      = Str( '<unknown>' )
    Materials = List( IAdapter )

class MaterialList ( HasTraits ):
    """ Defines a Materials with MaterialCategories and Materials. Basically
    a Node/Folder for tree.  Stores materials.
    """
    name        = Str( '<unknown>' )
    MaterialCategories = List( Category )
    Materials   = List( IAdapter )

# Create an empty view for objects that have no data to display:
no_view = View()

# Show's name in view panel for nodes (ie if use clicks model node)
# Why isn't working for some of them?
nodeview =  View( ['name'], 
                  style='readonly'
                  )

# Define the TreeEditor VIEW used to display the hierarchy:
tree_editor = TreeEditor(
    nodes = [
        
        # TOP NODE
        TreeNode( node_for  = [ MaterialList ],
                  auto_open = True,
                  label     = '=All Materials',
                  view      = no_view,
                  name      = 'Material models, files and databases',
                  ),        
        
        # Second level (models, files, database)
        TreeNode( node_for  = [ MaterialList ],
                  auto_open = False,
                  children  = 'ModelCategories',   #Trait
                  label     = '=Models',
                  name      = 'Material models: Drude etc...', # X NAMES DONT WORK EVEN IN NODEVIEW                  
                  view      = no_view,
                  add       = [ Category ],
                  ),

        TreeNode( node_for  = [ MaterialList ],
                  auto_open = False,
                  children  = 'FileCategories',   #Trait
                  label     = '=Files',
                  name      = 'Material from files',                  
                  view      = no_view,
                  add       = [ Category ],
                  ),

        TreeNode( node_for  = [ MaterialList ],
                  auto_open = False,
                  children  = 'DBCategories',   #Trait
                  label     = '=Databases',
                  view      = no_view,
                  add       = [ Category ],
                  ),

                  
        # --Dont Touch--- define how folders display contents (ie names)
        TreeNode( node_for  = [ Category ],
                  auto_open = True,
                  children  = 'Materials',
                  label     = 'name',
                  view      = nodeview,
                  add       = [ IAdapter ]
                  ),

        TreeNode( node_for  = [ IAdapter ],
                  auto_open = True,
                  label     = 'name',
                 )
            ],
        selection_mode='extended',
        selected='current_selection',
        )

class Model( HasTraits ):
    """Model for updating Tree, performs file searches, reads from databases
    instantiates material models."""

    # Sort files and DB entries 
    SORT = Bool(True)   # XXX NOT ON VIEW YET...
    REVERSE = Bool(False)

    materials_trees = Instance( MaterialList )  #An instance of the tree
    current_selection = Any()  #Used for navigating the table

    # File and database manager objects
    FileSearch = Instance(LiveSearch,())	
    FileDic = Dict  #Maintains object representations for files

    # All material categories ( see update_tree() )
    nonmetals  = List(IAdapter)
    metals  = List(IAdapter)
    soprafiles = List(IAdapter)
    riinfofiles = List(IAdapter)
    nkfiles = List(IAdapter)
    sopradb = List(IAdapter)

    def __init__(self, *args, **kwds):
        super(HasTraits, self).__init__(*args, **kwds)
        self.update_tree() #Necessary to make defaults work
        
    def _adaptersort(self, thelist):
        """ Sort a list of IAdapter object by name if self.SORT """
        if self.SORT:
            thelist.sort(key=lambda x: x.name, reverse=self.REVERSE)
        return thelist
            
    def read_databases(self):
        """ Imports database from json object. """


    # Non-Metals Models ------
    def _nonmetals_default(self): 
        return [
            BasicAdapter(),
            SellmeirAdapter(),
            ConstantAdapter(),
        ]

    # Metal Models Models ------
    def _metals_default(self):
        return [
            DrudeBulkAdapter()
            ]

    # Files managed by dictionary here
    @on_trait_change('FileSearch.my_files')
    def update_file_dic(self):
        '''Updates file dic, and since my_files won't update redundantly, the dictionary also won't gather duplicate entries'''

        for afile in self.FileSearch.my_files:
            # Fit new files to appropriate adapter
            full_path = afile.full_name 
            base_name = afile.base_name
            extension = afile.file_ext  
            file_id = afile.fileclass  #Specifies which filetype trait object this file should fit (Sopra)

            if file_id=='XNK': 
                self.FileDic[afile] = XNKFileAdapter(file_path=full_path)

            elif file_id == 'XNK_csv':
                self.FileDic[afile] = XNKFileAdapter(file_path=full_path, csv=True)                

            elif file_id=='Sopra': 

                # YAML TEST CASE DELETE ME
                testfile = YamlAdapter(file_path = '~/Desktop/fibersim/pame/data/RI_INFO/main/Ag/Johnson.yml')
                testfile.parse_file() #WHEN IS BEST TIEM TO DO THIS?  DON'T WANT TO READ EVERY FILE 
                self.riinfofiles = [testfile]

                self.FileDic[afile] = SopraFileAdapter(file_path=full_path)

            else:
                raise Exception('What kind of file id is %s' % file_id)

        # When entries in 'my_files' are removed, this syncs the dictionary
        for key in self.FileDic.keys():
            if key not in self.FileSearch.my_files:
                del self.FileDic[key]

        self.soprafiles= [self.FileDic[k] for k in self.FileDic.keys() if
                          k.fileclass =='Sopra']

        # nk files can be csv too, so have this workaround
        self.nkfiles= [self.FileDic[k] for k in self.FileDic.keys() if
                       k.fileclass in ['XNK', 'XNK_csv']]

        self.update_tree()

    def update_tree(self): 
        """ Updates the entire tree """
        # ALL MODELS MUST GO HERE!
        
        self.materials_trees = MaterialList(

            ModelCategories = 
            [
                Category(
                    name      = 'Non-Metals',
                    Materials = self._adaptersort(self.nonmetals)
                    ),
                Category(
                    name      = 'Metals',
                    Materials = self._adaptersort(self.metals)
                )
                ],

            DBCategories = 
            [
                Category(
                    name      = 'RIINFO Database',
                    Materials = self._adaptersort(self.riinfofiles) #CHANGE ME
                    ),
                
                Category(
                    name      = 'Sopra Database',
                    Materials = self._adaptersort(self.soprafiles) #CHANGE ME
                    ),
                ],

            FileCategories = 
            [
                Category(
                    name      = 'Sopra Files',
                    Materials = self._adaptersort(self.soprafiles)
                    ),
                Category(
                    name      = 'NK Files',
                    Materials = self._adaptersort(self.nkfiles)
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
    Model().configure_traits()