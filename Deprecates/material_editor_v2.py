from traits.api import *
from traitsui.api import *
import numpy as np  #Can remove if not calling with test data
from File_Finder import LiveSearch
from interfaces import IStorage
from main_parms import SpecParms

material_editor =\
   TableEditor(
       columns=[
           ExpressionColumn(expression='object.mat_name', label='Material Name'),         #CAN SET AN INDIVIDUAL COLUMN TO EDITABLE, BUT OBJECTCOLUMN VS EXPRESSION COLUMN IS ALSO WAY TO GO
	   ExpressionColumn(label='Source', expression='object.source'),
        ],
    deletable   = False, 
    sort_model  = True,

    auto_size = True,
    orientation='vertical',    #Orientation between built-in split between table and edit view

    show_toolbar=True,
    selected           = 'selected_material',   #String name is arbitrary and passed as a global variable to other instances
    selection_color    = 0x000000,
    selection_bg_color = 0xFBD391,

   )

class StorageDictionary(HasTraits):
	from interfaces import IMaterial
	majordic=Dict
	matname=Str('Unknown')
	source=Enum('Model', 'File')
	materialtype=Enum('Bulk', 'Particle')

class MaterialStorage(HasTraits):
   # from material_traits_v4 import SopraFile

    specparms=Instance(SpecParms,())

    edit=Button ; select=Button  ; launch_finder=Button    
    FileSearch = Instance(LiveSearch,())	
    FileTypes = FileSearch.ValidTypes   #THIS IS JUST LIST MOVE ELSEWHERE
    file_list=List

    materials = List
    selected_material = Any      #THIS IS AUTOMATICALLY INHERITED FROM TRAITS CLASS AND CHANGES WITH USER SELECTION
    current_selection=Any    #THIS IS THE STORED VALUE WHEN USER CHOOSES STORE
    lambdas = Array()
    Return=Bool       #Return is a trait which, when updated, will intiate updates in the main program.  Otherwise, errors occur; bad practice.

    implements(IStorage)

    single_view = View(
            Item( 'materials', help='List of possible materials to assign to a layer',
                  show_label  = False,
                  editor      = material_editor  ),
		HSplit( UItem('edit', label='Preview'), UItem('select') ,
			Item('launch_finder', label='Import Files')),
        title     = 'Material Selection',
        width     = .5,
        height    = .4,
        resizable = True,
        buttons   = [ 'OK', 'Cancel', 'Undo', 'Help' ],

    )

    def __init__(self, *args, **kwargs):
	super(HasTraits, self).__init__(*args, **kwargs)
#	self.populate_all_models()
	self.on_trait_change(self.update_file_list, name='FileSearch.my_files')  #ONLY WORKS THIS WAY BECAUSE IT'S MODAL

    def _launch_finder_fired(self):
	self.FileSearch.configure_traits(kind='modal')

    def update_file_list(self):
	newfiles=self.FileSearch.my_files  #Updates in a modal way
	self.filelist_translator(newfiles)

    def filelist_translator(self, newfiles):
	'''Takes in files, runs checks and associates them with the objects they have in the file list'''
	for afile in newfiles:
		full_path=afile.full_name
		base_name=afile.base_name
		extension=afile.file_ext
		file_id=afile.fileclass  #Specifies which filetype trait object this file should fit (Sopra)

		###Note: the file_id is also in the SopraFile object, so if could inspect them, this would be a way to determine how to get this to work###
	
		test=SopraFile(thefile=full_path, mat_name=base_name, specparms=self.specparms)
		self.materials.append(test) 
		
 #   def populate_all_models(self):
#	self.materials.append(Constant() )
#	self.materials.append(Sellmeir )
#	self.materials.append(Dispwater )
#	self.materials.append(DrudeNew() )
#	self.materials.append(CompositeMaterial )	


    def _edit_fired(self):
	self.selected_material.configure_traits()

if __name__ == '__main__':
	number=100
	x=np.linspace(200, 700, num=number)
	er=np.linspace(1,3,num=number)
	ei=np.linspace(2,5,num=number)
	etest=np.empty( len(x), dtype=complex) 
	for i in range(x.shape[0]):
		etest[i]=complex(er[i],ei[i])

#       f=Test(lambdas=x, x_unit='Nanometers')
 #       f.configure_traits()
     #   StorageDictionary().configure_traits()
	MaterialStorage().configure_traits()
#	DoubleStorage(lambdas=x, x_unit='Nanometers').configure_traits()

