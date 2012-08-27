from basic_material import BasicMaterial
from material_models import Sellmeir, Dispwater
from traits.api import *
from traitsui.api import *	
from interfaces import IMixer, IStorage, IMaterial
import math

class CompositeMaterial(BasicMaterial):
	'''Still inherits basic traits like earray, narray and how they are interrelated'''
	from modeltree_v2 import Main
	from material_mixer import MG_Mod, Bruggeman, QCACP, MG

	modeltree=Instance(Main,())
	Material1=Instance(IMaterial)
	Material2=Instance(IMaterial)   #Make these classes later
	MixingStyle=Enum('MGMOD', 'Bruggeman', 'QCACP', 'MG')
	Mix=Instance(IMixer)
	Vfrac=DelegatesTo('Mix')	#Coordinates with parameter in mixer
	earray=DelegatesTo('Mix', prefix='mixedarray')

	selectmat1=Button ; selectmat2=Button

	mixgroup=Group(   VGroup(
				HGroup(
					Item('MixingStyle', label='Mixing Method', show_label=False),
		 			Item('Mix', editor=InstanceEditor(), style='custom', label='Mixing Parameters', show_label=False ),
					),	
				Item('mviewbutton', label='Show Full Material', show_label=False),
							),    #Group Label here
			label='Mixing Parameters')            #View Label 

	compmatgroup=Group(Item('mat_name', label='Material Name'),
		Tabbed( 
	         Item('Material1', editor=InstanceEditor(), style='custom', label='Solute', show_label=False),
		 Item('Material2', editor=InstanceEditor(), style='custom', label='Solvent', show_label=False),
		      ),
		  HGroup(		
			Item('selectmat1', label='Change Solute', show_label=False), Item('selectmat2', label='Change Solvent', show_label=False),
			),
		label='Materials')

	traits_view=View(Item('specparms', style='custom'),Include('compmatgroup' ), Include('mixgroup'), resizable=True, buttons=OKCancelButtons)

	def __init__(self, *args, **kwds):
      	    super(CompositeMaterial, self).__init__(*args, **kwds)
            self.sync_trait('specparms', self.Material1, 'specparms', mutual=True)  	
            self.sync_trait('specparms', self.Material2, 'specparms', mutual=True)   	

	def _Material1_default(self): return Sellmeir() 
	def _Material2_default(self): return Dispwater() #MIXED MATERIAL WITH DEFAULTS DETERMINED BY THIS INSTANCE
	def _Mix_default(self): return self.MG_Mod(specparms=self.specparms, solventmaterial=self.Material2, solutematerial=self.Material1)
	def _MixingStyle_changed(self): 
		self.update_mix()
		self.update_mview()

	def _Material1_changed(self): 
                self.sync_trait('specparms', self.Material1, 'specparms', mutual=True)  	  #This is necessary because syncing is only done for the object
		self.update_mix()

	def _Material2_changed(self): 
                self.sync_trait('specparms', self.Material2, 'specparms', mutual=True)  	  #This is necessary because syncing is only done for the object
		self.update_mix()

#	def _specparms_changed(self):
#		if self.Material1.specparms != self.specparms:
#			self.Material1.specparm = self.specparms
#		if self.Material2.specparms != self.specparms:
#			self.Material2.specparm = self.specparms

	def update_mix(self):
		vfrac=self.Vfrac
		if self.MixingStyle=='MG':
			self.Mix=self.MG(specparms=self.specparms, solventmaterial=self.Material2, solutematerial=self.Material1, Vfrac=vfrac)
		elif self.MixingStyle=='Bruggeman':
			self.Mix=self.Bruggeman(specparms=self.specparms, solventmaterial=self.Material2, solutematerial=self.Material1,Vfrac=vfrac)
		elif self.MixingStyle=='QCACP':
			self.Mix=self.QCACP(specparms=self.specparms, solventmaterial=self.Material2, solutematerial=self.Material1,Vfrac=vfrac)
		elif self.MixingStyle=='MGMOD':
			self.Mix=self.MG_Mod(specparms=self.specparms, solventmaterial=self.Material2, solutematerial=self.Material1,Vfrac=vfrac)

	def _mat_name_default(self): return  (self.Material1.mat_name + '  IN   ' + self.Material2.mat_name)
		
	def _selectmat1_fired(self): 
		self.modeltree.configure_traits(kind='modal')
		selected_adapter=self.modeltree.current_selection[0]    #For some reason this returns a list
		selected_adapter.populate_object()
		print 'should i be here yet'
		self.Material1=selected_adapter.matobject

	def _selectmat2_fired(self): 
		self.modeltree.configure_traits(kind='modal')
		selected_adapter=self.modeltree.current_selection[0]  #For some reason this returns a list
		selected_adapter.populate_object()
		self.Material2=selected_adapter.matobject

	def _Vfrac_changed(self): 
		self.update_data() ; self.update_mview()

class CompositeMaterial_Equiv(CompositeMaterial):
	'''Like composite material except it uses equivalence method to mix spheres with shells'''
	from material_mixer import EquivMethod, CustomEquiv
	r_particle=Float(12)
	r_shell=Float(2)
	MixingStyle=Enum('Equivalence', 'Custom Equiv') 

	def update_mix(self):
		'''You don't want the mix to update everytime something changes, but do want update to run everytime mix changes'''
		if self.MixingStyle=='Equivalence':
			self.Mix=self.EquivMethod(specparms=self.specparms, solventmaterial=self.Material2, solutematerial=self.Material1, 
							r_particle=self.r_particle, r_shell=self.r_shell)
		elif self.MixingStyle=='Custom Equiv':
			self.Mix=self.CustomEquiv(specparms=self.specparms, solventmaterial=self.Material2, solutematerial=self.Material1,  
							r_particle=self.r_particle, r_shell=self.r_shell)
	def _MixingStyle_default(self): return 'Equivalence'

	def _Mix_default(self): 
		return self.EquivMethod(specparms=self.specparms, solventmaterial=self.Material2, solutematerial=self.Material1, 
							r_particle=self.r_particle, r_shell=self.r_shell)

	def _r_particle_changed(self): self.Mix.r_particle=self.r_particle

	def _r_shell_changed(self): self.Mix.r_shell=self.r_shell	

