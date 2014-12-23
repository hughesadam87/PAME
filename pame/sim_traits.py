from traits.api import *
from traitsui.api import *
import sys
import math
from numpy import empty, array, conj, average, inf
import layer_solver as ls
from basicplots import SimView
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
#	betas=DelegatesTo('fiberparms')
    sa=DelegatesTo('fiberparms') ; sb=DelegatesTo('fiberparms')
    ca=DelegatesTo('fiberparms') ; cb=DelegatesTo('fiberparms')
    N=DelegatesTo('fiberparms')

    layereditor=Instance(LayerEditor,())            #Need to initialize this because properties depend on this instance
    stack= DelegatesTo('layereditor')               #Variables are stored here just because they can be useful for future implementations

    R=CArray()   #THIS IS REFLECTION RESPONSE NOT REFLECTANCE!

    # PRIMARY STORAGE OBJECT FROM TRANSFER MATRIX FORMALISM
    Stackdata = Instance(Panel)

    Reflectance=Property(Array, depends_on='Stackdata')
    Transmittance=Property(Array, depends_on='Stackdata')
    AvgArray=Property(Array, depends_on='Reflectance, angle_avg')

    angle_avg=Enum('Equal', 'Gupta')

    simview=Instance(SimView,())
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


    @on_trait_change('fiberparms.Config, fiberparms.Mode, fiberparms.Lregion, fiberparms.Dcore,'
                     'fiberparms.angle_start, fiberparms.angle_stop, fiberparms.angle_ind') 
    def sync_stack(self):
        self.update_simview()

    def update_simview(self): #pass

        # Updates reflectance
        self.update_R()

        # Updates plot (simview)
        self.simview.update(self.lambdas, 
                            self.angles,
                            self.Reflectance,
                            self.Transmittance,
                            self.AvgArray)
    #	if self.ui is not None:
    #		self.ui.dispose()
    #		self.ui=self.simview.edit_traits()

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
        ds = [inf, inf]
        for layer in self.stack:
            if layer.d != 'N/A':  #When does this happen?  Substrate/solvent?
                ds.insert(-1, layer.d)
        return array(ds)

    # RENAME
    def update_R(self):
        '''Actually computes R'''
        logging.info('recomputing R')

        if self.Mode == 'S-polarized':
            pol = 's'
        elif self.Mode == 'P-polarized':
            pol = 'p'
        elif self.Mode == 'Mixed':
            print '\n\n\nSKIPPING MIXED MODE!!!\n\n\n\n'          
        else:
            raise ReflectanceError('Mode must be "S-polarized", "P-polarized" or Mixed; crashing intentionally.')
            sys.exit()

        paneldict = {}
        for ang in self.angles:
            paneldict[ang] = vector_com_tmm(pol, 
                                            self.ns,
                                            self.ds, 
                                            ang, 
                                            self.lambdas
                                            )

        # UPDATE STACKDATA!
        self.Stackdata = Panel(paneldict)

    #@cached_property
    def _get_Reflectance(self):  
        out = np.vstack([self.Stackdata[item]['R'] for item in self.Stackdata])
        print out
        print out.shape
        return out

    #@cached_property
    def _get_Transmittance(self): 
        return np.vstack([self.Stackdata[item]['T'] for item in self.Stackdata])

    def _angle_avg_default(self):
        return 'Equal'

    #@cached_property
    def _get_AvgArray(self):
        print 'AVERAGING ANGLES WITH STYLE %s' % self.angle_avg
        if self.angle_avg=='Gupta': 
            return self.gupta_averaging()
        elif self.angle_avg=='Equal': 
            return self.equal_averaging()

    def equal_averaging(self): 
        return average(self.Reflectance, axis=0)

    def gupta_averaging(self):
        P_num=empty((self.angles.shape[0], self.nsubstrate.shape[0]), dtype=float)
        P_den=empty((self.angles.shape[0], self.nsubstrate.shape[0]), dtype=float)
        for i in range(len(self.angles)):
            f1=self.nsubstrate**2 * self.sa[i] * self.ca[i]       #Technically nsubstrate is complex so this is complaining
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