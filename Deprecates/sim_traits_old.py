from traits.api import *
from traitsui.api import *
import math
import numpy as np
import layer_solver as ls
from sim_plotter import SimView
from main_parms import SpecParms, FiberParms
from interfaces import ISim

class BasicReflectance(HasTraits):
	'''Class used to store data in an interactive tabular environment'''

	specparms=Instance(SpecParms)
	fiberparms=Instance(FiberParms)

	lambdas=DelegatesTo('specparms')	
	Mode=DelegatesTo('fiberparms')
	angles=DelegatesTo('fiberparms')
	stack=List()

	R=Array()   #THIS IS REFLECTION RESPONSE NOT REFLECTANCE!
	Reflectance=Property(Array, depends_on='R')
	Transmittance=Property(Array, depends_on='Reflectance')

	simview=SimView()
	ui=Any

	Launch=Button ; Results=Button

	ns=Property(Array, depends_on='stack')    #This is a list of arrays [n1, n2, n3] one for each layer
	ds=Property(Array, depends_on='stack')    #This is a list of distances [d1, d2] for each non-endface layer
	sim_designator=Str('New Simulation')

	implements(ISim)

	traits_view=View(
			Item('Mode'), Item('sim_designator'),
			Item('ds', style='simple'), 
		#	Item('ns', style='simple'),
			UItem('Launch', label='Launch Simulation'),   #NEED ENABLED WHEN STUFF
			UItem('Results', label='Display Reflection/Transmission', enabled_when='simview is not None'),
			resizable=True
			)

	def __init__(self, *args, **kwargs):
	        super(HasTraits, self).__init__(*args, **kwargs)
	        self.on_trait_change(self.update_simview, 'Mode') 

	def update_simview(self): 
	#	if self.ui is not None:
		self.compute_R()         
		self.simview.update(self.lambdas, self.angles, self.Reflectance, self.Transmittance)
	

	def _Results_fired(self): 
		if self.ui is not None:         #Kills window if it's already open and update is fired
			self.ui.dispose() 
		self.simview.update(self.lambdas, self.angles, self.Reflectance, self.Transmittance)
		self.ui=self.simview.edit_traits()

	def _Mode_default(self): return 'TM'

	def _get_ns(self): 
		rows=len(self.stack) ; cols=self.lambdas.shape[0]
		ns=np.empty( (rows, cols), dtype=complex )
		for i in range(rows):	
			layer=self.stack[i]
			ns[i,:]=layer.material.narray	#LIST OF ARRAYS NOT AN ARRAY 		
		return ns	

	def _get_ds(self): 
		ds=[]
		for layer in self.stack:
			if layer.d != 'N/A':
				ds.append(layer.d)
		return np.array(ds)		

	def _Launch_fired(self): self.compute_R()

	def compute_R(self):
		'''Actually computes R'''
		rows= len(self.angles) ; cols=self.lambdas.shape[0]   
		R=np.empty( (rows,cols), dtype=float)
		for i in range(len(self.angles)):
			R[i,:]=ls.boundary_crushin(self.angles[i], self.ds, self.ns, self.Mode, self.lambdas)
		self.R=R   #Only change trait once so listeners don't get messd up later

	def _get_Reflectance(self): return (self.R)**2
	def _get_Transmittance(self): return (1.0 - self.Reflectance)





if __name__ == '__main__':
	BasicReflectance().configure_traits()
