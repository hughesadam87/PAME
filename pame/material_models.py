from basic_material import BasicMaterial
from traits.api import *
from traitsui.api import *
import numpy as np
from utils import complex_e_to_n

class ABCMaterialModel(BasicMaterial):	
    source='Model'
        
class Constant(ABCMaterialModel):
    """ Interpolated array from scalaer complex value N or E """
    constant_dielectric = Complex() 
    constant_index=Property(Complex,
                            depends_on='constant_dielectric')

    traits_view=View (
        VGroup(
            Include('basic_group'),
            HGroup(
                Item('constant_dielectric', label='Dielectric Constant'),
                Item('constant_index', label='Index of Refraction'),
                ),
            ),
        resizable=True, width=.5, height=.2,
    )

    def _constant_dielectric_changed(self):
        self.update_data()

    def _constant_dielectric_default(self):
        return complex(1.804535, 0.0)

    def _get_constant_index(self): 
        return complex_e_to_n(self.constant_dielectric)

    # This isn't same as complex_n_to_e, don't change
    def _set_constant_index(self, constant): 
        nr=constant.real
        nk=constant.imag          
        er = nr**2 -nk**2 
        ei = 2.0*nr*nk
        self.constant_dielectric=complex(er, ei)

    def _mat_name_default(self): 
        return  'Constant Material Array: No Dispersion'

    def update_data(self): 
        earray = np.empty(len(self.lambdas), dtype='complex')
        earray.fill(self.constant_dielectric)
        self.earray = earray
               
    def simulation_requested(self):
        out = super(Constant, self).simulation_requested()
        out['e_constant'] = self.constant_dielectric
        out['n_constant'] = self.constant_index
        return out


class Air(Constant):
    """ Constant material of n=1.0; no dipsersion
    """
    def _constant_dielectric_default(self):
        return complex(1.0, 0)
    
    def _mat_name_default(self): 
        return  'Air (n=1.0)'    
    
    traits_view=View (
        VGroup(
            Include('basic_group'),
            HGroup(
                Item('constant_dielectric', 
                     label='Dielectric Constant',
                     style='readonly'),
                Item('constant_index', 
                     label='Index of Refraction',
                     style='readonly'),
                ),
            ),
        resizable=True, width=.5, height=.2,
    )   

class Cauchy(ABCMaterialModel):
    """ """
    mat_name = Str('Fused Silica')
    
    A = Float(1.4580)
    B = Float(0.00354)
    C = Float(0.0)
    D = Float(0.0)
    
    cauchy_group=VGroup(HGroup(Item('A'), 
                               Item('B'),
                               Item('C'), 
                               Item('D'))) 
    
    traits_view=View (
        VGroup( Include('basic_group'), 
                Include('cauchy_group') 
                ),
        resizable=True
    )        
    
    @on_trait_change('A, B, C, D')
    def update_model(self):
        """ Update data and view.  For trait_change decorator, need to use a new
        method so I arbirarily named this "update_model()".
        """
        self.update_data()


    def update_data(self):		
        um = self.specparms.conv.specific_array('Micrometers')  #<---
        A,B,C,D = self.A, self.B, self.C, self.D
        self.narray = self.A + self.B/um**2 + C/um**3 + D/um**4       
        
    def simulation_requested(self):
        out = super(Cauchy, self).simulation_requested()
        for attr in ['A','B','C','D']:
            out[attr] = getattr(self, attr)
        return out        

    

class Sellmeir(ABCMaterialModel):
    """Returns sellmeir dispersion of glass.  Valid between 210-2200nm 
    according to:
    
    Sharma, Gupta.
    "On the performance of different bimetallic combinations in surface plasmon 
    resonance based fiber optic sensors."  J. APpl. Phys. 101, 092111 (2007)
    """
    mat_name=Str('Dispersive Glass')

    a1=Float(.6961663) 
    a3=Float(.8974794) 
    a2=Float(.4079426)
    b1=Float(.0684043) 
    b3=Float( 9.896161) 
    b2=Float(.1162414)		

    sellmeir_group=VGroup(HGroup(Item('a1'), Item('a2'), Item('a3')),
                          HGroup(Item('b1'), Item('b2'), Item('b3'))) 

    traits_view=View (
        VGroup( Include('basic_group'), Include('sellmeir_group') ),
        resizable=True
    )

    def simulation_requested(self):
        out = super(Sellmeir, self).simulation_requested()       
        for attr in ['a1','a2','a3','b1','b2','b3']:
            out[attr] = getattr(self, attr)       
        return out
           

    @on_trait_change('a1, b1, a2, b2, a3, b3')
    def update_model(self):
        """ Update data and view.  For trait_change decorator, need to use a new
        method so I arbirarily named this "update_model()".
        """
        self.update_data()

    def update_data(self):		
        um_xarray = self.specparms.conv.specific_array('Micrometers')
        l_sqr = um_xarray**2
        f1=(self.a1*l_sqr) / (l_sqr - self.b1**2)
        f2=(self.a2*l_sqr) / (l_sqr - self.b2**2)       #Dummy indicies
        f3=(self.a3*l_sqr) / (l_sqr - self.b3**2)  
        self.narray = np.sqrt(1.0 + f1 + f2 + f3)	


