""" Effective mixing theories including Maxwell Garnett, Modified Maxwell Garnett from Garcia,
Bruggeman, QCA-CP.  Are used twice in pame.  First, used if using nanoparticle with shell, need
to pick how to represent core-shell particle as a composite particle, and that's done through
mixing.  Secondly, need to represent layer of spherical inclusions in a matrix (ie the stack layer)
which is MG Garnett by default, but again, can be any. 
"""

from traits.api import *
from traitsui.api import *
import math, sys
import numpy as np
import scipy.optimize
from main_parms import SpecParms
from interfaces import IMixer, IMie, IMaterial
from material_models import Sellmeir, Dispwater
from mpmath import findroot

from functools import partial

from traits.api import HasTraits, Int, Range
from traitsui.api import View, Item

class DoubleMixer(HasTraits):
    
    solutematerial=Instance(IMaterial)
    solventmaterial=Instance(IMaterial)

    esolute=DelegatesTo('solutematerial', prefix='earray')
    esolvent=DelegatesTo('solventmaterial',prefix='earray')

    mixedarray=CArray   
    mix_name=Str('')
        
    # http://stackoverflow.com/questions/28403356/dynamic-initialization-of-traits-range-object?rq=1
    # Leave these dynamic so Vfrac range can be controlled dynamically
    # for example in triple material that needs to maintain rainges
    # WHY DOESNT THIS WORK!?  ALso tried putting in its own class and delegating

    ## This is correct syntax i'ms ure
    #_vmin = Float(value=0.0)
    #_vmax = Float(1.0)
    #Vfrac = Range(low='_vmin', high='_vmax')
    
    Vfrac = Range(low=0.0, high=1.0, value=0.1)
    
    implements(IMixer)   #Inherited by subclasses
    
    # LEAVE AS IS, NECESSARY
    def __init__(self, *args, **kwargs):
        super(DoubleMixer, self).__init__(*args, **kwargs)
        # Yes, neccesary to listen to materials and earrays
        self.on_trait_change(self.update_mix, 'solutematerial, solventmaterial, \
                                               esolvent, esolute, Vfrac') 

        # Let composite_material call this; for some reason, isn't triggering 
        # when used with composite_material anyway
        #self.update_mix() 

    def update_mix(self): 
        if self.esolute.shape != self.esolvent.shape:
            return
                           
    
class LinearSum(DoubleMixer):
    """ Linear mixing: V(e1) + (1-V)e2 for e1=solute, e2=solvent"""

    # alpha = percent material 1.  Beta = percent material 2
    alpha = Range(0.0, 1.0, value=0.5)
    beta = Property(Range(0.0, 1.0, value=0.5), depends_on='alpha')
    
    def update_mix(self):
        if self.esolute.shape != self.esolvent.shape:
            return        
        self.mixedarray = self.alpha*self.esolute + self.beta*self.esolvent
        
    def _alpha_changed(self):
        self.update_mix()
        
    def _get_beta(self):
        return 1.0 - self.alpha
    
    def _set_beta(self, beta):
        self.alpha = 1.0 - beta
    
        
    traits_view = View(
                  VGroup(
                      Item('alpha', label='% Mat 1'),
                      Item('beta', label='% Mat 2')
                      )
                  )

class MG_Mod(DoubleMixer):    
    """Modified MG equations by Garcia; specific to spheres with dipoles. 
    
    Taken from:
        Estimation of dielectric function of biotin-capped gold nanoparticles via signal enhancement on surface plasmon resonance.
        Li, Tamada, Baba et. al.  Journal of phys. chem B. 2006 (110) 32.
        
    Which cites an original resource for this mixing model:
       Garcia, M. A.; Llopis, J.; Paje, S. E. Chem. Phys. Lett. 1999, 315, 313.
       
    Beta is a geometrical parameter which is 1/3 if the particles are spherical.
    K is considered to be nearly zero if the particles are separated far enough so that the
    dipolar interactions are negligible, or if particle arrangement is spatially cubic.
    """
    mix_name='Maxwell Garnett Modification'
    K=Range(low= -100.0, high= 100.0, value=0.0)   #Parameter in Maxwell Garnett Mixing Model

    traits_view=View( 
        Item('mix_name', label='Mixing Style', style='readonly'), 
        HGroup( 
                Item('Vfrac'), 
                Item('K')
                ), 
        HGroup(
#            Item('solutematerial', label='solute_in_materialmix', show_label=False),
#            Item('solventmaterial', label='solvent_in_materialmix', show_label=False),
            )
        )

    def _K_changed(self): 
        self.update_mix()

    def update_mix(self):
        """Its important to update the mixed array all at once because there's a listenter 
        in another method that can change at exact moment anything changes
        """
        if self.esolute.shape != self.esolvent.shape:
            return
            
        eeff=np.empty(self.esolute.shape, dtype='complex')
        em = self.esolvent#np.copy(self.esolvent)
        emr = em.real
        emi = em.imag  #Usually zero
        ep = self.esolute#np.copy(self.esolute)
        epr = ep.real
        epi = ep.imag

        A = self.Vfrac*(epr - emr)
        B = self.Vfrac*epi
        shell_scaling = (1.0/3.0)          #1/3 for spherical particles, not sure for others!!!
        gam = (1.0/(3.0*emr) ) + (self.K/(4.0*math.pi*emr))
        C = em + shell_scaling*(epr - emr) - self.Vfrac*gam*(epr-emr)
        D = shell_scaling*epi - self.Vfrac*gam*epi
        eff_r = emr + ( (A*C + B*D)/ (C**2 + D**2) )
        eff_i = ((B*C - A*D)/(C**2 + D**2)).real   #IMAGINARY PART SHOULD BE 0 NO MATTER WHAT!
        eeff.real = eff_r
        eeff.imag = eff_i
       
        self.mixedarray = eeff       
       

