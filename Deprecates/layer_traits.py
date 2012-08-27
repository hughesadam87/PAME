from traits.api import *
from traitsui.api import *
from numpy import linspace
from interfaces import ILayer, IMaterial
from traitsui.table_filter \
    import EvalFilterTemplate, MenuFilterTemplate, RuleFilterTemplate, \
           EvalTableFilter
from main_parms import FiberParms, SpecParms

	
class BasicLayer(HasTraits):
	'''Class used to store layer in an interactive tabular environment'''
	from material_models import Dispwater

	specparms=Instance(SpecParms,())  #Passed through to the material; not necessarily used in layers

	implements(ILayer)     
	name=Str('Unnamed')
	material=Instance(IMaterial)
	d=Float(10.0)  
	designator=Str('basic')  #This can make the layer special...like substrate, solvent which aren't active at the material level

	editmaterial=Button
	materialname=Property(Str(''), depends_on='material')
	source=Property(Str(''), depends_on='material')
	ematerial=Property(CArray(), depends_on='material')  

        traits_view = View(Item('name'), Item('material', editor=InstanceEditor(), style='custom'), Item('materialname'), Item('d'), Item('editmaterial', enabled_when='material is not None', label='Edit Current Material' ) )

	def __init__(self, *args, **kwargs):
	        super(HasTraits, self).__init__(*args, **kwargs)
		self.sync_trait('specparms', self.material, 'specparms')

	def _get_materialname(self): return self.material.mat_name            #SHOULD PHASE OUT LATER
	def _get_source(self): return self.material.source
	def _get_ematerial(self): return self.material.earray
	def _editmaterial_fired(self): self.material.configure_traits()
	def _material_default(self): return self.Dispwater() #Spec parms?


class Boundary(BasicLayer):
	"""Represent the interface of the stack on either the left or right"""
	designator=Str('Fixed')
	d=Str('N/A')	

class Substrate(Boundary):             #THESE ARE NOT IMPLEMENTED IN SUPERMODEL YET
	name=Str('Substrate')
	from material_models import Sellmeir

	def _material_default(self): return self.Sellmeir()

class Solvent(Boundary):
	name=Str('Solvent')

	def _material_default(self): return self.Dispwater(specparms=self.specparms)

class Solvent_fixed_water(Boundary):
	name=Str('Solvent-no dispersion')
	from material_models import Constant
	def _material_default(self): return Constant()


class BulkMetal(BasicLayer):
	'''Just got lazy, could instantiate basiclayer.material but w/e'''
	from material_models import DrudeBulk
	name=Str('Metallic Layer') 
	def _material_default(self): 
		#return DrudeNP_corrected(specparms=self.specparms)
		return self.DrudeBulk()

class SyncdLayer(BasicLayer):
	'''Layer which shares all traits to the stack solvent'''
	name=Str('Synced basic layer')
	solvent=Instance(Solvent,())
	solventmaterial=Instance(IMaterial)

	def _solventmaterial_default(self): return self.solvent.material

class ParticleInclusions(SyncdLayer):
	name=Str('Shell NPs in solvent')
	from advanced_objects_v2 import NanoSphereShell
	def __init__(self, *args, **kwds):
      	    super(ParticleInclusions, self).__init__(*args, **kwds)
            self.sync_trait('solventmaterial', self.material, 'MediumMaterial')

	def _material_default(self): return self.NanoSphereShell()


if __name__ == '__main__':
	number=100
	x=linspace(300, 800, num=number)	

	f=dynamic_shell()
	f.layer_initial.material=CompositeNanosphere() ; f.layer_final.material=CompositeNanosphere()
	f.layer_initial.material.lambdas=x ; f.layer_final.material.lambdas=x

	f.configure_traits()













