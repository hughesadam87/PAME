from __future__ import division

from traits.api import *
from traitsui.api import *
from converter import SpectralConverter
from numpy import linspace, sin, cos, empty, argsort
import numpy as np

# PAME imports
import config

class SpectralError(Exception):
    """ """

class SpecParms(HasTraits):
    """ Creates spectral array from xstart, xend, xsamples and xunit.
    Internally, pame uses nm as a the primary spectral unit for numerical
    stability and consistency in calculations across components of the software.
    """
    
    conv=Instance(SpectralConverter)  
    valid_units = DelegatesTo('conv')
    x_unit = Enum(values='valid_units')   #THIS IS HOW YOU DEFER A LIST OF VALUES TO ENUM

    # Lambdas is the interally stored nanometers array
    # Working lambdas is in current x-unit (used in plotting even when
    # nanometers array is not changed)
    working_lambdas = Array
    working_x_unit = Str("Nanometers")
    lambdas = Array
    update = Button
    
    x_samples=Int(config.xpoints)
    #x_samples=Property(Int, depends_on=['_lambdas'])
    xstart = Float(config.xstart)#Property(Float, depends_on=['_lambdas'])
    xend = Float(config.xend)#Property(Float, depends_on=['_lambdas'])
    x_increment = Property(Float, depends_on=['x_samples', 'xstart', 'xend'])

    traits_view = View(
        VGroup(          
            HGroup(  
                     Item('update', label='Update Spectra', show_label=False),                 
                     Item(name='x_unit', style='simple', label='Spectral Unit'),
                     Item(name = 'x_increment', style='readonly'),                     
                   ), #    label='Spectral Parameters'
            HGroup(  Item(name = 'xstart'),  
                     Item(name = 'xend'),
                     Item(name ='x_samples'),
                     ),
             )
        )

    def _conv_default(self): 
        """ Starts with nanometer inputs and outputs"""
        return SpectralConverter(input_array=self.lambdas, 
                                 input_units='Nanometers',
                                 output_units='Nanometers', #<-- DO NOT CHANGE
                                 )         
    
    def _lambdas_default(self): 
        return linspace(config.xstart,
                        config.xend,
                        config.xpoints)
    
    def _working_lambdas_default(self):
        return np.copy(self.lambdas)
    

    def _update_fired(self):
        """ Set self.lambdas to self._lambdas.  If user didn't change anything,
        doesn't trigger a superfluous redraw.  If user changes sample size,
        then shapes change and can't do "allclose"
        """
        # Set the input array to user's new units (kind of roundabout)
        # and return the nanometers array as output units
        self.conv.input_array = np.linspace(self.xstart, 
                                            self.xend,
                                            self.x_samples)
        out = self.conv.specific_array('Nanometers')
        # Outunit still fixed to nanometers
        if not np.allclose(self.lambdas, out):
            self.lambdas = out
            
        # Trigger an update anytime update fires, even if doesn't change
        # self.lambdas so that plots can redraw their axis
        self.working_x_unit = self.conv.input_units #MUST COME BEFORE WORKIGN_LAMBDAS
        self.working_lambdas = np.copy(self.conv.input_array)
        
    def _x_unit_default(self): 
        return 'Nanometers'

    def _valid_units_default(self): 
        return self.conv.valid_units

    def _get_x_increment(self):  
        return  abs(self.xstart - self.xend) / self.x_samples

    def _x_unit_changed(self):
        """ Get new array, set xstart, xend form it and all will sync up."""
        oldarray = self.conv.specific_array(self.x_unit)
        
        self.conv.input_units = self.x_unit   
        self.conv.input_array = np.linspace(oldarray[0], 
                                            oldarray[-1],
                                            self.x_samples)        
        self.xstart = oldarray[0]
        self.xend = oldarray[-1]

    def _xstart_changed(self):
        self.conv.input_array = np.linspace(self.xstart, 
                                            self.xend,
                                            self.x_samples)         

    def _xend_changed(self):
        self.conv.input_array = np.linspace(self.xstart, 
                                            self.xend,
                                            self.x_samples) 

    def simulation_requested(self):
        ''' Method to return dictionary of traits that may be useful as 
        output for paramters and or this and that
        '''
        ### trait_get is shortcut to return dic if the keys are adequate descriptors for output
        return {'lambdas':self.working_lambdas, #<-- Unit user is working in 
                'xstart':self.xstart,
                'xend':self.xend,
                'x_increment':self.x_increment,
                'x_samples':self.x_samples,
                'x_unit':self.x_unit
                }


