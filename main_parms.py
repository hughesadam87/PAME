from traits.api import *
from traitsui.api import *
from converter import SpectralConverter
from numpy import linspace, sin, cos, empty, argsort
import math

class SpecParms(HasTraits):
	'''Global class which defines variables and methods shared by all other class methods''' 

	conv=Instance(SpectralConverter)  
        valid_units = DelegatesTo('conv')
        x_unit = Enum(values='valid_units')   #THIS IS HOW YOU DEFER A LIST OF VALUES TO ENUM

	lambdas=Array

	######THESE PROPERTY DEFINITIONS ARE CAUSING AN UPDATE ISSUE, MIXING PROPERTY AND LISTENERS...NEED AN "UPDATE" METHOD TO JUST SYNC THESE...###
	
	x_samples=Property(Int, depends_on=['lambdas'])
	xstart=Property(Float, depends_on=['lambdas'])
	xend=Property(Float, depends_on=['lambdas'])
	x_increment=Property(Float, depends_on=['x_samples', 'xstart', 'xend'])


	traits_view = View(
		VGroup(
		   HGroup(  Item(name = 'xstart'),  Item(name = 'xend'), Item(name = 'x_increment'), Item(name='x_samples') ),
	   	   HGroup(  Item(name='x_unit', style='readonly'), Item(name='x_unit', style='simple', label='Change Units' ) 
			  ), #    label='Spectral Parameters'
			))

	def _conv_default(self): return SpectralConverter(input_array=self.lambdas, input_units='Nanometers')
	def _lambdas_default(self): return linspace(300,800,300)
	def _x_unit_default(self): return 'Nanometers'
	def _valid_units_default(self): return self.conv.valid_units

	#@cached_property
	def _get_x_samples(self): return self.lambdas.shape[0]

	def _set_x_samples(self, samples):
		self.lambdas=linspace(self.xstart, self.xend, num=samples)
		
	#@cached_property
	def _get_x_increment(self):  
		return float(abs(self.xstart - self.xend))/float(self.x_samples)

	def _x_unit_changed(self):
		self.conv.output_units=self.x_unit     #INPUT ALWAYS KEPT AT NANOMETERS, THIS IS IMPORTANT DONT EDIT
		self.lambdas = self.conv.output_array

	#@cached_property
	def _get_xstart(self): return self.lambdas[0]

	#@cached_property
	def _get_xend(self):  return self.lambdas[-1]

	def _set_xstart(self, xstart): 
		self.lambdas=linspace(xstart, self.xend, num=self.x_samples)

	def _set_xend(self, xend):
		self.lambdas=linspace(self.xstart, xend, num=self.x_samples)

	def specific_array(self, new_unit): 
		"""Method Used to return a unit-converted array to models which specifically require certain unit systems (aka uM)"""
		if new_unit not in self.valid_units:
			print 'could not update based on this non_valid unit,', str(new_unit)
			return self.lambdas
		else:
			self.conv.input_array=self.lambdas
			self.conv.output_units=new_unit
			return self.conv.output_array   


class FiberParms(HasTraits):
	Config=Enum('Reflection', 'Transmission')
	Mode=Enum('TE', 'TM', 'Mixed')
	Lregion=Float(1500) #um or cm
	Dcore=Float(125)  #um
	Rcore=Property(Float, depends_on=['Dcore'])
	NA=Float(.24)
	theta_max=Property(Float, depends_on=['NA'])

	angle_start=Float(.5);  angle_stop=Float();	angle_inc=Float(.5)

	theta_max=Property(Float, depends_on=['NA'])

	angle_samples=Property(Int, depends_on=['angle_start', 'angle_stop', 'angle_inc'])
	angles=Property(Array, depends_on=['angle_samples, Config']) 

	N=Property(Array, depends_on=['Config', 'angles', 'Lregion', 'Dcore'])  #NUMBER OF REFLECTIONS

	sa=Property(Array, depends_on='angles')   #Sin and cosine of the angles, handy in other portion of code
	ca=Property(Array, depends_on='angles') 


        SharedGroup = Group(Item('Config'), Item('Mode'),
                   HGroup(Item(name='NA', label='Numerical Aperature'), Item('theta_max', label='Critical Angle')),
			VGroup(
				Item('angle_start', label='Angle Start'), 
				Item('angle_stop', label='Angle End'), 
				Item('angle_inc', label='Angle Increment'),
			      ),
                   show_border = True, #group border
		   )

	RefGroup=Group(
		      Item(name = 'Rcore', label='Core Radius (nm)'),Item(name = 'Dcore', label='Core Diameter(um)')
		      )

	TransGroup=Group(
			Item(name='Lregion', label='Length of Exposed Region (um)', enabled_when='Config==Transmission'), Item('N', style='readonly'), 
			Item('angles', style='readonly'),
			)

	traits_view=View(
		        Group(
        		    SharedGroup, RefGroup, TransGroup
       			     )
			)

	def _angle_stop_default(self): return self.theta_max
	def _Mode_default(self): return 'TM'
	def _Config_default(self): return 'Reflection'

	#@cached_property
	def _get_Rcore(self): return (1000.0 * self.Dcore)/2.0

	#@cached_property
	def _get_N(self): 
		N=empty( (len(self.angles)) )
		for i in range(len(self.angles)):
			if self.Config =='Reflection': 
					N[i]=int(1)  #Technically an int, but float works better for computations
			elif self.Config=='Transmission':
					N[i]=int(math.tan(self.to_rads(self.angles[i]) ) * self.Lregion/self.Dcore )
#					N[i]=(self.Dcore/(math.tan(self.to_rads(self.angles[i]) * self.Lregion)))
		return N

	#@cached_property
	def _get_theta_max(self): return round(self.to_degrees(math.asin(self.NA)),2)
	def _set_theta_max(self, theta): self.NA=round(math.sin(self.to_rads(theta)),2)
	
	def to_degrees(self, angle_in_rad):  return angle_in_rad* (180.0 / math.pi)
	
	def to_rads(self, angle_in_degrees): return angle_in_degrees*(math.pi / 180.0)   #Actually never used

	#@cached_property
	def _get_angle_samples(self):
		angle_samples=int( (self.angle_stop-self.angle_start)  / self.angle_inc ) 
		return angle_samples
	#@cached_property
	def _get_angles(self):
		angles=linspace(self.angle_start, self.angle_stop, num=self.angle_samples)
		if self.Config=='Reflection': return angles
		elif self.Config == 'Transmission':
			betas=abs(90.0-angles)
			return betas
	#@cached_property
	def _get_sa(self): return sin(self.to_rads(self.angles ))  #numpy.sin not math.sin

	#@cached_property
	def _get_ca(self): return cos(self.to_rads(self.angles ))

if __name__ == '__main__':
	SpecParms().configure_traits()
