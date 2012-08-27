import numpy as np
import math, cmath
from numpy.lib import scimath as SM
import re, os, sys
from traits.api import *
from traitsui.api import *
from layer_plotter import MaterialView, ScatterView
import scipy
from converter import SpectralConverter
from main_parms import SpecParms
from interfaces import IMaterial, IMie

ModelTypes = {
	    'Python': [ '.py' ],
	    'Sopra':      [ '.nk'],
	    'Other':    [ '.txt', '.data' ],   #CAN EDIT MODULE WHICH CONTROLS THIS TO ADD "ANY" OPTION, OR MAYBE FILTER = NONE OPTION
	    'Java':   [ '.java' ],
	    'Ruby':   [ '.rb' ]
	       }


#BUG::::
# UPDATE_DATA() SHOULD NOT NEED ARGUMENTS, BUT WHEN I DEFINE IT FOR MANY MATERIALS LIKE "COMPOSITE MATERIAL", ALL OF THE SUDDEN IT BECOMES A DIFFERENT TYPE WHICH REQUIRES
# TWO ARGUMENTS (SOMETHING LIKE AN INFO OBJECT)

class basic_material(HasTraits):
	implements(IMaterial)
	###THESE MUST BE SET BY USER###
	specparms=Instance(SpecParms,())

	lambdas=DelegatesTo('specparms')	
	x_unit=DelegatesTo('specparms')    #Actually used in the model, always kept at a default unit setting (Nanometers)
	valid_units=DelegatesTo('specparms') #ONLY NEEDED IF YOU WANT X-UNITS IN VIEW SINCE THESE ARE LINKED VIA METADATA
	


 	### MOST OF THESE WILL BE AUTOPOPULATED BY PARTICLUAR FILE/METHOD USED TO GENERATE THEM###
	earray=CArray()   #CAN BE REDIFINED IN LATER OBJECTS TO MAKE IT AUTOMATICALLY UPDATE WITH LAMBDAS
	narray=Property(CArray, depends_on=['earray'])
	karray=Property(CArray, depends_on=['narray'])  #Wave vectors

	mat_name=Str()
	source=Enum('Model', 'File', 'Custom')
	c=Float(299792458)     #Speed of light m/s

	### VIEW AND RELATED TRAITS###
	mview=MaterialView()   
	mviewbutton=Button 
	ui =Any           #Instance( UIInfo )  ??

	basic_group=VGroup( 	Item('mat_name', label='Material Name', style='simple'),
			        Item('mviewbutton', label='Show Material'))

	traits_view=View(
			Include('basic_group'), id='lol',
			resizable=True
			)

	def __init__(self, *args, **kwargs):
	        super(HasTraits, self).__init__(*args, **kwargs)
		self.update_data()

	def _earray_default(self): return np.empty(self.lambdas.shape, dtype='complex')   #Used later so not always redeclaring this
	def _karray_default(self): return np.empty(self.lambdas.shape, dtype='complex')   #Used later so not always redeclaring this
	def _narray_default(self): return np.empty(self.lambdas.shape, dtype='complex')   #Used later so not always redeclaring this

	def _lambdas_changed(self): self.update_data()
	def _earray_changed(self): 
		self.update_mview()

	def _x_unit_changed(self): self.update_mview()

	def update_data(self): pass

	def update_mview(self): 
		if self.ui is not None:           #If window is not open, pass
			self.mview.update(self.lambdas, self.earray, self.narray, self.x_unit)	

	def _mviewbutton_fired(self): 
		if self.ui is not None:         #Kills window if it's already open and update is fired
			self.ui.dispose()
		self.mview.update(self.lambdas, self.earray, self.narray, self.x_unit)	 
		self.ui=self.mview.edit_traits()

	def complex_n_to_e(self, narray): 		
		self.earray=np.empty(narray.shape, dtype='complex')  #This is necessary if changing lambdas, so everything works
		nr=narray.real; nk=narray.imag          #NEED TO VERIFY THESE WORK SEE PLOT VS OLD VALUES
 		self.earray.real = nr**2 -nk**2
		self.earray.imag = 2.0*nr*nk

	def complex_e_to_n(self): return SM.sqrt(self.earray)  #Return narray given earray

	def _get_narray(self):  return self.complex_e_to_n()                #get/set format used to ensure dual-population
	def _set_narray(self, narray): self.complex_n_to_e(narray)  
	def _get_karray(self): return (2.0*math.pi*self.narray)/(self.lambdas)
   