class AngleParms(HasTraits):
    """ ABC class for Ellipsometry, Optical fibers.  Essentially stores a series of angles
    and Modes used on reflectance computations.
    """

    Mode = Enum('S-polarized',
               'P-polarized',
               'Unpolarized')
    
    angle_start = Float(0)
    angle_stop = Float(45)
    angle_inc = Float(5)
    angle_avg = Str('Equal')
    
    angle_samples=Property(Int, depends_on=['angle_start', 'angle_stop', 'angle_inc'])
    angles = Property(Array, depends_on=['angle_samples, Config']) 
    angles_radians = Property(Array, depends_on=['angles'])
    _angle_sumstring = Property(Str, depends_on='angles')
    
    def _get__angle_sumstring(self):
        """ Summary of angles for nicer output"""
        return 'Angles=%s' % str(len(self.angles))

    #@cached_property
    def _get_angles(self):
        return linspace(self.angle_start, self.angle_stop, num=self.angle_samples)

    def _get_angles_radians(self):
        return np.radians(self.angles)
    
    #@cached_property
    def _get_angle_samples(self):
        return round ((self.angle_stop-self.angle_start)  / self.angle_inc)     
    
    

class EllipsometryParms(AngleParms):
    """ Unpolarized light and a range of angles for ellipsometry.
    """
    Mode = Str('Unpolarized') #<-- Fixed because need RS, RP
    _mode_message = Str('[required for ellipsometry]')
    
    traits_view = View(
        VGroup(
            HGroup(           
                   Item('_angle_sumstring', style='readonly', show_label=False),            
                   Item('Mode', style='readonly'),
                   Item('_mode_message', style='readonly', show_label=False)
                   ),
            HGroup(
                    Item('angle_start', label='Angle Start'), 
                    Item('angle_stop', label='End'),
                    Item('angle_inc', label='Increment')                    
                    ),
       )
    )

class FiberParms(AngleParms):
    """ Optical fiber of Transversal or Axial configuration of layers."""

    angle_start = Float(0.5)
    angle_inc = Float(0.5)    
    
    Config=Enum(['Axial', 'Transversal'])

    # Don't change these or BasicReflectance.update_R will get mad
    Mode=Enum('S-polarized', 'P-polarized', 'Unpolarized')
    Lregion=Float(1500) #um or cm
    Dcore=Float(62.5)  #um
    Rcore=Property(Float, depends_on=['Dcore'])

    #angle_start = Float(.5)
    #angle_stop = Float()
    #angle_inc = Float(.5)
    angle_avg = Enum('Equal', 'Gupta') #Why not in fiberparms    

    # Hypothetical max angle capacity, but are not actually used in iteration over angle start-stop
    NA=Float(.275)
    critical_angle=Property(Float, depends_on=['NA'])  #Critical angle

#    angle_samples=Property(Int, depends_on=['angle_start', 'angle_stop', 'angle_inc'])
#    angles = Property(Array, depends_on=['angle_samples, Config']) 
#    angles_radians = Property(Array, depends_on=['angles'])
#    _angle_sumstring = Property(Str, depends_on='angles')


    N=Property(Array, depends_on=['Config', 'angles', 'Lregion', 'Dcore'])  #NUMBER OF REFLECTIONS

    # VIEW
    # -------------

    traits_view = \
      View(
        VGroup(
        HGroup(
            Item('Config'), 
            Item('Mode'), 
            Item('angle_avg', label='Angle Averaging'),            
            Item(name='NA', label='Numerical Aperature'), 
            Item('critical_angle', label='Critical Angle')         
            ),
        HGroup(
            Item('angle_start', label='Angle Start'), 
            Item('angle_stop', label='End'), 
            Item('angle_inc', label='Increment'),
            Item('_angle_sumstring', 
                 style='readonly', 
                 show_label=False)            
            ),    

        HGroup(
            Item(name = 'Rcore', label='Core Radius (nm)'),
            Item(name = 'Dcore', label='Core Diameter(um)'),
            Item(name='Lregion',
                 label='Length of Exposed Region (um)',
                 visible_when='Config=="Transversal"'),  #<-- NEED INNER QUOTES       
                )
        ))
                
    def _Mode_default(self): 
        return 'S-polarized'

    def _Config_default(self): 
        return 'Axial'

    def _angle_stop_default(self): 
        return self.critical_angle

    #@cached_property
    def _get_angles(self):
        angles=linspace(self.angle_start, self.angle_stop, num=self.angle_samples)

        if self.Config=='Axial': 
            return angles
        
        # betas?
        elif self.Config == 'Transversal':
            betas=abs(90.0-angles)
            return betas


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


#GLOBALS
# BAD PRACTICE< BUT SHARED_SPECPARMS IS BASICALLY A GLOBAL SO NEED AN INSTANCE READY
# TO GO FOR SHARING
SHARED_SPECPARMS = SpecParms()

if __name__ == '__main__':
    SpecParms().configure_traits()