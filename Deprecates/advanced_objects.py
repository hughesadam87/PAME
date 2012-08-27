from traits.api import *
from traitsui.api import *
from composite_materials import CompositeMaterial  #Needed for inheritance
from material_models import basic_metal_model, DrudeBulk
from interfaces import IMie, IMaterial, IMixer, IStorage
from numpy import empty, array
import math, cmath

class NanoSphere(CompositeMaterial):
	'''Technically a nanosphere always needs a medium anyway, so make it composite object'''
	from mie_traits_delegated import sphere_full, sphere
	from material_models import DrudeBulk
	from material_models import Dispwater

	mat_name=Str('Bare Nanosphere')
	FullMie=Instance(IMie)  #Used to compute scattering properties	

	MediumMaterial=Instance(IMaterial)
	NanoMaterial=Instance(IMaterial)

	r_core=DelegatesTo('FullMie')

        def __init__(self, *args, **kwds):
      	    super(NanoSphere, self).__init__(*args, **kwds)
            self.sync_trait('NanoMaterial', self, 'Material1')
	    self.sync_trait('MediumMaterial', self, 'Material2')
	    self.sync_trait('NanoMaterial', self.FullMie, 'CoreMaterial')
	    self.sync_trait('MediumMaterial', self.FullMie, 'MediumMaterial')


	traits_view=View( Item('NanoMaterial', editor=InstanceEditor()), Item('selectmat1'), 
			Item('MediumMaterial', editor=InstanceEditor()), Item('r_core'),Item('FullMie') )


	def _FullMie_default(self): return self.sphere_full(specparms=self.specparms, 
				    CoreMaterial=self.Material1, MediumMaterial=self.Material2)   #Syntax (mateiral1, material2) is necessary for syncing

	def _NanoMaterial_default(self): return self.DrudeBulk(specparms=self.specparms)#, r=self.r_core)
	def _MediumMaterial_default(self): return self.Dispwater(specparms=self.specparms)
	
	def _r_core_changed(self):
		self.NanoMaterial.r=self.r_core

class DrudeNew(basic_metal_model, NanoSphere):
	'''Drude model with interband contributions(From paper "Advanced Drude Model")'''
	mat_name=Str('Drude Gold Nanoparticle')
	model_id=Str('DrudeNew')
	valid_metals=Enum('gold') 
	lamp=Float(145)
	gamp=Float(17000)
	nm_conv=Float(.000000001)   #why is lamp in these units?
	wplasma=Float()  #1.29 E 16
	v_fermi=Float(1.4 * 10**6)         #Same for gold and silver

	traits_view=View( Item('mat_name', show_label=False), Item('mviewbutton', label='Show Dielectric', show_label=False),
			 Item('r_core', show_label=True, style='simple', label='NP Radius'),
			  Item('FullMie'))


	def _wplasma_default(self): return 2.0*math.pi*self.c/(self.lamp * self.nm_conv)
			
	def update_data(self):           #THIS IS TOTALLY OLD WAY NEED TO UPDATE BUT NOT TRIVIAL
		eeff= empty(self.lambdas.shape, dtype='complex')
		for i in range(len(self.lambdas)):
			entry=self.lambdas[i] 
			f1=1.0/entry**2
			f2= 1.0/(entry*self.gamp)
			f3=complex(f1, f2)
			den=self.lamp**2 * f3
			term1=1.53 - (1.0/den)	
			tempsum=0.0
			for j in range(2):
				if j==0:
					Aj=.94
					lamj=468  #nm
					gamj=2300
					phij=-math.pi/4.0
				elif j==1:
					Aj=1.36
					lamj=331
					gamj=940	
					phij=-math.pi/4.0

				den1=complex( (1.0/lamj - 1.0/entry), (-1.0/gamj) )				
				den2=complex( (1.0/lamj + 1.0/entry), (1.0/gamj)   ) 
				expj1=cmath.exp(complex(0, phij)  )
				expj2=cmath.exp(complex(0, -phij))
				tempsum=tempsum + ((Aj/lamj)*(expj1/den1   + expj2/den2 ))   #SHORT LAMBDA CORRECTION!!!
			final=term1 + tempsum
			fr=final.real
			fi=final.imag
			omega=(2.0*math.pi*self.c)/(self.nm_conv*entry)
			fi=fi+(self.wplasma**2/omega**3)*(self.v_fermi/(self.r_core*self.nm_conv))  
			eeff[i]=complex(fr, fi)	
		self.earray=eeff
		self.NanoMaterial=self

