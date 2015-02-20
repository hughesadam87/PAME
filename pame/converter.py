from traits.api import HasTraits, Float, Array, Property, Enum, Trait, CFloat, Constant, List
from traitsui.api import View, Item, Group, HSplit, VSplit
from numpy import linspace, array
from math import pi

class ConversionError(Exception):
    """ """

class SpectralConverter ( HasTraits ):

    h=float(6.626068*10**-34)  # m**2 kg / s
    eVtoJ=float(1.60217646 * 10**-19)  #Number of Joules in one Ev
    c=float(299792458)     #speed of light m/
    Units = Trait( 'Meters', { 'Meters':      1.0,
                               'Centimeters':.01,
                               'Micrometers':.000001,
                               'Nanometers': .000000001,       #DEFINE RELATIVE TO METERS
                               'eV': h*c/(eVtoJ),   #RECIPROCAL UNITS (THESE ARE INVERTED BELOW)
                               'cm-1': .01,
                               'Wavenumber(nm-1)':.000000001,  #WAVENUMBER IS INVERSE WAVELENGTH IN NM
                               'Frequency(Hz)':  c,  #SIMPLY INVERTED
                               'Angular Frequency(rad)': 2.0*pi*c
                               } )

    proportional=['Meters', 'Nanometers', 'Centimeters', 'Micrometers']  #proportional to distance
    reciprocal=['cm-1', 'eV', 'Wavenumber(nm-1)', 'Frequency(Hz)', 'Angular Frequency(rad)']                #Inverse to distance (aka energy is recicprocal E=hc/lam)s  

    input_array  = Array( )  #Set on initialization
    input_units  = Units( )  #Set on initialization
    output_array = Property(Array, depends_on = [ 'input_array', 'input_units',
                                                  'output_units' ])
    output_units  = Units( )  #Default unit

    valid_units=Property(List, depends_on='proportional, reciprocal')  #All valid units in the system

    xstart=Property(Float, depends_on='input_array')
    xend=Property(Float, depends_on='input_array')

    xnewstart=Property(Float, depends_on='output_array')
    xnewend=Property(Float, depends_on='output_array')

    traits_view=View(  
        VSplit(
            Group(HSplit( Item('xstart', label='Old Spectral Min', style='readonly'),
                          Item('xend', label='Old Spectral Max',style='readonly'),
                          Item('input_units' , style='simple', label='Input Units' ))  ),
            Group(HSplit( Item('xnewstart', label='New Spectral Min',style='readonly'),
                          Item('xnewend', label='New Spectral Max',style='readonly'),
                          Item('output_units', label='Output Units')  ),
                  )
            ),  kind='modal',buttons = [ 'Undo', 'OK', 'Cancel', 'Help' ], height=500, width=500, resizable=True)

    def _get_xstart(self): 
        return self.input_array[0]

    def _get_xend(self):  
        return self.input_array[-1]

    def _get_xnewstart(self):
        return self.output_array[0]

    def _get_xnewend(self): 
        return self.output_array[-1]

    def _get_valid_units(self): 
        return self.proportional+self.reciprocal
    
    def specific_array(self, new_unit): 
        """Return a unit-converted array without changing current settings"""
        if new_unit not in self.valid_units:
            raise ConversionError('Invalid spectral unit: %s' % new_unit)
    
        # Temporarily change outunit, send, return it back
        old_unit = self.output_units
        self.output_units = new_unit
        specificarray = self.output_array  #propety so not copied 
        self.output_units = old_unit
        return specificarray    
    
    # Property implementations
    def _get_output_array ( self ):
        if self.input_units in self.proportional and self.output_units in self.proportional:
            return (self.input_array * self.input_units_) / self.output_units_

        elif self.input_units in self.proportional and self.output_units in self.reciprocal:
            return 1.0/( (self.input_array * self.input_units_) / self.output_units_)

        elif self.input_units in self.reciprocal and self.output_units in self.proportional:
            return 1.0/( (self.input_array * self.output_units_) / self.input_units_)   #Output/input

        elif self.input_units in self.reciprocal and self.output_units in self.reciprocal:
            return  (self.input_array * self.output_units_) / self.input_units_

if __name__ == '__main__':
    x=linspace(400,555,100)
    f=SpectralConverter()
    f.input_array=x ; f.input_units='Nanometers'
    f.output_units='Micrometers'
    f.configure_traits()