class basic_interp(basic_material):
	'''For materials imported from file or custom made generally a set of interpolting functions is necessary'''
	xarray_interp=Array()
	earray_interp=Property(CArray, depends_on=['xarray_interp'])
	narray_interp=Property(CArray, depends_on=['xarray_interp'])  #Setup arrays for holding experimental values

        ###Should not be passing these interpolated arrays, so no need to make properties of each other###
     
	def _get_earray_interp(self): return np.interp(self.lambdas, xarray_interp, self.earray)
	def _get_narray_interp(self): return np.interp(self.lambdas, xarray_interp, self.narray)   

	###NEED TO DEFINE IN CONTEXT OF UPDATE MODEL FORMALISM????

class basic_file(basic_material):
	'''Has no implementation of mat_name...maybe that's ok'''
	source='File'
	thefile=File() #Shortname? of file
	file_id=Str()  #Used to identify with methods below.  For example, Sopra is "Sopra"
	file_extenstion=Str() #Again, not all files may have this

	header=Str()       #Not all files will have this (CHANGE TO BOOL AND MAKE A GET HEADER METHOD IN GENERAL)
	headerlist=Property(List, depends_on='header')
	headerstatus=Bool(False)
	datalines=List()  #Data stored as lines
	datalist=Property(List, depends_on='datalines')

	xstart=Float()
	xend=Float()
	xpoints=Int()
	default_unit=Str()        #DEFAULT SPECTRAL UNIT IN A FILE

	lambdas=Array()           #No Longer Delegates

	def _thefile_changed(self): 
		self.header_data()	
		self.update_file()  
		self.update_mview()

	def update_file(self): 	pass

	def _get_datalist(self):
		'''Given the data as a list of lines, turns it into a list of lists'''
		data=[]
		for line in self.datalines:
			newline=line.strip().split()
			newlist=[]
			for entry in newline:
				newentry = float(entry)
				newlist.append(newentry)
			data.append(newlist)
		return data

	def _get_headerlist(self): return self.header.strip().split()

	def header_data(self):
		'''Should be general enough to fit all files with comment characters on first line'''
		f=open(self.thefile, 'r')
		data=f.readlines()
		firstline=data[0]
		if re.match('#', firstline):
			self.header=firstline 
			self.headerstatus=True
			data.pop(0)     #IF HEADER FOUND, POP IT OUT

		return data  #Datalist is set as property

class LamNK(basic_file):
	'''Format is Lambdas, N, K'''
	fileid='Lam_n_k'
	file_extension='.txt'  #FIX LATER

	def update_file(self):
		self.get_header_data()
	
	traits_view=View(Item('header', style='readonly') )
	