class DrudeNP_corrected(DrudeBulk, NanoSphere):
	'''Corrects plasma frequency for free electron term; from Gupta 2'''

	valid_metals=Enum('gold','silver')  #Need fermi velocity for copper and aluminum
	apply_correction=Bool(True)


	###USES VF IN NM/S SO THAT L CAN BE IN NM AS WELL SO THIS OBJECT IS DEPENDENT ON UNITS###

	def _valid_metals_changed(self): self.update_data()
	def _r_core_changed(self): self.update_data()
	def _apply_correction_changed(self): self.update_data()	


	def update_data(self):   #THIS DOES FIRE AT INSTANTIATION
		if self.valid_metals == 'gold':               #These effects may be size dependent, need to look into it.  
			self.lam_plasma=(1.6826 * 10**-7) #m
			lb=(8.9342 * 10**-6)              #m
			vf=Float(1.4*10**6) #m/s  ONLY VALID FOR GOLD AND SILVER
		elif self.valid_metals == 'silver':
			self.lam_plasma=(1.4541 * 10**-7) #m
			lb=(1.7614 * 10**-5)              #m   #Uncorrected collision wavelength	
			vf=Float(1.4*10**6) #m/s  ONLY VALID FOR GOLD AND SILVER
		den=1.0 + ( (self.vf * lb) / (2.0*math.pi*self.c * self.r_core* 1.0*10**-9 )) 
		if self.apply_correction==True:
	   		self.lam_collis=lb/den
		else:
			self.lam_collis=lb  #Set to bulk value

		m_xarray=self.specparms.specific_array('Meters')
		unity= array([complex(0.0,1.0)], dtype=complex)  #Gupta requries i * lambda, so this gets complex value of the xarray
		self.earray = 1.0 - ( (m_xarray**2 * self.lam_collis) / (self.lam_plasma**2 * ( self.lam_collis + m_xarray*unity)  ) )

		self.NanoMaterial=self

	traits_view=View(Item('r_core'), Item('valid_metals'),
			Item('lam_plasma', style='readonly'), Item('lam_collis', style='readonly'),Item('mviewbutton'), Item('apply_correction', label='Free Path Correction'),
			Item('FullMie')
			)