class Dispwater(ABCMaterialModel):
    """Returns dispersion of water as put in some paper"""
    A=Float(3479.0) 
    B=Float(5.111 * 10**7)  # I Believe units of NM

    def _mat_name_default(self): 
        return 'Dispersive Water'	
    
    def update_data(self): 	
        self.narray=1.32334 + (self.A/ self.lambdas**2 ) - (self.B/self.lambdas**4)   #Entry in nm

    @on_trait_change('A, B')
    def update_model(self):
        """ Update data and plot on any of these attributes chaning. """
        self.update_data()

    traits_view=View (
        Group(Include('basic_group'),
              HGroup(Item('A', style='simple'),
                     Item('B', style='simple')
                     )
              ),		
        resizable=True
    )


class Metals_plasma(HasTraits):
    """ ???? """
    
    metals_dic= DictStrList()
    name=Str()
    lam_plasma=Float()
    lam_collis=Float()
    keys=Any
    
    def __init__(self, *args, **kwds):
        super(Metals_plasma, self).__init__(*args, **kwds)
        self.metals_dic.key_trait = self.name
        self.metals_dic.value_trait = [self.lam_plasma, self.lam_collis]
        self.metals_dic['gold']=[1.6726 *10**-7, 8.9342 * 10**-6]
        self.name='gold'
        self.lam_plasma=self.metals_dic[self.name][0]	
        self.lam_collis=self.metals_dic[self.name][1]
        self.keys=(self.metals_dic.keys())     #WHAT IS THE TRAIT EQUIVALENT OF THIS?


class ABCMetalModel(ABCMaterialModel):
    lam_plasma=Float()   #Plasma frequency
    lam_collis=Float()   #Collision frequency
    freq_plasma=Float()
    freq_collis=Float()

    def _lam_plasma_changed(self): 
        self.update_data()           
        
    def update_data(self): 
        pass

    #SET FREQENCY/WAVELENGTH TO BE RECIPROCAL OF EACH OTHER LIKE N/E WITH FREQUENCY BEING CANONICAL REPRESENTATION

class DrudeBulk(ABCMetalModel):
    """ Sharma Gupta 2007 On the performance of different bimetallic combinations\
    in surface plasmon resonance based fiber optic sensors.  Journ. of app. physics.
    101 093111 (2007)
    """
    valid_metals = Enum('gold','silver','aluminum','copper')  #Currently only 

    def _valid_metals_default(self): 
        return 'gold'      #NEED TO MAKE METALS DIC THEN DEFAULT TO THAT 
    
    def _lam_plasma_default(self): 
        return 1.6826 * 10**-7

    def _lam_collis_default(self): 
        return 8.9342 * 10**-6

    def _mat_name_default(self): 
        return 'Drude Metal'

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
        self.update_data()	


    def update_data(self):   #THIS DOES FIRE AT INSTANTIATION
        m_xarray = self.specparms.conv.specific_array('Meters')
        unity = 0+1j#np.array([complex(0.0,1.0)], dtype=complex)  #Gupta requries i * lambda, so this gets complex value of the xarray
        self.earray = 1.0 - ( (m_xarray**2 * self.lam_collis) / (self.lam_plasma**2 * ( self.lam_collis + m_xarray*unity)  ) )

    traits_view=View(
        VGroup(
            HGroup(
            Include('basic_group'),            
            Item('valid_metals', show_label=False, label='Choose Metal'), 
            ),
            Item('lam_plasma', label='plasma wavelength(m)', style='readonly'),
            Item('lam_collis', label='collision wavelength(m)', style='readonly'),
              )
        )


if __name__ == '__main__':
    DrudeBulk().configure_traits()