class SopraFile(basic_file):  

	###NEEDS FIXED TO WORK W NEW SPECPARMS AND STUFF###
	
	file_id='Sopra'
	file_extension='.nk'
	lam_code=Enum(1,2,3,4)     #SOPRA-specific integer code to determine name of the lambda unit
		
	traits_view=View(  
			Item('thefile', editor=FileEditor() ) , Item('header' ),
			HGroup(
			 Item('xstart', style='readonly') , Item('xend', style='readonly'),	Item('xpoints', style='readonly'),
			      ),
			 Item('mviewbutton', label='Show Material', show_label=False),
			 Item('default_unit', label='File spectral unit', style='readonly'), 
			 Item('x_unit', style='readonly', label='Current spectral unit'),
			 resizable=True, buttons=['Undo']
			)

	def lam_decode(self):
		'''Converts sopra unit integer code to forms appropriate to this'''
		if self.lam_code==0:
			self.default_unit='eV'
		elif self.lam_code==1:
			self.default_unit='Micrometers'
		elif self.lam_code==2:
			self.default_unit='cm-1'   #Inverse centimeters	
		elif self.lam_code==3:
			self.default_unit='Nanometers'
		if self.default_unit != self.x_unit:
	   	     f=SpectralConverter(input_array=self.lambdas, input_units=self.default_unit, output_units=self.x_unit)
   		     self.lambdas=f.output_array
		

	def update_file(self):
		if self.headerstatus == True:
			self.lam_code=int(self.headerlist[0])
			self.xstart=float(self.headerlist[1])
			self.xend=float(self.headerlist[2])
			self.xpoints=int(self.headerlist[3])
			self.lambdas=np.linspace(self.xstart, self.xend, self.xpoints+1)  #NEED TO ADD THIS +1 SIMPLY BECAUSE
			self.lam_decode()
			ns=np.empty(len(self.datalist), dtype=complex)
			for i in range(len(self.datalist)):
				line=self.datalist[i]
				ns[i]=complex(float(line[0]), float(line[1]))
			self.narray=ns

	def header_data(self):
		'''Slightly modified for unusual sopra header'''
		f=open(self.thefile, 'r')
		data=f.readlines()
		firstline=data[0]
		if len(firstline.strip().split()) != 4:         #Crude file format test
			self.header='SOPRA FORMAT INCORRECT'
		else:
			self.header=firstline
			self.headerstatus=True
			data.pop(0)     #IF HEADER FOUND, POP IT OUT
		self.datalines=data



class basic_model(basic_material):	
	source='Model'
	model_id=Str('')    #model ID references the model used to construct the array

class Constant(basic_model):
	constant=Complex()  #Defines constant value for earray (NOT NARRAY)
	model_id=Str('constant')   

	def _constant_changed(self):
		self.update_data()
		self.update_mview()
	
	def _mat_name_default(self): return  'Constant Dielectric:'+'['+str(self.constant) +']'
	def update_data(self): self.earray[:]=self.constant

	traits_view=View (
			 Include('basic_group'),
			 Item('constant'),
			 resizable=True
			 )

class Sellmeir(basic_model):
	'''Returns sellmeir dispersion of glass'''
	mat_name=Str('Dispersive Glass')
	model_id=Str('sellmeir')   

	a1=Float(.6961663) ; a2=Float(.8774794) ;  a3=Float(.4079426)
	b1=Float(.0684043) ; b2=Float( 9.896161) ; b3=Float(.1162414)		

	sellmeir_group=VGroup(HGroup(Item('a1'), Item('a2'), Item('a3')),
			      HGroup(Item('b1'), Item('b2'), Item('b3'))) 
			

	traits_view=View (
			VGroup( Include('basic_group'), Include('sellmeir_group') ),
						 resizable=True
			 )


	def _a1_changed(self): self.update_data(); self.update_mview()  #NEED TO ADD THIS FOR ALL VARIABLES

	def _mat_name_default(self): return 'Sellmeir'	
	def update_data(self):		
		um_xarray=self.specparms.specific_array('Micrometers')
		l_sqr=um_xarray**2
		f1=(self.a1*l_sqr)/(l_sqr - self.b1**2)
		f2=(self.a2*l_sqr)/(l_sqr - self.b2**2)       #Dummy indicies
		f3=(self.a3*l_sqr)/(l_sqr - self.b3**2)  
		self.narray = np.sqrt(1.0 + f1 + f2 + f3)	

