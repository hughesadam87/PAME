"""
Module to compute mie scattering coefficients using exact and approximate methods for various particles
Follows from some sources and mainly the textbook  "Abs and scattering of light by small particles by Huffamn and Bohren"
Program will accept dielectric or index representations of materials, with dielectric chosen as the canonical representation
May want to include some consistency tests to verify array lengths to avoid improper user input
"""

import math, sys, os, re
from scipy import special
from numpy.lib import scimath as SM
from numpy import linspace, empty
from traits.api import HasTraits, Any, Instance, Array, CArray, Str, Float, Int, Button, Bool, Interface, implements, DelegatesTo, on_trait_change
from traitsui.api import Item, Group, View, Tabbed, Action, HSplit, Include, HGroup, VGroup, InstanceEditor
from basicplots import ScatterView 
from main_parms import SpecParms
from interfaces import IMaterial, IMie
from material_models import DrudeBulk, Sellmeir, Dispwater

from pame import XNK_dir
from material_files import XNKFile
import os.path as op
from pame.main_parms import SHARED_SPECPARMS

class Mie(HasTraits):
    """Class to compute scattering coefficients given an input of a dielectric array"""
    implements(IMie)          

    CoreMaterial=Instance(IMaterial)
    MediumMaterial=Instance(IMaterial)

    ecore=DelegatesTo('CoreMaterial',prefix='earray')
    emedium=DelegatesTo('MediumMaterial', prefix='earray')  
    ncore=DelegatesTo('CoreMaterial', prefix='narray')
    nmedium=DelegatesTo('MediumMaterial',prefix='narray')  

    #Scattering cross section (C) and scattering efficiency (Q). C chosen as canonical representation
    Cabs=Array()
    Cscatt=Array()
    Cext=Array()

    #Cross section series convergence parameters.  Loops will iterate til cutoff is reached or until reaching bessmax (safety net)
    cutoff=Bool(False)
    cutoff_criteria=Float(.000001)      
    bessmax=Int(10)                     

    #Buttons and view items for general use
    sview=Instance(ScatterView,())
    sviewbutton=Button

    #View groups
    basic_group=HGroup(
        Item('cutoff_criteria', name='Convergence Criteria'), 
        Item('bessmax'),
        Item('sviewbutton', label='Cross Section', show_label=False)	                
    )

    traits_view=View(Include('basic_group'))

    # Lots of events will trigger draw of cross section (as they should)
    # Problem is, when lambdas changes, changes all of these materials,
    # and they each go on to trigger a redraw.  Somehow need to make this
    # cycle.  
    def __init__(self, *args, **kwargs):
        super(Mie, self).__init__(*args, **kwargs)
        self.on_trait_change(self.update_cross, 'CoreMaterial, MediumMaterial,\
                             ecore, emedium, bessmax, cutoff_criteria') 
        
    def _sview_default(self):
        return ScatterView(model=self)

    def _Cext_default(self): 
        return empty(self.ecore.shape[0], dtype='float')   
    
    def _Cabs_default(self):
        return empty(self.ecore.shape[0], dtype='float')   

    def _Cscatt_default(self):
        return empty(self.ecore.shape[0], dtype='float')

    # Overwrite as package data eventually
    def _CoreMaterial_default(self):  
        return XNKFile(file_path = op.join(XNK_dir, 'JC_Gold.nk'))

    def _MediumMaterial_default(self): 
        return Dispwater()

    def _sviewbutton_fired(self): 
        self.sview.edit_traits()   

    def update_cross(self): 
        """ ABC METHOD, udpate cross section"""

    #Utilities to do general looping and have a cutoff in place to truncate scattering coefficients.###
    def cutoff_check(self, new, old):
        """Method used to test for cutoff"""	
        if abs(new - old)/abs(new) <= self.cutoff_criteria:
            self.cutoff=True         #This flips the switch

    def cutoff_reset(self):
        """Resets cutoff if it is on, kind of like a switch reset"""
        self.cutoff = False

    #For generating ricatti bessel functions of arbitrary argument and order###
    #http://stackoverflow.com/questions/28441767/vectorized-spherical-bessel-functions-in-python?noredirect=1#comment45215851_28441767
    def bessy(self, n, z):
        """Given order (n) and argument (z), computes mad bessel related junk.
        Argument can be a scalar or vector numeric.
        """
        #http://docs.scipy.org/doc/scipy/reference/special.html
        # Returns all orders of N for a single argument (ie if order is 5,
        # returns n=0,1,2,3,4 for arg z.  Pain in the ass actually...
        # sph_jnyn computes jn, derivjn, yn, derivyn in one pass

        jn, djn, yn, dyn = special.sph_jnyn(n,z) #Compute sph j/y in one pass
        i = 1j

        # Choose only the nth's bessel function 
        jn=complex(jn[n])  
        yn=complex(yn[n])
        djn=complex(djn[n])
        dyn=complex(dyn[n])

        hn=jn + i*yn      #VERIFIED!!!
        dhn=djn + i*dyn #Derivative (d/dp (j + iy)) = (dj + idy)

        Psi=z*jn
        dPsi=z*djn + jn  #Psi = p(jn)  DPsi= jn + p j'n    Chain rollin
        Zi=z*hn	          
        dZi=z*dhn + hn    
        Xi=-z*yn          #Xi=-i*(Zi + Psi)     Verified WORKING either way!
        dXi=-(z*dyn + yn) #dXi=-i*(dZi + dPsi)

        return(Psi, dPsi, Zi, dZi, Xi, dXi)


    def simulation_requested(self):
        """ Returns interesting parameters during a simulation.  Traits like core
        radius might be redundantly output by material depending on the calling
        materials' simulation_requested() method, but that's better than having
        neither call them...
        """
        
        self.update_cross()
        return{
            'extinction':self.Cext,
            'absorbance':self.Cabs,
            'scattering':self.Cscatt
            }


    def allview_requested(self, prefix=None):
        """Organized references to view elements.  Used by main PAME UI.
        """
        out = {'cross_sec':self.sview} 
        
        if prefix:
            out = dict( ('%s.%s' %(prefix, k), v) for k,v in out.items() )
        
        return out


