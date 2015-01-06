''' Define "layers".  Layers are mainly materials with a thickness, and some other meta attributes like special names and
stuff associated with them.  The stack of layers is not controlled here; see layer editor.'''

from traits.api import *
from traitsui.api import *
from numpy import linspace
from interfaces import ILayer, IMaterial
from traitsui.table_filter \
     import EvalFilterTemplate, MenuFilterTemplate, RuleFilterTemplate, \
     EvalTableFilter
from main_parms import FiberParms, SpecParms
from modeltree_v2 import Model
from material_models import Dispwater


class BasicLayer(HasTraits):
    '''Class used to store layer in an interactive tabular environment'''

    specparms=Instance(SpecParms,())  #Passed through to the material; not necessarily used in layers

    implements(ILayer)     
    name=Str('Single Bulk Material')
    material=Instance(IMaterial)
    d=Float(10.0)  
    designator=Enum('basic', 'composite', 'nanoparticle')  #Used to determine special properties like how to sync

    ### Do i need synching and delegation???   
    mat_name=DelegatesTo('material')  #Useful so user can change through editor

    modeltree=Instance(Model)#,())  #Although defined here, it's not really used until composite, nanoparticle layers
    sync_status=Bool(False)  #Used by editor, but only really valid for composite materials  


    traits_view = View(Item('name', label='Layer Name') 
                       )

    def __init__(self, *args, **kwargs):
        super(BasicLayer, self).__init__(*args, **kwargs)
        self.sync_trait('specparms', self.material, 'specparms')
        self.sync_trait('mat_name', self.material, 'mat_name', mutual=True)
        self.sync_trait('modeltree', self.material, 'modeltree', mutual=True)
        print '\n\nIN BASIC LAYER MODELTREE is\n\n', self.modeltree
        

    def _material_default(self): 
        return Dispwater() 

    def _material_changed(self): 
        self.sync_trait('specparms', self.material, 'specparms', mutual=True)  	  #This is necessary because syncing is only done for the obje
        self.sync_trait('mat_name', self.material, 'mat_name', mutual=True)
        self.sync_trait('modeltree', self.material, 'modeltree', mutual=True)        

    def get_usefultraits(self):
        return {'Layer Thickness':self.d, 'Material':self.mat_name}

class Composite(BasicLayer):
    ''' Layer of spherical inclusions '''
    from composite_materials_v2 import SphericalInclusions_Disk

    name=Str('Composite Bulk Material')
    material=Instance(IMaterial)
    designator=Str('composite')
    sync_status=Bool(False)

    oldsolvent=Instance(IMaterial)  #Used for syncing layers, called by layer_editor

    def _material_default(self): 
        return self.SphericalInclusions_Disk()

    #def __init__(self, *args, **kwargs):
        #super(Composite, self).__init__(*args, **kwargs)
        #self.sync_trait('modeltree', self.material, 'modeltree', mutual=True)  #Syncs basic materials tree

    def sync_solvent(self, solvent):
        '''Used to override materials from layereditor'''
        self.oldsolvent=self.material.Material2
        self.material.Material2=solvent
        self.sync_status=True


    def unsync_solvent(self):
        '''Used to unsync material from layereditor'''
        self.material.Material2=self.oldsolvent
        self.sync_status=False

    def _material_changed(self): 
        self.sync_trait('modeltree', self.material, 'modeltree', mutual=True)
        self.sync_trait('specparms', self.material, 'specparms', mutual=True)  	  #This is necessary because syncing is only done for the obje

class Nanoparticle(Composite):
    ''' Layer of nanoparticle inclusions'''
    from advanced_objects_v2 import NanoSphereShell
    name=Str('Nanosphere with Shell')
    material=Instance(IMaterial)	
    designator=Str('nanoparticle')
    sync_rad_selection=Enum('rcore', 'rcore+rshell')

    def _material_default(self): return self.NanoSphereShell()

    def sync_solvent(self, solvent):
        '''Used to override materials from layereditor'''
        self.oldsolvent=self.material.MediumMaterial
        self.material.MediumMaterial=solvent
        self.sync_status=True

    def unsync_solvent(self):
        '''Used to unsync material from layereditor'''
        self.material.MediumMaterial=self.oldsolvent
        self.sync_status=False



class Boundary(BasicLayer):
    """Represent the interface of the stack on either the left or right"""
    designator=Str('basic')
    d=Str('N/A')	

class Substrate(Boundary):             #THESE ARE NOT IMPLEMENTED IN SUPERMODEL YET
    name=Str('Substrate')
    from material_models import Sellmeir

    def _material_default(self): 
        return self.Sellmeir()

class Solvent(Boundary):
    name=Str('Solvent')

    def _material_default(self): 
        return Dispwater()




if __name__ == '__main__':
    number=100
    x=linspace(300, 800, num=number)	

    f=dynamic_shell()
    f.layer_initial.material=CompositeNanosphere() ; f.layer_final.material=CompositeNanosphere()
    f.layer_initial.material.lambdas=x ; f.layer_final.material.lambdas=x

    f.configure_traits()