class Dispwater(basic_model):
	'''Returns dispersion of water as put in some paper'''
	A=Float(3479.0) ; B=Float(5.111 * 10**7)  #WHAT UNITS
	model_id=Str('Dispwater')   

	def _mat_name_default(self): return  'Dispersive Water'	
	def update_data(self): 	
		self.narray=1.32334 + (self.A/ self.lambdas**2 ) - (self.B/self.lambdas**4)   #Entry in nm

	def _A_changed(self): self.update_data(); self.update_mview()
	def _B_changed(self): self.update_data(); self.update_mview()

	traits_view=View (
			 Group(Include('basic_group'), HGroup(Item('A', style='simple'), Item('B', style='simple'))),		
							 resizable=True
			 )

class Metals_plasma(HasTraits):
	metals_dic= DictStrList()
	name=Str()
	lam_plasma=Float()
	lam_collis=Float()
	keys=Any
	def __init__(self):
		self.metals_dic.key_trait = self.name
		self.metals_dic.value_trait = [self.lam_plasma, self.lam_collis]
		self.metals_dic['gold']=[1.6726 *10**-7, 8.9342 * 10**-6]
		self.name='gold'
		self.lam_plasma=self.metals_dic[self.name][0]	
		self.lam_collis=self.metals_dic[self.name][1]
		self.keys=(self.metals_dic.keys())     #WHAT IS THE TRAIT EQUIVALENT OF THIS?


class basic_metal_model(basic_model):
	lam_plasma=Float()   #Plasma frequency
	lam_collis=Float()   #Collision frequency
	freq_plasma=Float()
	freq_collis=Float()

	def _lam_plasma_changed(self): self.update_Data; self.update_mview
	def update_data(self): pass

        #SET FREQENCY/WAVELENGTH TO BE RECIPROCAL OF EACH OTHER LIKE N/E WITH FREQUENCY BEING CANONICAL REPRESENTATION

class Drude_bulk(basic_metal_model):
	'''Taken from another gupta paper to test form.  I think this is valid for a metal sheet, not np's'''

	model_id=Str('drude_bulk')   

	valid_metals=Enum('gold','silver','aluminum','copper')  #Currently only 

	traits_view=View(
			Item('valid_metals'), Item('mat_name', label='Custom Name'), Item('lam_plasma'), Item('mviewbutton'), Item('x_unit')
			)

	def _valid_metals_default(self): return 'gold'      #NEED TO MAKE METALS DIC THEN DEFAULT TO THAT 
	def _lam_plasma_default(self): return 1.6826 * 10**-7
	def _lam_collis_default(self): return 8.9342 * 10**-6
	def _mat_name_default(self): return 'Drude Metal'
	
	def _valid_metals_changed(self):
		if self.valid_metals == 'gold':               #These effects may be size dependent, need to look into it.  
			self.lam_plasma=(1.6826 * 10**-7) #m
			self.lam_collis=(8.9342 * 10**-6) #m
		elif self.valid_metals == 'silver':
			self.lam_plasma=(1.4541 * 10**-7) #m
			self.lam_collis=(1.7614 * 10**-5) #m	
		elif self.valid_metals == 'aluminum':
			self.lam_plasma=(1.0657 * 10**-7) #m
			self.lam_collis=(2.4511 * 10**-5) #m	
		elif self.valid_metals == 'copper':
			self.lam_plasma=(1.3617 * 10**-7) #m
			self.lam_collis=(4.0825 * 10**-5) #m	

	def update_data(self):   #THIS DOES FIRE AT INSTANTIATION
		m_xarray=self.specparms.specific_array('Meters')
		unity=np.array([complex(0.0,1.0)], dtype='complex')  #Gupta requries i * lambda, so this gets complex value of the xarray
		self.earray = 1.0 - ( (m_xarray**2 * self.lam_collis) / (self.lam_plasma**2 * ( self.lam_collis + m_xarray*unity)  ) )


###INHERIT LATER FROM BASIC NANOSPHERE###

class CompositeMaterial(basic_material):
	'''Still inherits basic traits like earray, narray and how they are interrelated'''
	from material_mixer import MG_Mod, Bruggeman, QCACP, MG
	from interfaces import IMixer, IStorage
