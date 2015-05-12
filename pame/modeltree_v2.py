""" Tree to store files by catgeory (model, bulk etc...).  Dictionary maps entries
in tree to list of files stored in "my_list" in File_Finder.  Also stores models and
other default objects.
"""
import os
import os.path as op
from traits.api import *

from traitsui.api \
     import Item, View, TreeEditor, TreeNode, OKCancelButtons, VSplit

from interfaces import IAdapter
from File_Finder import LiveSearch

from simple_materials_adapter import BasicAdapter, SellmeirAdapter, ConstantAdapter, \
    DrudeBulkAdapter, SopraFileAdapter, DispwaterAdapter, XNKFileAdapter, CauchyAdapter, \
    AirAdapter

# Adapters
from yamlmaterials import YamlAdapter
import composite_materials_adapter as cma
import nano_materials_adapter as nma

from pame import sopra_dir, riinfo_dir, XNK_dir
import config
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
                  style='readonly',
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
        
        TreeNode( node_for  = [ MaterialList ],
                  auto_open = False,
                  children  = 'CompMaterials',
                  label     = '=Composite Materials',
                  name      = 'Mixed materials: binary liquids, spheres in shells...',
                  view      = no_view,
                  add       = [ Category ]
                  ),        
        
        TreeNode( node_for  = [ MaterialList ], #<--- Not really, node of other nodes/categories
                  auto_open = False,
                  children  = 'NanoMaterials',
                  label     = '=NanoMaterials',
                  name      = 'Nanosphere + shell',
                  view      = no_view,
                  add       = [ Category ]
                  ),             

        # Couldn't get this to be a folder node proper because needs to be
        # a folder of folders, and couldn't figure out how to add BulkMateirals
        # to MaterialList, because material list is list of categories.  Would
        # need to add a category of categories EG:
            # BulkMaterial
            #  [ModelCategories, FileCategeories, DBCategories]
            #
            
        # But material list expects list of materials not list of list of materials
        # I did try a lot of messing around but nothing worked.
        TreeNode( node_for  = [ MaterialList ],
                  auto_open = False,
#                  children  = 'BulkMaterials',
                  label     = '=< BulkMaterials >',
                  name      = 'Material models or refractive index files',
                  view      = no_view,
                  add       = [ IAdapter ]
                  ),       
      
        
#        Second level (models, files, database)
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
        selection_mode='single', #Select one material at a time
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
    riinfodb = List(IAdapter)
    nkfiles = List(IAdapter)
    sopradb = List(IAdapter)
    xnkdb = List(IAdapter)

    def __init__(self, *args, **kwds):
        super(HasTraits, self).__init__(*args, **kwds)
        self.update_tree() #Necessary to make defaults work
        
    def _current_selection_changed(self):
        # Parse yaml file metadata only when selected to save time
        try:
            self.current_selection.read_file_metadata() 
        except Exception:
            pass

    # Default Database Files
    def _sopradb_default(self):
        """ Read all files from sopra database"""
        out = []
        if config.USESOPRA:
            for f in os.listdir(sopra_dir):
                out.append(SopraFileAdapter(file_path = op.join(sopra_dir, f)))
        return out

    def _riinfodb_default(self):
        """ Read all files form RI_INFO database. """
        out = []
        if config.USERIINFO:           
            for d, folders, files in os.walk(riinfo_dir):
                if files:
                    for f in files:
                        obj = YamlAdapter(file_path = op.join(d, f),
                                          source = 'RIInfo', #<--- CHANGE ADAPTER SOURCE!!!
                                          root=riinfo_dir) #THIS WILL SORT
                        out.append(obj)
        return out 
    

    def _xnkdb_default(self):
        """ Read all files from sopra database"""
        out = []
        if config.USESOPRA:
            for f in os.listdir(XNK_dir):
                out.append(XNKFileAdapter(file_path = op.join(XNK_dir, f)))
        return out
        
    def _adaptersort(self, thelist):
        """ Sort a list of IAdapter object by name if self.SORT """
        if self.SORT:
            thelist.sort(key=lambda x: x.name, reverse=self.REVERSE)
        return thelist
            

    # Non-Metals Models ------
    def _nonmetals_default(self): 
        return [
            AirAdapter(),            
            BasicAdapter(),            
            ConstantAdapter(),            
            DispwaterAdapter(),
            CauchyAdapter(),
            SellmeirAdapter()            ]

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
        
        self.materials_trees = MaterialList(

            #Composite and Nano materials
            #------------
            NanoMaterials = [
                nma.NanoSphereAdapter(),
                nma.NanoSphereShellAdapter()
                ],
            
            CompMaterials = [
                        cma.CompositeAdapter(),
                        cma.CompositeMaterial_EquivAdapter(),
                        cma.SphericalInclusions_ShellAdapter(),
                        cma.SphericalInclusions_DiskAdapter()
                        ],

            #Bulk Materials
            #--------
            ModelCategories = \
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
    
            DBCategories = \
               [
                Category(
                    name      = 'XNK Database',
                    Materials = self._adaptersort(self.xnkdb) 
                    ),
                
                Category(
                    name      = 'Sopra Database',
                    Materials = self._adaptersort(self.sopradb) 
                    ),
    
                Category(
                    name      = 'RIINFO Database',
                    Materials = self._adaptersort(self.riinfodb),
                    ),
                ],
    
            FileCategories = \
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
    
    
# SHARED TREE
SHARED_TREE = Model()




# Run the demo (if invoked from the command line):
if __name__ == '__main__':
    Model().configure_traits()