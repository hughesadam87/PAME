from traits.api import *
from traitsui.api import *
import sys
import math
from numpy import empty, array, conj, inf
import layer_solver as ls
from basicplots import OpticalView
from main_parms import SpecParms, FiberParms
from interfaces import ISim, ILayer
from layer_editor import LayerEditor
from scipy.integrate import simps
from pandas import Panel
import logging
from tmm_mod import vector_com_tmm
import numpy as np

class ReflectanceError(Exception):
    """ """

class BasicReflectance(HasTraits):
    '''Class used to store data in an interactive tabular environment'''

    specparms=Instance(SpecParms,())
    fiberparms=Instance(FiberParms,())

    lambdas=DelegatesTo('specparms')	
    Mode=DelegatesTo('fiberparms')
    angles=DelegatesTo('fiberparms')
    angles_radians=DelegatesTo('fiberparms')
#   betas=DelegatesTo('fiberparms')

    angle_avg = DelegatesTo('fiberparms')
    N=DelegatesTo('fiberparms')
    
    layereditor=Instance(LayerEditor,())            #Need to initialize this because properties depend on this instance
    stack= DelegatesTo('layereditor')               #Variables are stored here just because they can be useful for future implementations

    # PRIMARY STORAGE OBJECT FROM TRANSFER MATRIX FORMALISM
    optical_stack = Instance(Panel)

    Reflectance=Property(Array, depends_on='optical_stack')
    Transmittance=Property(Array, depends_on='optical_stack')
    Reflectance_AVG=Property(Array, depends_on='Reflectance, angle_avg')

    opticview=Instance(OpticalView,())
    ui=Any

    nsubstrate=Property(Array, depends_on='stack')
    ns=Property(Array, depends_on='stack')    #This is a list of arrays [n1, n2, n3] one for each layer
    ds=Property(Array, depends_on='stack')    #This is a lis

    sim_designator=Str('New Simulation')

    implements(ISim)

    traits_view=View(
        Item('Mode'),
        Item('sim_designator'),
        Item('ds', style='simple'), 
        Item('Reflectance'),
        resizable=True
    )


     # AUTO UPDATE PLOT WITH VARIOUS TRAITS
#    @on_trait_change('fiberparms.Config, fiberparms.Mode, fiberparms.Lregion, fiberparms.Dcore,'
#                     'fiberparms.angle_start, fiberparms.angle_stop, fiberparms.angle_ind') 
#    def sync_stack(self):
#        self.update_opticview()

    def update_opticview(self): #pass
        """ Updates the plot.  Recompitcs optical parameter"""
        # Updates reflectance
        self.update_optical_stack()

        # Updates plot (opticview)
        self.opticview.update(self.lambdas, 
                            self.angles,
                            self.Reflectance,
                            self.Transmittance,
                            self.Reflectance_AVG)

    #@cached_property
    def _get_ns(self): 
        rows=len(self.stack) ; cols=self.lambdas.shape[0]
        ns=empty( (rows, cols), dtype=complex )
        for i in range(rows):	
            layer=self.stack[i]
            ns[i,:]=layer.material.narray	#LIST OF ARRAYS NOT AN ARRAY 		
        return ns	

    #@cached_property
    def _get_nsubstrate(self):
        for layer in self.stack:
            if layer.name == 'Substrate':
                return layer.material.narray

    #@cached_property
    def _get_ds(self): 
        """Returns inf, d1, d2, d3, inf for layers"""
        ds = [inf, inf]
        for layer in self.stack:
            if layer.d != 'N/A':  #When does this happen?  Substrate/solvent?
                ds.insert(-1, layer.d)
        return array(ds)

    # RENAME
    def update_optical_stack(self):
        '''Actually computes R'''
        print 'recomputing optical stack'

        if self.Mode == 'S-polarized':
            pol = 's'
        elif self.Mode == 'P-polarized':
            pol = 'p'
        elif self.Mode == 'Mixed':
            pol = '????'
            print '\n\n\nSKIPPING MIXED MODE!!!\n\n\n\n'          
        else:
            raise ReflectanceError('Mode must be "S-polarized", "P-polarized" or Mixed; crashing intentionally.')
            sys.exit()

        paneldict = {}
        for ang in self.angles:
            ang = math.radians(ang)
            paneldict[ang] = vector_com_tmm(pol, 
                                            self.ns,
                                            self.ds, 
                                            ang, 
                                            self.lambdas
                                            )

        # UPDATE optical_stack!
        self.optical_stack = Panel(paneldict)

    #Don't forget about pandas swapaxes(0,1) etc.. for changing orientation

    #@cached_property
    
    def as_stack(self, attr, as_float=True):
        """ Return attribute from optical stack in a 2darray.  IE if have 5 angles and 
        for each angle have 100 reflectance coefficients, returns a 5x100 matrix.  Used
        for arrayplotdata compatibility with .

        as_float required for compatibility with chaco nan-checker
        """
        out_2d = np.vstack([self.optical_stack[item][attr] for item in self.optical_stack])
        if as_float:
            out_2d = out_2d.astype(float)
        return out_2d

    def _get_Reflectance(self):  
        return self.as_stack('R')
    
    #@cached_property
    def _get_Transmittance(self): 
        return self.as_stack('T')

    def _angle_avg_default(self):
        return 'Equal'

    #@c
    def _get_Reflectance_AVG(self):
        if self.angle_avg=='Gupta': 
            return self.gupta_averaging()
        elif self.angle_avg=='Equal': 
            return np.average(self.Reflectance, axis=0)

    # THESE BOTH USE REFLECTANCES INNATELY NOT TRANSMITTANCE!!!!!
    def equal_averaging(self): 
        return average(self.Reflectance, axis=0)

    def gupta_averaging(self):
        """ CITE ME!!"""
        P_num=empty((self.angles.shape[0], self.nsubstrate.shape[0]), dtype=float)
        P_den=empty((self.angles.shape[0], self.nsubstrate.shape[0]), dtype=float)
        
        sa = np.sin(self.angles_radians)
        ca = np.cos(self.angles_radians)
        
        for i in range(len(self.angles)):
            f1=self.nsubstrate**2 * sa[i] * ca[i]       #Technically nsubstrate is complex so this is complaining
            Rn=self.Reflectance[i,:]**self.N[i]
            logging.info('N, rn', self.N[i], Rn)

#			f2=1.0 - (self.nsubstrate**2 * self.ca[i]**2)     
#			f3=f1/(f2**2) 	

            P_num[i,:]=(self.Reflectance[i,:]**Rn) * f1  #NOTATION FROM GUPTA LED  I THINK ITS NUMERICALLY UNSTABLE BECAUSE R<1 and N is huge so equals 0
            P_den[i,:]=f1	

        tempnum =simps(P_num, axis=0, even='last')
        tempden =simps(P_den, axis=0, even='last')
        return tempnum/tempden


if __name__ == '__main__':
    BasicReflectance().configure_traits()