#	from material_editor_v2 import MaterialStorage

	Material1=Instance(IMaterial)
	Material2=Instance(IMaterial)   #Make these classes later
	MixingStyle=Enum('MGMOD', 'Bruggeman', 'QCACP', 'MG')
	Mix=Instance(IMixer)
	Vfrac=DelegatesTo('Mix')	#Coordinates with parameter in mixer
	earray=DelegatesTo('Mix', prefix='mixedarray')

#	selectmat1=Button ; selectmat2=Button

	matstorage=Instance(IStorage)

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
		label='Materials')

	traits_view=View(Include('compmatgroup' ), Include('mixgroup'), resizable=True, buttons=OKCancelButtons)


	def _Material1_default(self): return Sellmeir(specparms=self.specparms) 
	def _Material2_default(self): return Dispwater(specparms=self.specparms) #MIXED MATERIAL WITH DEFAULTS DETERMINED BY THIS INSTANCE
	def _Mix_default(self): return self.MG_Mod(specparms=self.specparms, solventmaterial=self.Material2, solutematerial=self.Material1)
	def _MixingStyle_changed(self): 
		self.update_mix()
		self.update_mview()

	def _Material1_changed(self): 
		self.Material1.specparms=self.specparms #Autosyncs materials
		self.update_mix()

	def _Material2_changed(self): 
		print 'mat 2 changing'
		self.Material2.specparms=self.specparms  
		self.update_mix()

	def _specparms_changed(self):
		if self.Material1.specparms != self.specparms:
			self.Material1.specparm = self.specparms
		if self.Material2.specparms != self.specparms:
			self.Material2.specparm = self.specparms

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
		
#	def _selectmat1_fired(self): 
#		self.matstorage=self.MaterialStorage(specparms=self.specparms)
#		f=self.matstorage.configure_traits(kind='nonmodal')
#		if f.current_selection != None:
#			self.material1=f.current_selection 
	
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

	def _r_particle_changed(self): 
		print self.Material1
		self.Mix.r_particle=self.r_particle
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

				HGroup(Item('coverage', label='Shell Coverage %'),Item('vinc_occ', label='Total inclusion volume') ),
				HGroup(Item('N_occ', label='Occupied Sites     '), Item('N_tot', label='Total Sites')),
				HGroup(Item('vshell_occ', label='Shell volume occupied'), Item('VT', label='Total shell volume')),
				Include('mixgroup'),
				label='Layer Inclusions and Mixing'    )

	traits_view=View(
			Include('compmatgroup'), Include('inclusionsgroup')
			 )

##########Class nanoparticles##########

class NanoSphere(CompositeMaterial):
	'''Technically a nanosphere always needs a medium anyway, so make it composite object'''
	from mie_traits_delegated import sphere_full, sphere
	from alias import Alias

	mat_name=Str('Bare Nanosphere')
	FullMie=Instance(IMie)  #Used to compute scattering properties	

	MediumMaterial=Instance(IMaterial)       #GOING TO JUST BE RENAMED FROM MATERIAL 1 AND 2
	CoreMaterial=Instance(IMaterial)

	r_core=DelegatesTo('FullMie')

	traits_view=View(Item('show_mie'), Item('CoreMaterial'), Item('MediumMaterial'), Item('r_core'), Item('sview'), Item('x_unit', style='readonly'), Item('FullMie') )

	def _MediumMaterial_default(self): return self.Material2
	def _CoreMaterial_default(self): return self.Material1

	def _FullMie_default(self): return self.sphere_full(specparms=self.specparms, CoreMaterial=self.CoreMaterial, MediumMaterial=self.MediumMaterial)

	def _MediumMaterial_changed(self): 
		self.FullMie.MediumMaterial=self.MediumMaterial   
		self.Material2=self.MediumMaterial

	def _CoreMaterial_changed(self):
		self.FullMie.CoreMaterial=self.CoreMaterial  
		self.Material1=self.CoreMaterial
		print 'recognize\n\n\n\n\n\n\n\n\n'