class ABCsphere(Mie):
    """Scattering functions for a plain sphere"""
    r_core=Float(12)
    basic_sphere_group=Group( Item('r_core') )
    k_medium=DelegatesTo('MediumMaterial', prefix='karray')

#	traits_view=View(Include('basic_sphere_group'), Include('basic_group') )
    traits_view=View(Item('MediumMaterial'), Item('sviewbutton'), Item('rcore'))

    def _r_core_changed(self): 
        self.update_cross()

    def simulation_requested(self):
        out = super(ABCsphere, self).simulation_requested()
        out['r_core'] = self.r_core
        return out


class shell(Mie):
    ### AS OF NOW THIS ONLY WORKS FOR SHELS OF REAL MATERIALS BECAUSE THE BESSEL FUNCTIONS TAKE IN THE WAVE VECTOR ###
    """Basic functions to handle operations on particles with shells"""
    ShellMaterial=Instance(IMaterial)
    eshell=DelegatesTo('ShellMaterial', prefix='earray')
    nshell=DelegatesTo('ShellMaterial', prefix='narray')
    shell_width=Float(2.0)

    basic_shell_group=Group( Item('shell_width') )

    traits_view=View( Item('shell_width') )

    def _ShellMaterial_default(self): 
        return Sellmeir()
    
    def _shell_width_changed(self): 
        self.update_cross()

    def _ShellMaterial_changed(self): 
        self.update_cross()

    def _eshell_changed(self):
        self.update_cross()
        

class sphere_electrostatics(ABCsphere):
    """Scattering cross section for a sphere using the conditions x<<1 and |m|x<<1 pg 136""" 

    def update_cross(self):
        x=self.k_medium* self.r_core
        Qscatt=(8.0/3.0 * x**4) * ( abs(self.ecore-self.emedium/ self.ecore+2.0* self.emedium)**2 )  #????QSCAT VS CSCATT???
        # DOESN"T SET/RETURN ANYTHING	