class NanoSphereShell(NanoSphere):
	'''This is a single object, but it inherits from composite material to allow for trait changes and stuff to be understood'''		
	from mie_traits_delegated import sphere_shell
	from composite_materials import CompositeMaterial_Equiv, SphericalInclusions_Disk, SphericalInclusions_Shell

	###Note: NanoMaterial refers to the core/shell composite object that is the "NanoSphere" for this instance ###

	CoreMaterial=Instance(IMaterial)     #Bare Metal
	ShellMaterial=Instance(IMaterial)    #Composite Shell	
	DiskCounter=Instance(IMaterial)      #Tracks number of np's in material

	CompositeMix=DelegatesTo('NanoMaterial', prefix='Mix')             #Only needed for view
	CompositeMixStyle=DelegatesTo('NanoMaterial', prefix='MixingStyle')  


	r_shell=DelegatesTo('FullMie')	

	CompositeMie=Instance(IMie)  #This will store optical properties of the composite scattering cross section

	opticalgroup=Group(
			Tabbed(
				Item('FullMie', editor=InstanceEditor(), style='custom', label='Full Shell Particle', show_label=False, ),
				Group( 
					Item('CompositeMie', editor=InstanceEditor(), style='custom', label='Mixed Mie Particle', show_label=False), 	
					Item('CompositeMixStyle', style='custom', show_label=False),
					Item('CompositeMix', style='custom', show_label=False),				     
			   	    label='Composite Shell/core')
			      ),
			label='Optical Properties')

	compnpgroup=Group(
		 HGroup(Item('r_core'), Item('r_shell'), Item('x_unit', style='readonly'), Item('mviewbutton', label='Show Full material', show_label=False)),
			Group(
		  		Tabbed(
					Item('CoreMaterial', style='custom', label='NP Core', show_label=False), 
					Item('MediumMaterial', editor=InstanceEditor(),style='custom',  label='Medium Material', show_label=False),
					Item('ShellMaterial', editor=InstanceEditor(),style='custom', label='Shell Material', show_label=False),
					Include('opticalgroup'),
					Item('DiskCounter', style='custom', show_label=False, label='Layer Inclusions'),
				     label='Constituent Materials and Optical Properties' ), 
				),
	
			)
		

	traits_view=View(Include('compnpgroup'), title='Composite Nanoparticle with Shell', resizable=True )

	def __init__(self, *args, **kwds):
      	    super(NanoSphereShell, self).__init__(*args, **kwds)
            self.sync_trait('r_core', self.CompositeMie, 'r_core', mutual=False)  #COMPOSITE MIE TAKES R_CORE AND R_SHELL SO IF MUTUAL, IT WILL RESET  	
	    self.sync_trait('r_core', self.DiskCounter, 'r_particle')
	    self.sync_trait('Vfrac', self.DiskCounter, 'Vfrac')
	    self.sync_trait('MixingStyle', self.DiskCounter, 'MixingStyle')
	    self.sync_trait('MediumMaterial', self.ShellMaterial, 'Material2')
	    self.sync_trait('MediumMaterial', self.DiskCounter, 'Material2')

	def _CoreMaterial_default(self): return DrudeNew(specparms=self.specparms)#, r_core=self.r_core)   
	def _MediumMaterial_default(self): return self.Dispwater(specparms=self.specparms)   
	def _ShellMaterial_default(self): return self.SphericalInclusions_Shell(specparms=self.specparms)#, r_platform=self.r_core, r_particle=self.r_shell)

	def _FullMie_default(self): return self.sphere_shell(specparms=self.specparms, CoreMaterial=self.CoreMaterial, MediumMaterial=self.MediumMaterial, ShellMaterial=self.ShellMaterial)  
	def _CompositeMie_default(self): return self.sphere_full(specparms=self.specparms, CoreMaterial=self.NanoMaterial, MediumMaterial=self.MediumMaterial)

	def _NanoMaterial_default(self): return self.CompositeMaterial_Equiv(specparms=self.specparms, Material1=self.CoreMaterial, 
							Material2=self.ShellMaterial, r_particle=self.r_core, r_shell=self.r_shell)

	def _DiskCounter_default(self): return self.SphericalInclusions_Disk(specparms=self.specparms, Material1=self.NanoMaterial, material2=self.MediumMaterial, r_particle=self.r_core)

	def _Mix_default(self): return self.MG_Mod(specparms=self.specparms, solutematerial=self.NanoMaterial, solventmaterial=self.MediumMaterial)

	def _mat_name_default(self): 
		return str('Composite NP:  ')+str(self.Material1.mat_name)+' IN '+str(self.Material2.mat_name)

	def _ShellMaterial_changed(self):       
		self.FullMie.ShellMaterial=self.ShellMaterial 
		self.NanoMaterial.MediumMaterial=self.ShellMaterial

	def _CoreMaterial_changed(self):
		self.NanoMaterial.Material1=self.CoreMaterial
		self.FullMie.CoreMaterial=self.CoreMaterial
		self.CompositeMie.CoreMaterial=self.CoreMaterial

	def _MediumMaterial_changed(self):
		self.FullMie.MediumMaterial=self.MediumMaterial
		self.CompositeMie.MediumMaterial=self.MediumMaterial


	def _r_core_changed(self): 
#		self.CompositeMie.r_core=self.r_core
		self.ShellMaterial.r_platform=self.r_core  #CORE NP PARTICLE DETERMINES THE SIZE OF R_PLATFORM 
		self.CoreMaterial.r_core=self.r_core
		self.NanoMaterial.r_particle=self.r_core

	def _r_shell_changed(self):
		self.ShellMaterial.r_particle=self.r_shell         #ASSUMES SHELL THICKNESS IS DETERIMNED BY PARTICLE SIZES
		self.CompositeMie.r_core=(self.r_shell+self.r_core)
		self.NanoMaterial.r_shell=self.r_shell

if __name__ == '__main__':
	NanoSphereShell().configure_traits()