class DrudeNew(basic_metal_model, NanoSphere):
	mat_name=Str('Drude Gold Nanoparticle')
	model_id=Str('DrudeNew')
	valid_metals=Enum('gold') 
	lamp=Float(145)
	gamp=Float(17000)
	nm_conv=Float(.000000001)   #why is lamp in these units?
	wplasma=Float()  #1.29 E 16
	v_fermi=Float(1.4 * 10**6)         #Same for gold and silver

	traits_view=View( Item('mat_name', show_label=False), Item('mviewbutton', label='Show Dielectric', show_label=False), Item('r_core', show_label=True, style='simple', label='NP Radius'))


	def _wplasma_default(self): return 2.0*math.pi*self.c/(self.lamp * self.nm_conv)
			
	def update_data(self):           #THIS IS TOTALLY OLD WAY NEED TO UPDATE BUT NOT TRIVIAL
		eeff=np.empty(self.lambdas.shape, dtype='complex')
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




###The composite nanoparticle derives many of its listeners and properties frmo composite material; however, it is a single material.  Strictly
### speaking, it should be defined by a core material, shell material then a surrounding medium.  I used the material1 material2 trait attributes
### from the composite material object, then put the surrounding medium as a third material.  Therefore, the trait listeners are sorta of hybrids
### but this was the best option rather than trying to reinvent the wheel.  

class NanoSphereShell(NanoSphere):
	'''This is a single object, but it inheres from composite material to allow for trait changes and stuff to be understood'''		
	from mie_traits_delegated import sphere_shell
	from material_mixer import EquivMethod, CustomEquiv

	###Note: NanoSphereShell "Mix" variable mixes the shell and core materials into a composite mateiral using the equivalence method.
	### The shell material is mixed using standard mixing rules.
	### 		

	ShellMaterial=Instance(IMaterial)

	r_shell=DelegatesTo('FullMie')	

	CompositeMie=Instance(IMie)  #This will store optical properties of the composite scattering cross section

	MixingStyle=Enum('Equivalence', 'Custom Equiv') #THESE ARE FOR MIXING INCLUSIONS INTO THE SHELL, NOT THE MIXING OF THE SHELL/CORE COMPOSITE!

	###Redefine mix group for aesthetic reasons###
	shellmixgroup=Group(   VGroup(            
				Item('MixingStyle', label='Shell Mixing Method', show_label=False),
		 		Item('Mix', editor=InstanceEditor(), style='custom', label='Shell Mixing Parameters', show_label=False ),
		        label='Shell Equivalence Mixing',),  #Group Label
		      )

	compnpgroup=Group(
		 HGroup(Item('r_core'), Item('r_shell'), Item('x_unit', style='readonly')),
		   HSplit(
			Group(
		  		Tabbed(
					Item('CoreMaterial', editor=InstanceEditor(), style='custom', label='Core Material', show_label=False),  
					Item('MediumMaterial', editor=InstanceEditor(),style='custom',  label='Medium Material', show_label=False),
					Item('ShellMaterial', editor=InstanceEditor(),style='custom', label='Shell Material', show_label=False),
				      ), 
				),
			Tabbed(
				Item('FullMie', editor=InstanceEditor(), style='custom', label='Full Shell Particle', show_label=False), 
				Group(	
					Item('CompositeMie', editor=InstanceEditor(), style='custom', label='Mixed Mie Particle', show_label=False), 	
 	 			        Include('shellmixgroup'),
					Item('mviewbutton', label='Show Composite Nanoparticle'),
				    label='Composite Shell/Core Particle' 
				     )
			      ),
			 ),
			)
		

	traits_view=View(Include('compnpgroup'), title='Composite Nanoparticle with Shell', resizable=True )

	### Full optical properties are based on core, medium and a composite shell ###
	### Composite optical properties are based on core/shell mixture being passed as and effective "core" ###

	def update_mix(self):
		'''You don't want the mix to update everytime something changes, but do want update to run everytime mix changes'''
		if self.MixingStyle=='Equivalence':
			self.ShellMix=self.EquivMethod(specparms=self.specparms, solventmaterial=self.ShellMaterial, solutematerial=self.CoreMaterial, 
							r_particle=self.r_core, r_shell=self.r_shell)
		elif self.MixingStyle=='Custom Equiv':
			self.ShellMix=self.CustomEquiv(specparms=self.specparms, solventmaterial=self.ShellMaterial, solutematerial=self.CoreMaterial,  
							r_particle=self.r_core, r_shell=self.r_shell)

	def _FullMie_default(self): return self.sphere_shell(specparms=self.specparms, CoreMaterial=self.CoreMaterial, MediumMaterial=self.MediumMaterial, ShellMaterial=self.ShellMaterial)  

	def _CompositeMie_default(self): return self.sphere_full(specparms=self.specparms, CoreMaterial=self, MediumMaterial=self.MediumMaterial)

	def _ShellMaterial_default(self): return SphericalInclusions_Shell(specparms=self.specparms)

	def _CoreMaterial_default(self): return DrudeNew(specparms=self.specparms)

	def _ShellMaterial_changed(self):
		self.FullMie.ShellMaterial=self.ShellMaterial 

	### SHELL MIX METHODS MAKE A COMPOSITE OUT OF THE SHELL###
	### MIX METHODS MAKE A COMPOSITE OUT OF HTE CORE/SHELL ###

	def _Mix_default(self): return self.EquivMethod(specparms=self.specparms, solventmaterial=self.ShellMaterial, solutematerial=self.CoreMaterial,  
							r_particle=self.r_core, r_shell=self.r_shell)

	def _mat_name_default(self): 
		return str('Composite NP:  ')+str(self.Material1.mat_name)+' IN '+str(self.Material2.mat_name)

	def _r_core_changed(self): 
		self.CompositeMie.r_core=self.r_core  #Full mie already changed by NanoSphere inheritance
		self.ShellMaterial.r_platform=self.r_core  #CORE NP PARTICLE DETERMINES THE SIZE OF R_PLATFORM 
		self.CoreMaterial.r_core=self.r_core
		self.Mix.r_particle=self.r_core

	def _r_shell_changed(self):
		self.ShellMaterial.r_particle=self.r_shell         #ASSUMES SHELL THICKNESS IS DETERIMNED BY PARTICLE SIZES
		self.CompositeMie.r_core=(self.r_shell+self.r_core)
		self.Mix.r_shell=self.r_shell

