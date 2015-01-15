from __future__ import division

from traits.api import *
from traitsui.api import *
from converter import SpectralConverter
from numpy import linspace, sin, cos, empty, argsort
import numpy as np

# PAME imports
import config

class SpecParms(HasTraits):
    '''Global class which defines variables and methods shared by all other class methods''' 

    conv=Instance(SpectralConverter)  
    valid_units = DelegatesTo('conv')
    x_unit = Enum(values='valid_units')   #THIS IS HOW YOU DEFER A LIST OF VALUES TO ENUM

    lambdas=Array

    x_samples=Property(Int, depends_on=['lambdas'])
    xstart=Property(Float, depends_on=['lambdas'])
    xend=Property(Float, depends_on=['lambdas'])
    x_increment=Property(Float, depends_on=['x_samples', 'xstart', 'xend'])


    traits_view = View(
        VGroup(
            HGroup(  Item(name = 'xstart'),  
                     Item(name = 'xend'),
                     Item(name ='x_samples'),
                     Item(name = 'x_increment', style='readonly')
                     ),
            
            HGroup(  Item(name='x_unit', style='readonly'), 
                     Item(name='x_unit', style='simple', label='Change Units' ) 
                   ), #    label='Spectral Parameters'
             )
        )

    def state_requested(self):
        ''' Method to return dictionary of traits that may be useful as output for paramters and or this and that'''
        ### trait_get is shortcut to return dic if the keys are adequate descriptors for output
        return self.trait_get('x_start',
                              'x_end', 
                              'x_increment', 
                              'x_samples')

    def _conv_default(self): 
        return SpectralConverter(input_array=self.lambdas, input_units='Nanometers')
    
    def _lambdas_default(self): 
        return linspace(config.xstart,config.xend,config.xpoints)

    def _x_unit_default(self): 
        return config.xunit

    def _valid_units_default(self): 
        return self.conv.valid_units

    #@cached_property
    def _get_x_samples(self): 
        return self.lambdas.shape[0]

    def _set_x_samples(self, samples):
        self.lambdas= np.linspace(self.xstart, self.xend, num=samples)

    #@cached_property
    def _get_x_increment(self):  
        return round(abs(self.xstart - self.xend) / self.x_samples, 4)

    def _x_unit_changed(self):
        self.conv.output_units=self.x_unit     #INPUT ALWAYS KEPT AT NANOMETERS, THIS IS IMPORTANT DONT EDIT
        self.lambdas = self.conv.output_array

    #@cached_property
    def _get_xstart(self): 
        return self.lambdas[0]

    #@cached_property
    def _get_xend(self):  
        return self.lambdas[-1]

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
    Config=Enum('Axial', 'Transversal')

    # Don't change these or BasicReflectance.update_R will get mad
    Mode=Enum('S-polarized', 'P-polarized', 'Unpolarized')
    Lregion=Float(1500) #um or cm
    Dcore=Float(62.5)  #um
    Rcore=Property(Float, depends_on=['Dcore'])

    angle_start = Float(.5)
    angle_stop = Float()
    angle_inc = Float(.5)
    angle_avg = Enum('Equal', 'Gupta') #Why not in fiberparms
    

    ### Used to compute hypothetical max angle capacity, but are not actually used in iteration over angle start-stop
    NA=Float(.275)
    critical_angle=Property(Float, depends_on=['NA'])  #Critical angle

    angle_samples=Property(Int, depends_on=['angle_start', 'angle_stop', 'angle_inc'])
    angles = Property(Array, depends_on=['angle_samples, Config']) 
    angles_radians = Property(Array, depends_on=['angles'])

    N=Property(Array, depends_on=['Config', 'angles', 'Lregion', 'Dcore'])  #NUMBER OF REFLECTIONS

    
    def simulation_requested(self):
        ''' Method to return dictionary of traits that may be useful as output for paramters and or this and that'''
        traitdic={'Optical Configuration':self.Config, 
                  'Mode':self.Mode, 
                  'Core Diameter':self.Dcore, 
                  'Numerical Aperature':self.NA, 
                  'Critical Angle':self.critical_angle, 
                  'Angle Min':self.angle_start, 
                  'Angle Max':self.angle_stop,
                  'Angle Inc.':self.angle_inc}

        if self.Config=='Transversal':
            l=self.Lregion
        else:
            l='N/A'
        traitdic.update({'Strip Region':l})
        return traitdic


    # VIEW
    # -------------

    SharedGroup =Group(
        HGroup(
            Item('Config'), Item('Mode')
            ),
        HGroup(
            Item(name='NA', label='Numerical Aperature'), 
            Item('critical_angle', label='Critical Angle')
            ),
        HGroup(
            Item('angle_avg', label='Averaging'),
            Item('angle_start', label='Angle Start'), 
            Item('angle_stop', label='Angle End'), 
            Item('angle_inc', label='Angle Increment'),
            ),
        show_border = True, #group border
    )

    RefGroup=HGroup(
        Item(name = 'Rcore', label='Core Radius (nm)'),
        Item(name = 'Dcore', label='Core Diameter(um)')
    )

    TransGroup=Group(
        Item(name='Lregion', label='Length of Exposed Region (um)',
             enabled_when='Config==Transversal'), 
        Item('N', style='readonly'), 
        Item('angles', style='readonly'),
    )

    traits_view=View(
        Group(SharedGroup, RefGroup, TransGroup)
    )

    def _angle_stop_default(self): 
        return self.critical_angle
    
    def _Mode_default(self): 
        return 'S-polarized'

    def _Config_default(self): 
        return 'Axial'

    #@cached_property
    def _get_Rcore(self): return (1000.0 * self.Dcore)/2.0

    #@cached_property
    def _get_N(self): 
        """ Number of reflectations for each mode in the fiber if the ray can bounce indefinitely """
        N=empty( (len(self.angles)) )

        if self.Config == 'Axial':
            return N.fill(1) #One reflection per mode
        
        elif self.Config == 'Transversal':
            return np.tan(self.angles_radians * (self.Lregion / self.Dcore))


    #@cached_property
    def _get_critical_angle(self): 
        return round(np.degrees(np.arcsin(self.NA)),2)
    
    def _set_critical_angle(self, theta): 
        self.NA=round(np.sin(np.radians(theta)),2)

    #@cached_property
    def _get_angle_samples(self):
        return round ((self.angle_stop-self.angle_start)  / self.angle_inc) 

    #@cached_property
    def _get_angles(self):
        angles=linspace(self.angle_start, self.angle_stop, num=self.angle_samples)

        if self.Config=='Axial': 
            return angles
        
        # betas?
        elif self.Config == 'Transversal':
            betas=abs(90.0-angles)
            return betas

    def _get_angles_radians(self):
        return np.radians(self.angles)


if __name__ == '__main__':
    SpecParms().configure_traits()