class RootFinder(DoubleMixer):
    """ These mixing models come from:

    Effect of interphase on effective permittivity of composites.
    J. Phys. D: Appl. Phys. 44 (2011) 1115042 (5pp)
    Liu, Wu, Wang, Li and Zhang

    Their paper gives a succinct equation to represent the maxwell garnett equation with volume fill correction,
    QCA-CP and Bruggeman's equation.  All can be solved with one equation of different coeffiecines, but requires a 
    root finder to solve it.  The roots have to be solved for the real and imaginary components separately.  
    """
    
    w=Enum(0,2,3)

    def fill_func_dielectric(self, x, em, e1, v, w):
        '''From paper 'effect of interphase on effective permittivity of composites, used in conj w/ newton rhapson'''
        A = v *  (e1 - em) / (e1 + 2.0*em + w*(x - em) )
        B = (x - em) / (x + 2.0*em + w*(x-em) )
        return B-A

    def update_mix(self):
        if self.esolute.shape != self.esolvent.shape:
            return
        
        eeff=np.empty(self.esolute.shape, dtype=complex)
        for i in range(len(eeff)):
            e1 = self.esolute[i]#.real    
            em = self.esolvent[i]#.real   #THIS IS GENERALLY THE SOLVENT
            
            partialfunc = partial(self.fill_func_dielectric, em=em, e1=e1, v=self.Vfrac, w=self.w)
            
            
            eeff[i] = findroot(partialfunc, 
                               (0.5, 1, 2),  #This is a root that we are guessing for 3 params
                               solver='muller',
                               )            
            
            #eeff[i] = scipy.optimize.newton(self.fill_func_dielectric, 
                                            #self.Root,
                                            #fprime=None, 
                                            #args=(em, e1, self.Vfrac, self.w),
                                            #tol=.0001, 
                                            #maxiter=1000)
#			self.Root=eeff[i]  #Reset the root
        self.mixedarray=eeff


class MG(RootFinder):
    mix_name='MG w/ RootFinder'
    w=0

    traits_view=View( 
        Item('mix_name',label='Mixing Style Name'), Item('Vfrac'))

class Bruggeman(RootFinder):
    mix_name='Bruggeman w/ RootFinder'  
    w=2

    traits_view=View( 
        Item('mix_name',label='Mixing Style Name'), Item('Vfrac'))
    

class QCACP(RootFinder):
    mix_name='QCACP w/ RootFinder'
    w=3

    traits_view=View( 
        Item('mix_name', label='Mixing Style Name'), Item('Vfrac'))


# Core/shell/Matrix scaling
###########################
class EquivMethod(DoubleMixer):
    """Mix a shell, core spherical nanoparticle mixture into a composite particle of effective radius.

    Essentially: 
         e_eff = gamma * e_core
    
    Does not use mixing theories, Bruggman, MG etc..., just is an equivalent coefficient form Garcia Eq. 2
    """
    mix_name='Equivalence Method'

