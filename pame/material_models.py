from basic_material import BasicMaterial
from traits.api import *
from traitsui.api import *
from numpy import array, sqrt, empty

class ABCMaterialModel(BasicMaterial):	
    def __init__(self, *args, **kwargs):
        super(ABCMaterialModel, self).__init__(*args, **kwargs)

    source='Model'
        

class Constant(ABCMaterialModel):
    from numpy.lib import scimath as SM
    constant_dielectric=Complex() 
    constant_index=Property(Complex,
                            depends_on='constant_dielectric')

    def _constant_dielectric_changed(self):
        self.update_data()

    def _constant_dielectric_default(self):
        return complex(1.804535, 0.0)

    def _get_constant_index(self): 
        return self.SM.sqrt(self.constant_dielectric)

    def _set_constant_index(self, constant): 
        nr=constant.real
        nk=constant.imag          #NEED TO VERIFY THESE WORK SEE PLOT VS OLD VALUES
        er = nr**2 -nk**2 
        ei = 2.0*nr*nk
        self.constant_dielectric=complex(er, ei)

    def _mat_name_default(self): 
        return  'Constant Material Array: No Dispersion'

    def update_data(self): 
        self.earray[:]=self.constant_dielectric
        
        
    def simulation_requested(self):
        out = super(Constant, self).simulation_requested()
        out['e_constant'] = self.constant_dielectric
        out['n_constant'] = self.constant_index
        return out


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

class Cauchy(ABCMaterialModel):
    """ """
    mat_name = Str('Fused Silica')
    model_id = Str('cauchy') #Waht are model id's for?
    
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
        um = self.specparms.specific_array('Micrometers')  #<---
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
    model_id=Str('sellmeir')   

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
        um_xarray = self.specparms.specific_array('Micrometers')
        l_sqr = um_xarray**2
        f1=(self.a1*l_sqr) / (l_sqr - self.b1**2)
        f2=(self.a2*l_sqr) / (l_sqr - self.b2**2)       #Dummy indicies
        f3=(self.a3*l_sqr) / (l_sqr - self.b3**2)  
        self.narray = sqrt(1.0 + f1 + f2 + f3)	


class Dispwater(ABCMaterialModel):
    '''Returns dispersion of water as put in some paper'''
    A=Float(3479.0) 
    B=Float(5.111 * 10**7)  #WHAT UNITS
    model_id=Str('Dispwater')   

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
    '''Taken from another gupta paper to test form.  I think this is valid for a metal sheet, not np's'''

    model_id=Str('DrudeBulk')   # What is the point of this?  Have class name... delete, or put in ABCMaterial???

    valid_metals=Enum('gold','silver','aluminum','copper')  #Currently only 

    traits_view=View(
        Item('valid_metals'), 
        Item('mat_name', label='Custom Name'),
        Item('lam_plasma', style='readonly'),
        Item('lam_collis', style='readonly'),
        Item('mviewbutton'), 
        Item('x_unit')
    )

    def __init__(self, *args, **kwargs):
        super(DrudeBulk, self).__init__(*args, **kwargs)

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
        m_xarray=self.specparms.specific_array('Meters')
        unity=array([complex(0.0,1.0)], dtype=complex)  #Gupta requries i * lambda, so this gets complex value of the xarray
        self.earray = 1.0 - ( (m_xarray**2 * self.lam_collis) / (self.lam_plasma**2 * ( self.lam_collis + m_xarray*unity)  ) )

if __name__ == '__main__':
    Constant().configure_traits()