class bare_sphere(ABCsphere):
    """Full mie solution to plain sphere"""
    
    bare_sphere_group=Group(Include('basic_group'), 
                            HGroup(
                                Item('r_core', label='Core Radius'), 
                                ), 
                            )
    
    traits_view=View(VGroup(
        Include('bare_sphere_group'), 
        HGroup(
            Item('MediumMaterial', editor=InstanceEditor(), style='simple', show_label=False),
            Item('CoreMaterial', editor=InstanceEditor(), style='simple', show_label=False),
            )), buttons=[ 'OK', 'Cancel', 'Undo', 'Help']
            )

    def update_cross(self):
        for i in range(self.ecore.shape[0]):   #XX! Can't remove; bessel functions can't generate with full arrays
            ext_term=0.0  ; scatt_term=0.0 ; ext_old=50
            asum=0.0      ; bsum=0.0
            n=0
            while self.cutoff==False and n <= self.bessmax:   #DYNAMIC CONVERGENCE, WITH SAFETY NET
                n=n+1                   #  SUM FROM 1 TO INFINITY!!!
                k=self.k_medium[i]
                x=k*self.r_core         
                m1=self.ncore[i]/self.nmedium[i]   #m1 is really just m in book 
                Px, dPx, Xx, dXx = self.bessy(n,x)[0:4]   #Riccati bessel of X
                Pmx, dPmx, Xmx = self.bessy(n, m1*x)[0:3] #Ricatti bessel of MX
                

                f1=m1*Pmx*dPx  ; f2=Px*dPmx  ;  f3=m1*Pmx*dXx  ;  f4=Xx*dPmx
                a=(f1-f2)/(f3-f4)

                f1=f1/m1  ; f2=m1*f2 ;  f3=f3/m1  ; f4=m1*f4            #Relation between at and be is simply adjusting these by m or 1/m
                b=(f1-f2)/(f3-f4)

                asum=asum+a 
                bsum=bsum+b 
                AB=a+b
                
                # Why only real components in ext term?
                ext_term=ext_term + ( (2.0*n + 1.0)  * AB.real)      #UNITLESS
                scatt_term=scatt_term + ( (2.0*n + 1.0) ) * ( (abs(a))**2  + (abs(b))**2)

                #Cutoff the loop, then reset the switch after#
                self.cutoff_check(ext_term, ext_old)     #THIS ONLY CHECKS THE SCATTERING TERM AN FOR CONVERGENCE, MAY NOT THE FIRST TO CONVERGE IN ALL INSTANCES
                ext_old=ext_term
            self.cutoff_reset()


            self.Cext[i]=( (2.0*math.pi)/(k**2) ) * ext_term            
            self.Cscatt[i]=( (2.0*math.pi)/(k**2) ) * scatt_term   #UNITS DEFINED BY 1/K**2
            self.Cabs[i]=self.Cext[i]-self.Cscatt[i]

        self.sview.update_data()     
        

    def update_cross_new(self):
#           for i in range(self.ecore.shape[0]):   #XX! Can't remove; bessel functions can't generate with full arrays
            ext_term=0.0  ; scatt_term=0.0 ; ext_old=50
            asum=0.0      ; bsum=0.0
            n=0
            while self.cutoff==False and n <= self.bessmax:   #DYNAMIC CONVERGENCE, WITH SAFETY NET
                n += 1                   #  SUM FROM 1 TO INFINITY, NOT 0!!!
                k=self.k_medium
                x=k*self.r_core         
                m1=self.ncore / self.nmedium   #m1 is really just m in book 
               
                Px, dPx, Xx, dXx = self.bessy(n,x)[0:4]   #Riccati bessel of X
                Pmx, dPmx, Xmx = self.bessy(n, m1*x)[0:3] #Ricatti bessel of MX
                
                f1=m1*Pmx*dPx  
                f2=Px*dPmx    
                f3=m1*Pmx*dXx 
                f4=Xx*dPmx
                a=(f1-f2)/(f3-f4)

                f1=f1/m1  
                f2=m1*f2 
                f3=f3/m1 
                f4=m1*f4            #Relation between at and be is simply adjusting these by m or 1/m
                b=(f1-f2)/(f3-f4)

                asum=asum+a 
                bsum=bsum+b 
                AB=a+b
                
                # Why only real components in ext term?
                ext_term += ( (2.0*n + 1.0)  * AB.real)      #UNITLESS
                scatt_term +=  ( (2.0*n + 1.0) ) * ( (abs(a))**2  + (abs(b))**2)

                #Cutoff the loop, then reset the switch after#
                self.cutoff_check(ext_term, ext_old)     #THIS ONLY CHECKS THE SCATTERING TERM AN FOR CONVERGENCE, MAY NOT THE FIRST TO CONVERGE IN ALL INSTANCES
                ext_old=ext_term

            self.cutoff_reset()

            self.Cext = ( (2.0*math.pi)/(k**2) ) * ext_term            
            self.Cscatt = ( (2.0*math.pi)/(k**2) ) * scatt_term   #UNITS DEFINED BY 1/K**2
            self.Cabs = self.Cext[i]-self.Cscatt[i]   
            self.sview.update_data()     

        
class effective_sphere(bare_sphere):
    """ Bare sphere, but r_core is implied to mean effective radius,
    usually r_core + shell_width passed in from another model.  Used by
    NanoSphereShell, which handles the r_core + shell_width sum.
    
    Computationally, this is identical to bare sphere (no shell parameters 
    into play in the cross section)
    """
    
    bare_sphere_group=Group(Include('basic_group'), 
                            HGroup(
                                Item('r_core', label='EFFECTIVE Radius')
                                ), 
                            )    


