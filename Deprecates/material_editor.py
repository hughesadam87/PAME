from traits.api import *
from traitsui.api import *
from material_traits_v4 import *
import numpy as np  #Can remove if not calling with test data
from File_Finder import LiveSearch

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

class IStorage(Interface):
     """ Interface to distinguish material storage facilities """

	#RIGHT NOW THIS HAS NO REAL USE JUST SO THAT USERS CAN SEE WHEN THESE TYPES OF TRAITS ARE REQUIRED

	#Should make current_selection and Return a required trait because supermodel doesn't distinguish these on any other facility

class MaterialStorage(HasTraits):

    edit=Button ; select=Button  ; launch_finder=Button    
    FileSearch = Instance(LiveSearch,())	
    FileTypes = FileSearch.ValidTypes   #THIS IS JUST LIST MOVE ELSEWHERE
    file_list=List

    materials = List
    selected_material = Any      #THIS IS AUTOMATICALLY INHERITED FROM TRAITS CLASS AND CHANGES WITH USER SELECTION
    current_selection=Any    #THIS IS THE STORED VALUE WHEN USER CHOOSES STORE
    lambdas = Array()
    Return=Bool       #Return is a trait which, when updated, will intiate updates in the main program.  Otherwise, errors occur; bad practice.
    x_unit = Str()

    implements(IStorage)

    single_view = View(
            Item( 'materials', help='List of possible materials to assign to a layer',
                  show_label  = False,
                  editor      = material_editor  ),
		HSplit( UItem('edit'), UItem('select'), Item('x_unit') ,
			Item('launch_finder', label='Import Files')),
        title     = 'Material Selection',
        width     = .5,
        height    = .4,
        resizable = True,
        buttons   = [ 'OK', 'Cancel', 'Undo', 'Help' ],

    )

    def __init__(self, lambdas, x_unit):
	self.lambdas=lambdas ; self.x_unit=x_unit
	self.populate_all_models()
	self.on_trait_change(self.update_file_list, name='FileSearch.my_files')  #ONLY WORKS THIS WAY BECAUSE IT'S MODAL

    def _launch_finder_fired(self):
	self.FileSearch.configure_traits(kind='modal')

    def update_file_list(self):
	newfiles=self.FileSearch.my_files  #Updates in a modal way
	self.filelist_translater(newfiles)

    def filelist_translater(self, newfiles):
	'''Takes in files, runs checks and associates them with the objects they have in the file list'''
	for afile in newfiles:
		full_path=afile.full_name
		base_name=afile.base_name
		extension=afile.file_ext
		file_id=afile.fileclass  #Specifies which filetype trait object this file should fit
		
		###AT THIS POINT, NEED A LIST THAT DELEGATES BETWEEN THE FILE_IDS AND ACTUALLY CALLING THE METHODS, THEN RUN A FILE CHECK, THEN IF NO ISSUE, OR IF OBJECT TYPE IS ALREADY
		#		PRE CONFIGURED, THEN STOP####

    def populate_all_models(self):
	self.materials.append(Constant() )
	self.materials.append(Sellmeir() )
	self.materials.append(Disp_water() )
	self.materials.append(Drude_bulk() )
	self.materials.append(Drude_new() )
	self.materials.append(CompositeMaterial() )	

    def update_current(self):
	self.current_selection=self.selected_material   #SET THE CURRENT VALUE AS THE PERMANENT ONE
	self.current_selection.lambdas=self.lambdas
	self.current_selection.x_unit=self.x_unit
	self.update_Return()
	
    def update_Return(self):
	self.Return=True

    def _edit_fired(self):
	self.update_current()
	self.selected_material.configure_traits()

    def _select_fired(self):
	self.update_current()


class DoubleStorage(HasTraits):
	mixer=Button 

        lambdas = Array()
        x_unit = Str()

	material2=Instance(MaterialStorage)   #Instance
	material2list=List               #Materials list
	current2=Any                            #Actual selected material
	current2name=Str()

	material1=Instance(MaterialStorage)
	material1list=List
	current1=Any
	current1name=Str()     #MAKE MODEL OR ID OR SOMETHING AND PROPERTY OF CURRENT2,CURRENT1

	current_selection=Instance(mt.CompositeMaterial)    #Instance of composite material	
	composite_name=Str   #POPULATE THIS

        implements(IStorage)

	view=View(Item('x_unit'), 
		HSplit(
			Item('material1', label='Set Material 1 (Solute)', editor=InstanceEditor(), style='custom', show_label=False), 
			Item('material2', label='Set Material 2 (solvent)', editor=InstanceEditor(), style='custom', show_label=False),
		      ),
		Item('current1name', label='Solute Name'), Item('current2name', label='Solvent Name'), 
		UItem('mixer', label='Launch Material Mixer', enabled_when='current1 is not None and current2 is not None'),
		resizable=True, width=600, height=600, buttons=[ 'OK', 'Cancel', 'Undo', 'Help' ],
			)
	
	def __init__(self, lambdas, x_unit):	
		self.lambdas=lambdas
		self.x_unit=x_unit
		self.material1=MaterialStorage(lambdas=self.lambdas, x_unit=self.x_unit)
		self.material2=MaterialStorage(lambdas=self.lambdas, x_unit=self.x_unit)

		self.material2list=self.material2.materials
		self.material1list=self.material1.materials
		self.material1.on_trait_change(self.update1, 'current_selection')  #Need to be updated separately
		self.material2.on_trait_change(self.update2, 'current_selection')  #When user chooses to store
		self.current_selection=mt.CompositeMaterial()


	def update1(self):
		self.current1=self.material1.current_selection
		self.current1name=self.material1.current_selection.mat_name
		self.update_mixed()

	def update2(self):
		self.current2=self.material2.current_selection
		self.current2name=self.material2.current_selection.mat_name
		self.update_mixed()
	
	def _mixer_fired(self):
		self.update_mixed()
		self.current_selection.configure_traits()

	def update_mixed(self):
		'''Only updates when both materials are selected'''
		if self.current1 is not None and self.current2 is not None:
			self.current_selection.Material1=self.current1
			self.current_selection.Material2=self.current2 #THESE HAVE EARRAYS PASSED SO MATERIAL1 and MATERIAL2 are fully loaded
			self.current_selection.lambdas=self.lambdas
			self.current_selection.x_unit=self.x_unit



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
  #      MaterialStorage(lambdas=x, x_unit='Nanometers').configure_traits()
	DoubleStorage(lambdas=x, x_unit='Nanometers').configure_traits()