class NanoSphereShell_advanced(NanoSphere):
	'''This is a single object, but it inheres from composite material to allow for trait changes and stuff to be understood'''		
	from mie_traits_delegated import sphere_shell
	from interfaces import IMixer, IStorage

	###Note: NanoSphereShell "Mix" variable mixes the shell and core materials into a composite mateiral using the equivalence method.
	### The shell material is mixed using standard mixing rules.
	### 		

	ShellMaterial=Instance(IMaterial)
	CoreShellMaterial=Instance(IMaterial)
	CoreShellMix=DelegatesTo('CoreShellMaterial', prefix='Mix')
	CoreShellMixStyle=DelegatesTo('CoreShellMaterial', prefix='MixingStyle')

	r_shell=DelegatesTo('FullMie')	

	CompositeMie=Instance(IMie)  #This will store optical properties of the composite scattering cross section


	###Redefine mix group for aesthetic reasons###
	shellmixgroup=Group(   VGroup(            
				Item('CoreShellMixStyle', label='Core Shell Mixing Method', show_label=True),
		 		Item('CoreShellMix', editor=InstanceEditor(), style='custom', label='Core/Shell Equiv Parameters', show_label=False ),
		        label='Shell Equivalence Mixing',),  #Group Label
		      )

	compnpgroup=Group(
		 HGroup(Item('r_core'), Item('r_shell'), Item('x_unit', style='readonly')),
		   HSplit(
			Group(
		  		Tabbed(
					Item('CoreMaterial', editor=InstanceEditor(), style='custom', label='Core Material', show_label=False),  
					Item('MediumMaterial', editor=InstanceEditor(),style='custom',  label='Medium Material', show_label=False),
					Item('ShellMaterial', editor=InstanceEditor(),style='custom', label='Shell Material', show_label=False),
				      ), 
				),
			Tabbed(
				Item('FullMie', editor=InstanceEditor(), style='custom', label='Full Shell Particle', show_label=False), 
				Group(	
					Item('CompositeMie', editor=InstanceEditor(), style='custom', label='Mixed Mie Particle', show_label=False), 	
 	 			        Include('shellmixgroup'),
					Item('mviewbutton', label='Show Composite Nanoparticle'),
				    label='Composite Shell/Core Particle' 
				     )
			      ),
			 ),
			)
		

	traits_view=View(Item('Mix'), Item('Material1'), Item('CoreMaterial'),Include('compnpgroup'), title='Composite Nanoparticle with Shell', resizable=True )

	### Full optical properties are based on core, medium and a composite shell ###
	### Composite optical properties are based on core/shell mixture being passed as and effective "core" ###

	def _FullMie_default(self): return self.sphere_shell(specparms=self.specparms, CoreMaterial=self.CoreMaterial, MediumMaterial=self.MediumMaterial, ShellMaterial=self.ShellMaterial)  


	def _ShellMaterial_default(self): return SphericalInclusions_Shell(specparms=self.specparms)

	def _CoreMaterial_default(self): return DrudeNew(specparms=self.specparms)

	def _CoreShellMaterial_default(self): return CompositeMaterial_Equiv(specparms=self.specparms, Material1=self.CoreMaterial, 
							Material2=self.ShellMaterial, r_particle=self.r_core, r_shell=self.r_shell)

	def _CompositeMie_default(self): return self.sphere_full(specparms=self.specparms, CoreMaterial=self.CoreShellMaterial, MediumMaterial=self.MediumMaterial)

