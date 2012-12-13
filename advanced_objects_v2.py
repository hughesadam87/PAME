from traits.api import *
from traitsui.api import *
from material_models import basic_metal_model, DrudeBulk
from interfaces import IMie, IMaterial, IMixer, IStorage
from numpy import empty, array
import math, cmath
from composite_materials_v2 import SphericalInclusions_Disk #For inheritance

def free_path_correction():
    ''' Size correction for the reduced mean free path.  Cited in many papers, in fact I'm writing this from,
    "Determination of Size and concentratino of Gold Nanopariticles from UV-Vis Spectra; Haiss et al;however, 
    original paper seems to be Kreibig, U.; Vonfrags. C Z. Phys. 1969 224, 307'''

class NanoSphere(SphericalInclusions_Disk):
    '''Technically a nanosphere always needs a medium anyway, so make it composite object'''
    from mie_traits_v2 import sphere_full, sphere
    from material_models import Dispwater
    from material_files import NK_Delimited

    mat_name=Str('Bare Nanosphere')
    FullMie=Instance(IMie)  #Used to compute scattering properties	

    MediumMaterial=Instance(IMaterial)
    CoreMaterial=Instance(IMaterial)

    r_core=Float(12)

    d_core=Property(Float, depends_on='r_core')

    def _get_d_core(self): return 2.0*self.r_core
    def _set_d_core(self, d): self.r_core=d/2.0

    def __init__(self, *args, **kwds):
        super(NanoSphere, self).__init__(*args, **kwds)
        self.sync_trait('CoreMaterial', self, 'Material1')
        self.sync_trait('MediumMaterial', self, 'Material2')

        self.sync_trait('CoreMaterial', self.FullMie, 'CoreMaterial')
        self.sync_trait('MediumMaterial', self.FullMie, 'MediumMaterial')
        self.sync_trait('specparms', self.FullMie, 'specparms')
        self.sync_trait('r_core', self.FullMie, 'r_core')

    traits_view=View(	
        VGroup(			
            HGroup(
                Item('r_core'),Item('FullMie'),
                ),
            Group(	
                Group(
                    Item('selectmat1', label='Change Core Material'),
                    Item('CoreMaterial', style='custom'),  
                    label='Core Material'),
                Group(
                    Item('selectmat2', label='Change Medium Material'),
                    Item('MediumMaterial',style='custom'), 
                    label='Medium Material'),
                layout='tabbed',
                ),
            ),
    )


    def _FullMie_default(self): return self.sphere_full()			
    def _CoreMaterial_default(self):  ### Overwrite as package data eventually
        return self.NK_Delimited(thefile='./Optical_metal_data/Converted_Files/JC_Gold.txt')
    def _MediumMaterial_default(self): return self.Dispwater()#specparms=self.specparms)


######## DRUDE MODELS BELOW MAY BE DEPRECATES	

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

    def __init__(self, *args, **kwargs):
        super(DrudeNew, self).__init__(*args, **kwargs)


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
        self.CoreMaterial=self

class DrudeNP_corrected(DrudeBulk, NanoSphere):
    '''Corrects plasma frequency for free electron term; from Gupta 2'''

    valid_metals=Enum('gold','silver')  #Need fermi velocity for copper and aluminum
    apply_correction=Bool(True)

    def __init__(self, *args, **kwargs):
        super(DrudeNP_corrected, self).__init__(*args, **kwargs)

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

        self.CoreMaterial=self

    traits_view=View(Item('r_core'), Item('valid_metals'),
                     Item('lam_plasma', style='readonly'), Item('lam_collis', style='readonly'),Item('mviewbutton'), Item('apply_correction', label='Free Path Correction'),
                     Item('FullMie')
                     )