class SphericalInclusions(CompositeMaterial):
	'''Essentially a composite material except inclusions of spheres are integrated with the VFrac parameter in volume'''
	###SINCE ONLY METHODS I USE SO FAR USE SPHERICAL PARTICLES, THIS HAS unitvolume_sphere WHICH IS FOR SPHERICAL INCLUSIONS ONLY###
	platform_type=Str
	particle_type=Str('Spherical Inclusions')  
	mat_name=Str('Composite Material with Spherical Inclusions')

	r_particle=Float(2.0)     #Radius parameters for r_particle and r_platform respectively
	r_platform=Float(12.0)
	shell_thickness=Property(Float, depends_on='r_particle')  #Thickness of shell determined by 2r inclusion

	vbox=Property(Float, depends_on='r_particle')           #Box defined by diameter of sphere
	unitvolume=Property(Float, depends_on='r_particle')     #Total amount of volume occupied by the sphere 
	VT=Property(Float, depends_on='r_particle, r_platform') #DEFINED SEPARATELY FOR DIFFERENT PLATFORM TYPES

	N_tot=Property(Float, depends_on='VT, vbox')
	N_occ=Property(Float, depends_on='Vfrac, VT, unitvolume')

	vinc_occ=Property(Float, depends_on='N_occ, unitvolume')  #Total volume of the inclusions
	vshell_occ=Property(Float, depends_on='N_occ, vbox')      #Total volume of the shell filled by boxes

	coverage=Property(Float, depends_on='N_occ, N_tot')

	def _get_shell_thickness(self): return 2.0*self.r_particle

	def _get_vbox(self): return 8.0*(self.r_particle**3)           #Square boxes of volumes
	def _get_vinc_occ(self): return self.N_occ*self.unitvolume
	def _get_vshell_occ(self): return self.N_occ*self.vbox

	def _get_unitvolume(self): 
		value=(4.0*math.pi/3.0)*self.r_particle**3  #THIS IS ONLY VALID FOR SPHERE
		return round(value, 2)

	def _get_N_tot(self): return int(self.VT/self.vbox)   #Total number of available boxes is Vbox/VT
	def _get_N_occ(self): return  int((self.Vfrac * self.VT)/(self.unitvolume))
	def _set_N_occ(self, Nocc): 
		self.Vfrac= (Nocc * self.unitvolume)/self.VT 

	def _get_coverage(self): return round ( (float(self.N_occ) / float(self.N_tot) )*100.0 , 4)	
	def _set_coverage(self, coverage):
		self.N_occ=int( (coverage * self.N_tot) / 100.0	)
	
class SphericalInclusions_Shell(SphericalInclusions):
	'''Used for sphere/shell nanoparticles; shell thickness is automatically determined by r_particle (aka biotin radius)'''

	platform_type=Str('Shell Platform')   #Core particle  (Usually NP)

	inclusionsgroup=Group(
				HGroup(Item('particle_type', style='readonly'), Item('platform_type', style='readonly')), 
				 HGroup( Item('r_particle', label='Inclusion radius'), Item('shell_thickness', style='readonly')),
				(Item('r_platform')),

				HGroup(Item('coverage', label='Shell Coverage %'),Item('vinc_occ', label='Total inclusion volume') ),
				HGroup(Item('N_occ', label='Occupied Sites     '), Item('N_tot', label='Total Sites')),
				HGroup(Item('vshell_occ', label='Shell volume occupied'), Item('VT', label='Total shell volume')),
				Include('mixgroup'),
				label='Shell Inclusions and Mixing'    )

	traits_view=View(
			Include('compmatgroup'), Include('inclusionsgroup')
			 )


	def _get_VT(self): return round ( (4.0*math.pi/3.0) * (  (self.r_platform+2.0*self.r_particle)**3 - self.r_platform**3 ) , 2)

	def _Material1_default(self): return Sellmeir(specparms=self.specparms)
	def _Material2_default(self): return Dispwater(specparms=self.specparms)

	


class SphericalInclusions_Disk(SphericalInclusions):

	platform_type=Str('Disk')                 #Fiber endface
	particle_type=Str('Spherical Particles')  #Nanoparticles

	def _r_platform_default(self): return 31250.0

	def _get_VT(self): return round( math.pi * self.r_platform**2 * self.shell_thickness, 2)

	inclusionsgroup=Group(
				HGroup(Item('particle_type', style='readonly'), Item('platform_type', style='readonly')), 
				 HGroup( 
					Item('r_particle', label='Particle Size'), Item('r_platform'),
					),

				HGroup(Item('coverage', label='Shell Coverage %'),Item('vinc_occ', label='Total inclusion volume', style='readonly') ),
				HGroup(Item('N_occ', label='Occupied Sites     '), Item('N_tot', label='Total Sites', style='readonly')),
				HGroup(Item('vshell_occ', label='Shell volume occupied'), Item('VT', label='Total shell volume', style='readonly')),
				Include('mixgroup'),
				label='Layer Inclusions and Mixing'    )

	traits_view=View(
		#	Include('compmatgroup'),
			 Include('inclusionsgroup')
			 )

##########Class nanoparticles##########



if __name__ == '__main__':

	f=CompositeMaterial()
	f.configure_traits()

