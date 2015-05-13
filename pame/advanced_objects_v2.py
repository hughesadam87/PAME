from traits.api import *
from traitsui.api import *
from material_models import ABCMetalModel, DrudeBulk
from interfaces import IMie, IMaterial, IMixer, IStorage
from numpy import empty, array
import os.path as op
import math, cmath
from mie_traits_v2 import bare_sphere, effective_sphere
from material_models import Dispwater #<--- Used by double nanoparticle
from composite_materials_v2 import SphericalInclusions_Disk, DoubleComposite #For inheritance

from pame import XNK_dir
from material_files import XNKFile

def free_path_correction():
    ''' Size correction for the reduced mean free path.  Cited in many papers, in fact I'm writing this from,
    "Determination of Size and concentratino of Gold Nanopariticles from UV-Vis Spectra; Haiss et al;however, 
    original paper seems to be Kreibig, U.; Vonfrags. C Z. Phys. 1969 224, 307'''

class NanoSphere(SphericalInclusions_Disk):
    '''Technically a nanosphere always needs a medium anyway, so make it composite object'''
    from material_models import Dispwater

    mat_name = Str('Bare Nanosphere') #<-- Only used if auto name disabled
    FullMie = Instance(IMie)  #Used to compute scattering properties	

    MediumMaterial = Instance(IMaterial)
    CoreMaterial = Instance(IMaterial)

    r_core = Float(12)
    d_core = Property(Float,
                      depends_on='r_core')

    def _get_d_core(self): 
        return 2.0*self.r_core

    def _set_d_core(self, d): 
        self.r_core=d/2.0

    def __init__(self, *args, **kwds):
        super(NanoSphere, self).__init__(*args, **kwds)
        self.sync_trait('CoreMaterial', self, 'Material1')
        self.sync_trait('MediumMaterial', self, 'Material2')

        self.sync_trait('CoreMaterial', self.FullMie, 'CoreMaterial')
        self.sync_trait('MediumMaterial', self.FullMie, 'MediumMaterial')
        self.sync_trait('r_core', self.FullMie, 'r_core')

    traits_view=View(	
        VGroup(			
            HGroup(
                Item('r_core'),Item('FullMie'),
                ),
            Group(	
                Group(
                    Item('selectmat1', label='Change Core Material', show_label=False),
                    Item('CoreMaterial', style='custom', show_label=False),  
                    label='Core Material'),
                Group(
                    Item('selectmat2', label='Change Medium Material'),
                    Item('MediumMaterial',style='custom'), 
                    label='Medium Material'),
                Group(
                    Item('Mix', label='Mixture Coverage')
                    ),
                layout='tabbed',
                ),
            ),
       )


    def _FullMie_default(self): 
        return bare_sphere()			

    def _CoreMaterial_default(self):  # Overwrite as package data eventually
        return XNKFile(file_path = op.join(XNK_dir, 'JC_Gold.nk'),
                       mat_name='JCGold') #<-- No adapter, so have to set name manually

    def _MediumMaterial_default(self): 
        return self.Dispwater()
    
    def simulation_requested(self):
        out = super(NanoSphere, self).simulation_requested()
        
        # Core/medium materials and Mie scattering
        out['material_core'] = self.CoreMaterial.simulation_requested()
        out['material_medium'] = self.CoreMaterial.simulation_requested()       
        out['mie_full'] = self.FullMie.simulation_requested()
        out['r_core'] = self.r_core            
        return out

    def allview_requested(self, prefix=None):
        """Dielectric for self, core, medium, and MIE plots
        """
        # Don't call super, don't want composite material's M1, M2 ...
        out = {'perm': self.mview}              

        out.update(self.FullMie.allview_requested(prefix='mie_full'))
        out.update(self.CoreMaterial.allview_requested(prefix='core'))
        out.update(self.MediumMaterial.allview_requested(prefix='medium'))

        if prefix:
            out = dict( ('%s.%s' %(prefix, k), v) for k,v in out.items() )
        return out


# DRUDE MODELS BELOW MAY BE DEPRECATES	
# ------------------------------------
class DrudeNew(ABCMetalModel, NanoSphere):
    '''Drude model with interband contributions(From paper "Advanced Drude Model")'''
    mat_name=Str('Drude Gold Nanoparticle')
    valid_metals=Enum('gold') 
    lamp=Float(145)
    gamp=Float(17000)
    nm_conv=Float(.000000001)   #why is lamp in these units?
    wplasma=Float()  #1.29 E 16
    v_fermi=Float(1.4 * 10**6)         #Same for gold and silver

    traits_view=View( Item('mat_name', show_label=False), 
                      Item('mviewbutton', label='Show Dielectric', show_label=False),
                      Item('r_core', show_label=True, style='simple', label='NP Radius'),
                      Item('FullMie')
                      )

    def _wplasma_default(self): 
        return 2.0*math.pi*self.c/(self.lamp * self.nm_conv)

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
            eeff[i] = complex(fr, fi)	
        self.earray = eeff
        self.CoreMaterial = self