class NanoSphereShell(NanoSphere):
    '''This is a single object, but it inherits from composite material to allow for trait changes and stuff to be understood'''		
    from mie_traits_v2 import sphere_shell
    from composite_materials_v2 import CompositeMaterial_Equiv, SphericalInclusions_Shell
    from composite_plots import DoubleSview
    from material_models import Constant

    ###Note: CoreMaterial refers to the core/shell composite object that is the "NanoSphere" for this instance ###


    ShellMaterial=Instance(IMaterial)    #Composite Shell	
    CoreShellComposite=Instance(IMaterial)
    TotalMix=Instance(IMaterial)   #TotalMix is used to mix the composite sphere/shell and medium 
                    #Neceassary because Mix() already defined such that Corematerial is already sync'd to solute
                    #TotalMix syncs CompositeCore to solutematerial.  Solution not ideal

    doublescattview=Instance(DoubleSview)

    earray=DelegatesTo('TotalMix')
    Vfrac=DelegatesTo('TotalMix')

    ## selected_material.ShellMaterial.Vfrac is shell trait

    CompositeMie=Instance(IMie)  #This will store optical properties of the composite scattering cross section

    r_shell=Float(2)	

    d_shell=Property(Float, depends_on='r_shell')

    def _get_d_shell(self): return 2.0*self.r_shell
    def _set_d_shell(self, d): self.r_shell=d/2.0    

    opticalgroup=Group(
        Tabbed(
            Item('FullMie', editor=InstanceEditor(), style='custom', label='Full Shell Particle', show_label=False, ),
            Group( 
                Item('CompositeMie', editor=InstanceEditor(), style='custom', label='Mixed Mie Particle', show_label=False), 	
                #				Item('CompositeMixStyle', style='custom', show_label=False),
                #				Item('CompositeMix', style='custom', show_label=False),				     
                label='Composite Shell/core')
            ),
        label='Optical Properties')

    coregroup=Group(
        Item('CoreMaterial', style='custom', show_label=False), 
        Item('selectmat1', label='Choose Core Material', show_label=False) , label='Core Material',
    )

    mediumgroup=Group(	
        Item('MediumMaterial', editor=InstanceEditor(),style='custom', show_label=False),
        Item('selectmat2', label='Choose Medium Material', show_label=False) , label='Medium Material', 
    )

    compnpgroup=Group(
        HGroup(            
            Item('d_core', label='NP Core diameter'), Item('d_shell', label='NP Shell diameter'),
            Item('r_core', label='NP Core radius'), Item('r_shell', label='NP Shell radius'), 
            #Item('specparms', style='custom'), 
            Item('mviewbutton', label='Show Full material', show_label=False)),
        Group(
            Tabbed(
                Include('coregroup'),
                Include('mediumgroup'),
                Item('ShellMaterial', editor=InstanceEditor(),style='custom', label='Shell Material', show_label=False),
                Include('opticalgroup'),
                Item('CoreShellComposite', style='custom', label='CoreShellComposite Mix', show_label=False),
                Item('TotalMix', style='custom', label='Surface Coverage', show_label=False),
                label='Constituent Materials and Optical Properties' ), 
            ),

    )


    traits_view=View(Item('doublescattview', label='Cross Section Mixing'),#Item('allbutt', label='Plot Comparison'),
                     Include('compnpgroup'), title='Composite Nanoparticle with Shell', resizable=True )

    def __init__(self, *args, **kwds):
        super(NanoSphereShell, self).__init__(*args, **kwds)
        ## sync syntx ('Trait name here', Object to sync with, 'trait name there'##
        self.sync_trait('r_shell', self.ShellMaterial, 'r_particle')
        self.sync_trait('r_core', self.ShellMaterial, 'r_platform')
        self.sync_trait('MediumMaterial', self.ShellMaterial, 'Material2')

        self.sync_trait('specparms', self.CoreShellComposite, 'specparms')
        self.sync_trait('CoreMaterial', self.CoreShellComposite, 'Material1')
        self.sync_trait('ShellMaterial', self.CoreShellComposite, 'Material2')
        self.sync_trait('r_core', self.CoreShellComposite, 'r_particle')
        self.sync_trait('r_shell', self.CoreShellComposite, 'r_shell')

        self.sync_trait('CoreShellComposite', self.TotalMix, 'Material1')
        self.sync_trait('MediumMaterial', self.TotalMix, 'Material2')
        self.sync_trait('r_core', self.TotalMix, 'r_particle', mutual=False)

        self.sync_trait('r_shell', self.CompositeMie, 'r_shell', mutual=False)  #So I can play with it
        self.sync_trait('r_core', self.CompositeMie, 'r_core', mutual=False)
        self.sync_trait('specparms', self.CompositeMie, 'specparms')
        self.sync_trait('CoreShellComposite', self.CompositeMie, 'CoreMaterial') 
        self.sync_trait('MediumMaterial', self.CompositeMie, 'MediumMaterial')

        self.sync_trait('ShellMaterial', self.FullMie, 'ShellMaterial')
        self.sync_trait('r_shell', self.FullMie, 'r_shell')

#	def _ShellMaterial_default(self): return self.SphericalInclusions_Shell()
    def _ShellMaterial_default(self): return self.Constant(constant_index=1.4330)  #NOTE THIS DOESN'T AUTOMATICALLY TRIGGER UDPATES!!
    def _CoreShellComposite_default(self): return self.CompositeMaterial_Equiv()
    def _TotalMix_default(self): return SphericalInclusions_Disk()   
    def _FullMie_default(self): return self.sphere_shell()
    def _CompositeMie_default(self): return self.sphere_full()
    def _mat_name_default(self): return str('Composite NP:  ')+str(self.Material1.mat_name)+' IN '+str(self.Material2.mat_name)

    def _doublescattview_default(self): return self.DoubleSview(scatt1=self.FullMie.sview, scatt2=self.CompositeMie.sview)

#	def update_allplots(self): 
#		''' I replaced this with doublescattview anyway'''
#		self.allplots={'full':self.FullMie.sview, 'comp':self.CompositeMie.sview}

    def get_usefultraits(self):
        ''' Method to return dictionary of traits that may be useful as output for paramters and or this and that'''
        ### Eventually, make complex materials liked mixed shell call down levels of this.  aka self.shellmaterial.get_usefultraits()
        return {'Core Material':self.CoreMaterial.mat_name, 'Shell Inclusion':self.ShellMaterial.mat_name,
                'Medium Material':self.MediumMaterial.mat_name, 'Core Diameter':self.d_core, 'Shell Thickness':self.d_shell}


if __name__ == '__main__':
#	NanoSphereShell().configure_traits()
    NanoSphere().configure_traits()