#	def _CoreShellMix_default(self): return self.CoreShellMaterial.Mix
#	def _CoreShellMixStyle_default(self): return self.CoreShellMaterial.MixingStyle
	

	def _ShellMaterial_changed(self):       #THESE ARE INSUFFICIENT
		self.FullMie.ShellMaterial=self.ShellMaterial 
		self.CoreShellMaterial.Material2=self.ShellMaterial

	def _CoreMaterial_changed(self):
		self.CoreShellMaterial.Material1=self.CoreMaterial

	def _mat_name_default(self): 
		return str('Composite NP:  ')+str(self.Material1.mat_name)+' IN '+str(self.Material2.mat_name)

	def _r_core_changed(self): 
		self.CompositeMie.r_core=self.r_core
		self.ShellMaterial.r_platform=self.r_core  #CORE NP PARTICLE DETERMINES THE SIZE OF R_PLATFORM 
		self.CoreMaterial.r_core=self.r_core
		self.CoreShellMaterial.r_particle=self.r_core

	def _r_shell_changed(self):
		self.ShellMaterial.r_particle=self.r_shell         #ASSUMES SHELL THICKNESS IS DETERIMNED BY PARTICLE SIZES
		self.CompositeMie.r_core=(self.r_shell+self.r_core)
		self.CoreShellMaterial.r_shell=self.r_shell

	
if __name__ == '__main__':

#	f=NanoSphereShell_advanced()

#	f=LamNK(thefile='/home/glue/Desktop/11_11_Reboot/Fiber_modeling/Optical_metal_data/Converted_Files/JC_Gold.txt')
#	f=SopraFile(thefile='/home/glue/Desktop/11_11_Reboot/Fiber_modeling/Optical_metal_data/SOPRA_nk_files/Ag.nk')

	f=NanoSphere()
#	f=CompositeMaterial_Equiv()
#	e=CompositeMaterial(Material1=f, Material2=g)
#	print f.Material1.earray
	f.configure_traits()