class DrudeNP_corrected(DrudeBulk, NanoSphere):
    '''Corrects plasma frequency for free electron term; from Gupta 2'''

    valid_metals=Enum('gold','silver')  #Need fermi velocity for copper and aluminum
    apply_correction=Bool(True)

    def _valid_metals_changed(self): 
        self.update_data()
    
    def _r_core_changed(self):
        self.update_data()

    def _apply_correction_changed(self): 
        self.update_data()	

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

        # WTF IS THIS
        self.CoreMaterial=self

    traits_view=View(Item('r_core'), Item('valid_metals'),
                     Item('lam_plasma', style='readonly'),
                     Item('lam_collis', style='readonly'),
                     Item('mviewbutton'),
                     Item('apply_correction', label='Free Path Correction'),
                     Item('FullMie')
                     )


class NanoSphereShell(NanoSphere):
    '''This is a single object, but it inherits from composite material to allow for trait changes and stuff to be understood'''		
    from mie_traits_v2 import sphere_shell
    from composite_materials_v2 import CompositeMaterial_Equiv, SphericalInclusions_Shell
    from composite_plots import DoubleSview
    from material_models import Constant
    
    # bug in composite material name or something preventing this...
    mat_name = Str('AuNP & Shell')

    #Note: CoreMaterial refers to the core/shell composite object that is the "NanoSphere" for this instance #


    ShellMaterial=Instance(IMaterial)    #Composite Shell	
    CoreShellComposite=Instance(IMaterial)
    TotalMix=Instance(IMaterial)   #TotalMix is used to mix the composite sphere/shell and medium 
                    #Neceassary because Mix() already defined such that Corematerial is already sync'd to solute
                    #TotalMix syncs CompositeCore to solutematerial.  Solution not ideal

    np_plots=Instance(DoubleSview)
    free_path = Bool(False)

    earray=DelegatesTo('TotalMix')
    Vfrac=DelegatesTo('TotalMix')

    # selected_material.ShellMaterial.Vfrac is shell trait

    CompositeMie=Instance(IMie)  #This will store optical properties of the composite scattering cross section

    shell_width = Float(2)	

    opticalgroup=Group(
        Tabbed(
            Item('FullMie', editor=InstanceEditor(), style='custom', label='Mie Particle w/ Shell', show_label=False, ),
            Group( 
                Item('CompositeMie', 
                     editor=InstanceEditor(), 
                     style='custom', label='Mixed Mie Particle', show_label=False), 	
                #				Item('CompositeMixStyle', style='custom', show_label=False),
                #				Item('CompositeMix', style='custom', show_label=False),				     
                label='Equivalent Particle')
            ),
        label='Optical Properties')

    coregroup=Group(
        Item('CoreMaterial', style='custom', show_label=False), 
        Item('selectmat1', label='Choose Core Material', show_label=False) , 
        label='Core Material',
    )

    mediumgroup=Group(	
        Item('MediumMaterial', editor=InstanceEditor(),style='custom', show_label=False),
        Item('selectmat2', label='Choose Medium Material', show_label=False) , 
        label='Medium Material', 
    )

    compnpgroup=Group(
        HGroup(            
            Item('d_core', label='NP Core diameter', width=5),
            Item('r_core', label='NP Core radius'),
            Item('shell_width', label='NP Shell thickness', width=0.5),
            Item('mviewbutton', label='Show Full material', show_label=False),
            Item('np_plots', show_label=False)
            ),
        Group(
            Tabbed(
                Include('coregroup'),
                Include('mediumgroup'),
                Item('ShellMaterial', editor=InstanceEditor(), style='custom', label='Shell Material', show_label=False),
                Include('opticalgroup'),
                Item('CoreShellComposite', style='custom', label='CoreShellComposite Mix', show_label=False),
                Item('TotalMix', style='custom', label='Surface Coverage', show_label=False),
                label='Constituent Materials and Optical Properties' ), 
            ),

    )


    traits_view=View(Include('compnpgroup'), 
                     title='Composite Nanoparticle with Shell', 
                     resizable=True )

    def __init__(self, *args, **kwds):
        super(NanoSphereShell, self).__init__(*args, **kwds)
        # sync syntx ('Trait name here', Object to sync with, 'trait name there'##
       
        self.sync_trait('CoreMaterial', self.CoreShellComposite, 'Material1')
        self.sync_trait('ShellMaterial', self.CoreShellComposite, 'Material2')  
        
        # Sync my solvent to shellmaterial solvent
        self.sync_trait('MediumMaterial', self.ShellMaterial, 'Material2')

        # Material 2 is set in CoreShellComposite itself (ie the inclusion matera
        self.sync_trait('r_core', self.CoreShellComposite, 'r_particle')
        self.sync_trait('shell_width', self.CoreShellComposite, 'shell_width')

        self.sync_trait('r_core', self.ShellMaterial, 'r_platform')
        self.sync_trait('shell_width', self.ShellMaterial, 'shell_width') # <---- Will set r_inclusion, confirmed        
        
        self.sync_trait('selectedtree', self.CoreShellComposite, 'selectedtree')
        self.sync_trait('selectedtree', self.ShellMaterial, 'selectedtree')        

        # Mixes the Complex Particle and Medium (SHOULD SYNC R_EFFECTIVE, NO?)
        self.sync_trait('CoreShellComposite', self.TotalMix, 'Material1')
        self.sync_trait('MediumMaterial', self.TotalMix, 'Material2')
        self.sync_trait('r_core', self.TotalMix, 'r_particle', mutual=False) #<-- USES RCORE NOT R_EFF   
        
        # Sync materials to composite mie, including shell!
        self.sync_trait('CoreShellComposite', self.CompositeMie, 'CoreMaterial') #<-- IMPORTANT
        self.sync_trait('MediumMaterial', self.CompositeMie, 'MediumMaterial')

        self.sync_trait('CoreMaterial', self.FullMie, 'CoreMaterial', mutual=False) 
        self.sync_trait('MediumMaterial', self.FullMie, 'MediumMaterial')        
        
        # Sync materials to full mie
        self.sync_trait('ShellMaterial', self.FullMie, 'ShellMaterial')
        self.sync_trait('shell_width', self.FullMie, 'shell_width')
        # COMPOSITE MIE RADII ARE SYNCED MANUALLY IN DECORATOR

    def _ShellMaterial_default(self): 
        return self.SphericalInclusions_Shell()
    
    def _CoreShellComposite_default(self): 
        """ This is the complex core/shell represented as a single particle.  This does
        not take into account medium.  That's handled in MIE.
        """
        return self.CompositeMaterial_Equiv()

    def _TotalMix_default(self): 
        return SphericalInclusions_Disk()   
    
    # Sphere and shell
    def _FullMie_default(self): 
        out = self.sphere_shell()
        out.sview.plot_title = 'Full Sphere-Shell'
        return out
    
    # Just a sphere BUT CORE RADIUS IS EFFECTIVE RADIUS!!!
    def _CompositeMie_default(self): 
        out = effective_sphere(r_core = self.r_core + self.shell_width, 
                                label='EFFECTIVE Radius')
        out.sview.plot_title = 'Composite Sphere'
        return out        
    
    @on_trait_change('r_core, shell_width, ShellMaterial.Material1, ShellMaterial.Material2')
    def r_eff(self):
        self.CompositeMie.r_core = self.r_core + self.shell_width

    def _np_plots_default(self): 
        return self.DoubleSview(scatt1=self.FullMie.sview, 
                                scatt2=self.CompositeMie.sview)


    def simulation_requested(self):
        """ Method to return dictionary of traits that may be useful as output for paramters and or this and that"""
        # Eventually, make complex materials liked mixed shell call down levels of this.  aka self.shellmaterial.simulation_requested()

        # Updates earray, narray, matname
        out = super(NanoSphereShell, self).simulation_requested()

        # Shell
        out['material_shell'] = self.ShellMaterial.simulation_requested()
        out['shell_thickness'] = self.shell_width                
        
        # Mie
        out['mie_composite'] = self.CompositeMie.simulation_requested()
        
        # Mix
        out['mix'] = self.TotalMix.simulation_requested()
        
        return out
    
    def allview_requested(self, prefix=None):
        """Dielectric for self, core, medium, shell, full and composite MIE
        """
        # Don't call super, don't want composite material's M1, M2 ...
        out = super(NanoSphereShell, self).allview_requested() #<-- no prefix          

        out.update(self.CompositeMie.allview_requested(prefix='mie_equiv'))
        out['mie_double.cross_sec'] = self.np_plots
        out.update(self.ShellMaterial.allview_requested(prefix='shell'))
        out.update(self.CoreShellComposite.allview_requested(prefix='core_shell'))

        if prefix:
            out = dict( ('%s.%s' %(prefix, k), v) for k,v in out.items() )
        return out


class DoubleNanoparticle(DoubleComposite):
    """ Double material, but default values are gold and silver nanospheres.
    """

    mat_name = Str('Small & Big AuNPs')
        
    # Might want to eventually explicitly sync medium in __init__ of doublecomposite
    def _Material1_default(self): 
        return NanoSphereShell(r_core = 12, MediumMaterial=self.Medium)

    def _Material2_default(self): 	
        return NanoSphereShell(r_core = 100, MediumMaterial=self.Medium)
    
    def _Medium_default(self):
        return Dispwater()  
    


if __name__ == '__main__':
#	NanoSphereShell().configure_traits()
    DoubleNanoparticle().configure_traits()