class sphere_shell(bare_sphere, shell):
    """This is a sphere with a surrounding shell; inherits from basic sphere"""
    sphere_shell_group=Group(Include('bare_sphere_group') )

    traits_view=View(VGroup(
        Include('sphere_shell_group'),
        HGroup(
            Item('MediumMaterial', style='simple', show_label=False),
            Item('CoreMaterial', style='simple', show_label=False),             #FOR TESTING PURPOSES
            Item('ShellMaterial', style='simple', show_label=False),
            ),
        ), buttons=[ 'OK', 'Cancel', 'Undo', 'Help'] 
                     )

    def update_cross(self):
        print 'full mie updating cross'
        for i in range(self.ecore.shape[0]):
            ext_term=0.0
	    scatt_term=0.0
	    ext_old=50.0 	  #Loop related parameters to ensure proper entry
            k=self.k_medium[i]
            x=k*float(self.r_core)         #N (nm CANCEL so conv not needed)
            y=k*float(self.shell_width+self.r_core)  #THIS IS IMPORTANT!!
            m1=self.ncore[i]/self.nmedium[i]
            m2=self.nshell[i]/self.nmedium[i]
            n=0
            while self.cutoff==False and n <= self.bessmax:   #DYNAMIC CONVERGENCE
                n=n+1                 

                #(Psi, dPsi, Zi, dZi, Xi, dXi)
                arg=(y)
                bess=self.bessy(n, arg)
                Py=bess[0] ; dPy=bess[1]; Zy=bess[2]  ; dZy=bess[3]
                arg=(m2*y)
                bess=self.bessy(n, arg)
                Pm2y = bess[0]  ; dPm2y=bess[1]  ; Xm2y=bess[4];  dXm2y=bess[5]  

                arg=(m1*x)
                bess=self.bessy(n, arg)
                Pm1x=bess[0] ; dPm1x=bess[1] ; Xm1x=bess[4];  dXm1x=bess[5]

                arg=(m2*x)
                bess=self.bessy(n, arg)
                Pm2x=bess[0] ; dPm2x=bess[1] ; Xm2x=bess[4];  dXm2x=bess[5]

                An=( (m2*(Pm2x*dPm1x)) - (m1 *(dPm2x*Pm1x)) ) / ( (m2*(Xm2x*dPm1x)) - (m1*(dXm2x*Pm1x)) )
                Bn=( m2*(Pm1x*dPm2x) - m1*(Pm2x*dPm1x) ) / (m2*(dXm2x*Pm1x) - m1*(dPm1x*Xm2x) )

                f1=(dPm2y - (An*dXm2y))      ;	f2=( Pm2y - (An*Xm2y) )  
                a=( (Py*f1) - (m2*dPy*f2) ) / ( (Zy*f1) - (m2*dZy*f2) )

                f1=(dPm2y - Bn*dXm2y)      ;  f2=(Pm2y - Bn*Xm2y )
                b=(m2*Py*f1 - dPy*f2) /  (m2*Zy*f1  - dZy*f2 )

                AB=a+b
                ext_term=ext_term + ( (2.0*n + 1.0)  * AB.real)      #UNITLESS
                scatt_term=scatt_term + ( (2.0*n + 1.0) ) * ( (abs(a))**2  + (abs(b))**2)

                #Cutoff the loop, then reset the switch after#
                self.cutoff_check(ext_term, ext_old)     
                ext_old=ext_term
            self.cutoff_reset()

            self.Cext[i]=( (2.0*math.pi)/(abs(k**2)) ) * ext_term            
            self.Cscatt[i]=( (2.0*math.pi)/(abs(k**2)) ) * scatt_term   #UNITS DEFINED BY 1/K**2
            self.Cabs[i]=self.Cext[i]-self.Cscatt[i]

        self.sview.update_data()

    def simulation_requested(self):
        out = super(sphere_shell, self).simulation_requested()          
        out['shell_width'] = self.shell_width
        return out
        

###FROM PAGE 135, MAY BE WORTH USING LATER###
#	ncoeff=( (m1**2 - 1.0) / (m1**2 + 2.0) ).imag      #ELECTROSTATIC APPROX
#	Cscatt[i]=4.0*math.pi * ncoeff
#	Qabs=Cscatt * math.pi * self.r_core**2           #* pi a^2    

