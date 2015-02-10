from traits.api import *
from traitsui.api import *
import sys
import math
from numpy import empty, array, conj, inf
from basicplots import OpticalView
from main_parms import SpecParms, AngleParms
from interfaces import IOptic, ILayer
from scipy.integrate import simps
import logging
from tmm_mod import vector_com_tmm
import numpy as np
from pandas import Panel
import globalparms


class OpticalModelError(Exception):
    """ """

class DielectricSlab(HasTraits):
    '''Class used to store data in an interactive tabular environment'''
    
    # Need base_app to delegate fiberparms, so find that delegate the rest
    base_app = Any
    specparms = DelegatesTo('base_app')
    fiberparms = DelegatesTo('base_app')
    layereditor = DelegatesTo('base_app')

    x_unit = DelegatesTo('specparms') #<-- Required by optic_view for xaxis, wish easier to acess these globally
    lambdas = DelegatesTo('specparms')	
    Mode = DelegatesTo('fiberparms')
    angles = DelegatesTo('fiberparms')
    angles_radians=DelegatesTo('fiberparms')
#   betas=DelegatesTo('fiberparms')

    angle_avg = DelegatesTo('fiberparms')
    N = DelegatesTo('fiberparms')
    
#    layereditor=Instance(LayerEditor,())            #Need to initialize this because properties depend on this instance
    stack= DelegatesTo('layereditor')               #Variables are stored here just because they can be useful for future implementations

    # PRIMARY STORAGE OBJECT FROM TRANSFER MATRIX FORMALISM
    optical_stack = Instance(Panel)
    opticview = Instance(OpticalView)

    nsubstrate=Property(Array, depends_on='stack')
    ns=Property(Array, depends_on='stack')    #This is a list of arrays [n1, n2, n3] one for each layer
    ds=Property(Array, depends_on='stack')    #This is a lis

    #sim_designator=Str('New Simulation') #<--- WHY
    implements(IOptic)
    
    # Need to initialize base_app first or Delegation Will not work
    def __init__(self, *args, **kwargs):
        self.base_app = kwargs.pop('base_app')
        super(DielectricSlab, self).__init__(*args, **kwargs)

    def _opticview_default(self):
        return OpticalView(optic_model = self)

    def update_opticview(self): #pass
        """ Recomputes optical parameter. Updates the plot.  """
        # Updates Stack parameters (R, T, A, rt...)
        self.update_optical_stack()
        # Updates plot (opticview)
        self.opticview.update()

    #@cached_property
    def _get_ns(self): 
        rows=len(self.stack) 
        cols=self.lambdas.shape[0]
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
            if layer.d != globalparms.semiinf_layer:  #When does this happen?  Substrate/solvent?
                ds.insert(-1, layer.d)
        return array(ds)

    # RENAME
    def update_optical_stack(self):
        """ Calls the transfer method matrix vectorially (for each wavelength) and for each angle.
        Results are stored in a pandas Panel of Item Axis Angle.  For each angle, there's a 
        DataFrame which stores R(lam), T(lam), r(lam) etc... ie the vectorized reflectance, 
        transmittance, reflectance amplitude etc... anything returned by vector_com_tmm().
        
        If polarization is both, the average of these values at each polariziation is stored.  For example
        Rs + Rp / 2.0 gives the average, unpolarized reflection coefficient.  This should work for
        complex quantities like the reflection amplitude (ie rs + rp / 2.0); however, the average
        (possilby complex) reflection amplitude squared is not necessarily equal to Rs + Rp /2 unless
        rs and rp are real.  
        
        The takeaway is that for unpolarized light, the operation (results_s + results_p) / 2.0 is performed
        on the DataFrames, irregardless of a real or complex value in each columns.  We confirmed this works
        as expected, and when plotted, only the real part will be plotted anyway (default behavior of pandas plot).
        """
        print 'recomputing optical stack'

        if self.Mode == 'S-polarized':
            pol = 's'
        elif self.Mode == 'P-polarized':
            pol = 'p'
        elif self.Mode == 'Unpolarized':
            pol = 'both'
        else:
            raise OpticalModelError('Mode must be "S-polarized", "P-polarized" or Unpolarized; crashing intentionally.')
            sys.exit()
            

        paneldict = {}        
        for ang in self.angles:
            # CALCULATION IN RADIAN MODE
            ang_rad = math.radians(ang)
            
            if pol == 'both':
                df_s = vector_com_tmm('s', self.ns, self.ds, ang_rad, self.lambdas) 
                df_p = vector_com_tmm('p', self.ns, self.ds, ang_rad, self.lambdas)                  
                result_dataframe = (df_s+df_p) / 2.0

                # Add ellipsometry parameter Psi
                tan_psi = df_p['r_amp'].abs() / df_s['r_amp'].abs()
                result_dataframe['r_psi'] = np.arctan(tan_psi)

                # j ln( tan_psi * [r_s / r_p ] ) reversed ratio in algebra, work it out...

                # Use mpmath http://mpmath.googlecode.com/svn/trunk/doc/build/functions/powers.html
                # But mpmath needs loops, doesn't work on array
                # Tried numpy.log, numpy.lib.scimath.log.... same thing
                result_dataframe['r_delta'] = 1.0j * \
                    (np.log( (tan_psi * (df_s['r_amp'] / df_p['r_amp']) ) ))
                
                
            else:
                result_dataframe = vector_com_tmm(
                    pol, self.ns, self.ds, ang_rad, self.lambdas
                                            )
                # FILL PSI/DELTA TO NANS IF UNPOLARIZED!
                result_dataframe['r_psi'] = np.nan * np.empty(len(self.lambdas))
                result_dataframe['r_delta'] = np.nan * np.empty(len(self.lambdas))
                

            paneldict[ang] = result_dataframe

        # UPDATE optical_stack!
        self.optical_stack = Panel(paneldict)
              

    def as_stack(self, attr):
        """ Return attribute from optical stack in a 2darray.  IE if have 5 angles and 
        for each angle have 100 reflectance coefficients, returns a 5x100 matrix.  Used
        for arrayplotdata compatibility with .
        """
        # Potentially going to mix complex and floats, so these will be objects.
        out_2d = np.vstack([self.optical_stack[item][attr] for item in self.optical_stack])
        #print out_2d, '\nattr', out_2d.dtype
        return out_2d
    
    def _angle_avg_default(self):
        return 'Equal'
    
    # Should this return Series instead??  For simulation, have to reconstruct it...
    def compute_average(self, attr):
        """ Returns the angle average of an optical parameter of self.optical_stack,
        eg "R" or "A".  Averaging style delegates to FiberParms (angle_avg)
        """
        # DOES IT MATTER THAT AVERAGE IS COMPLEX
        matrix = self.as_stack(attr)

        if self.angle_avg == 'Gupta': 
            return self.gupta_averaging(attr)

        elif self.angle_avg == 'Equal': 
            return np.average(matrix, axis=0)            
        
        else:
            raise OpticalModelError('Unknown averaging style: %s' % self.angle_avg)
            

    def gupta_averaging(self, matrix):
        """ CITE ME!!
        matrix is the return of as_stack(attr) where attr can be Reflectance, Transmittance 
        etc..."""
        P_num=empty((self.angles.shape[0], self.nsubstrate.shape[0]), dtype=float)  #<-- COMPLEX!? RN IS NOW COMPLEX
        P_den=empty((self.angles.shape[0], self.nsubstrate.shape[0]), dtype=float)
        
        sa = np.sin(self.angles_radians)
        ca = np.cos(self.angles_radians)
        
        for i in range(len(self.angles)):
            f1=self.nsubstrate**2 * sa[i] * ca[i]       #Technically nsubstrate is complex so this is complaining
            Rn=self.matrix[i,:]**self.N[i]
            logging.info('N, rn', self.N[i], Rn)

#			f2=1.0 - (self.nsubstrate**2 * self.ca[i]**2)     
#			f3=f1/(f2**2) 	

            P_num[i,:]=(self.matrix[i,:]**Rn) * f1  #NOTATION FROM GUPTA LED  I THINK ITS NUMERICALLY UNSTABLE BECAUSE R<1 and N is huge so equals 0
            P_den[i,:]=f1	

        tempnum =simps(P_num, axis=0, even='last')
        tempden =simps(P_den, axis=0, even='last')
        return tempnum/tempden
    
    def simulation_requested(self, update=False):
        """ Returns optical stack and any other useful traits of dielectric slab for 
        simulation. Update used to skip updating, since simulations often call this twice.
        """
        if update:
            self.update_optical_stack()
        return {'optical_stack':self.optical_stack.copy(deep=True)}


if __name__ == '__main__':
    DielectricSlab().configure_traits()