#	mie=Instance(IMie)  #Since I want mie to store the main representation for r_particle and shell_width, and delgation control the rest, this needs to be here
    r_particle=Float(12)
    shell_width=Float(8)
    shell_core_ratio=Property(Float, depends_on=['r_particle', 'shell_width'])  #Make this to tune proportion
    gamma=Array


    traits_view=View( 
        ###  MADE A FEW OF THESE READ ONLY BECAUSE THEY ARE ACTUALLY TRAITS CONTROLLED BY THE MATERIAL VIEWER SO SHOULDN'T BE ADJUSTED WHEN MIXING ###			
        Item('mix_name',label='Mixing Style Name'), 
        HGroup(
            Item('r_particle', style='readonly'), 
            Item('shell_width', style='readonly'), 		
            Item('shell_core_ratio', label='Shell/Core Ratio', style='readonly'),
            ),

#        Item('solutematerial'), 
#        Item('solventmaterial'),
    )


    ###USES THE NOTATION THAT ESOLUTE REFERS TO DIELECTRIC FUNCTION OF CORE PARTICLE, ESOLVENT REFERS TO DIELECTRIC FUNCTION OF SHELL###

    def _r_particle_changed(self):
        self.update_mix()
    
    def _shell_width_changed(self): 
        self.update_mix()

    def _get_shell_core_ratio(self): 
        return round(self.shell_width/self.r_particle,2)

    def _set_shell_core_ratio(self, input_value): 
        '''If user changes ratio, this will adjust the shell (by choice) and not the core to fit the ratio'''
        self.shell_width=input_value * self.r_particle

    def update_mix(self):
        if self.esolute.shape != self.esolvent.shape:
            return        
        eeff = np.empty(self.esolute.shape, dtype='complex')
        r1 = self.r_particle
        r2 = self.shell_width+self.r_particle        #KEY THAT r2 is not just shell_width
        A = (r1/r2)**3
        B = self.esolvent/self.esolute
        
        num = (B*(1.0 + 2.0*B)) + (2.0*A*B*(1.0-B))
        den = (1.0+2.0*B) - (A*(1.0-B))

        gam = num/den #gamma is the equivalent coefficient
        self.mixedarray = gam*self.esolute

        self.gamma=gam  #In case I ever want to plot it, tacked this on 4_13_12


class CustomEquiv(EquivMethod):
    """Modification of the equivalence method to allow for scaling parmaeters on the size of the shell, core 
    and on the dielectric constants.  Note, the scaling is linear, meaning dispersion will scale only linearly.
    I replaced variables alpha/beta to avoid confusion with the primary resource.
    """
    mix_name='Custom Equiv Method'

    #Correction parameters for fine tuning shell, core to meet#
    core_scaling=Range(low=0.0,high=25.0,value=1.0) 
    shell_scaling= Range(low=0.0, high=15.0,value=1.0)

    e_core_scaling=Range(low=1.0,high=10.0,value=1.0)  
    e_shell_scaling=Range(low=1.0,high=10.0,value=1.0)  #This is the shell not overall medium

    rcore_eff=Property(Float, depends_on=['core_scaling, r_particle'])
    shell_width_effective=Property(Float, depends_on=['shell_scaling, shell_width'])

    traits_view=View(         #FOR SOME REASON 'shell_core_ratio' causes the view to crash!
                              VGroup(
                                  HGroup(Item('r_particle', style='readonly'), 
                                         Item('shell_width', style='readonly')), 
                                  HGroup(Item('rcore_eff'),
                                         Item('shell_width_effective') ),
                                  HGroup(Item('core_scaling'), 
                                         Item('shell_scaling')
                                         ), 
                                  HGroup(Item('e_core_scaling', label='Scaling of core dielectric'), 
                                         Item('e_shell_scaling', label='Scaling of shell dielectric')
                                         ),                                  # Item('shell_core_ratio') ),
                              )
                              )

    def _rcore_eff_changed(self): 
        self.update_mix()
    
    def _shell_width_effective_changed(self): 
        self.update_mix()

    def _e_core_scaling_changed(self): 
        self.update_mix()

    def _e_shell_scaling_changed(self): 
        self.update_mix()

    def _get_rcore_eff(self): 
        return self.core_scaling * self.r_particle

    def _get_shell_width_effective(self): 
        return self.shell_scaling * self.shell_width

    def update_mix(self):
        if self.esolute.shape != self.esolvent.shape:
            return
        
        r1=self.rcore_eff
        r2=self.shell_width_effective+self.rcore_eff        #KEY THAT r2 is not just shell_width
        A=(r1/r2)**3

        #Solvent in this case is shell on np not surrounding matrix/solution (VERIFIED 4_13_12)
        B = ((self.esolvent*self.e_shell_scaling)/(self.e_core_scaling * self.esolute) )   #B = eshell/ecore  (each one given a scale factor)
        num = (B*(1.0 + 2.0*B)) + (2.0*A*B*(1.0-B))
        den = (1.0+2.0*B) - (A*(1.0-B))
        gam = num/den
        self.mixedarray = gam*self.esolute
        self.gamma = gam


if __name__ == '__main__':
    DynamicRNG().configure_traits()