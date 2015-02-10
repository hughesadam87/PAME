from numpy import empty
import math
from enable.api import ComponentEditor
import re, os, sys
from traits.api import *    #Not worth it to do otherwise
from traitsui.api import *
from basicplots import MaterialView, ScatterView
from composite_plots import MultiView  
from converter import SpectralConverter
from main_parms import SpecParms
from interfaces import IMaterial, IMie
from chaco.api import Plot
import copy
from pame.utils import complex_e_to_n, complex_n_to_e
from pame.main_parms import SHARED_SPECPARMS

class BasicMaterial(HasTraits):
    
    implements(IMaterial)
    
    specparms=Instance(HasTraits, SHARED_SPECPARMS)    
    lambdas=DelegatesTo('specparms')	

    # For mview only
    x_unit=DelegatesTo('specparms')   

    earray=CArray()  
    narray=Property(CArray, depends_on=['earray'])
    karray=Property(CArray, depends_on=['narray'])  #Wave vectors

    mat_name=Str()
    source=Enum('Model', 'File', 'Custom')
    c=Float(299792458)     #Speed of light m/s

    mview=Instance(MaterialView,())  
    mviewbutton=Button 

    basic_group=HGroup(Item('mviewbutton', label='Show Material', show_label=False), 
                       Item('mat_name', label='Material Name', style='simple')
                       )

    traits_view=View(
        Include('basic_group'),
        resizable=True
    )

    def __init__(self, *args, **kwargs):
        super(BasicMaterial, self).__init__(*args, **kwargs)
        self.update_data()
        self.update_mview()  

    def _earray_default(self): 
        #Used later so not always redeclaring this
        return empty(self.lambdas.shape, dtype='complex') 
    
    def update_all(self):
        """ Update data, view all"""
        self.update_data()
        self.update_mview()
        # File materials and so on will update interp as well

    def _lambdas_changed(self): 
        self.update_all()
        
    def _earray_changed(self): 
        self.update_mview()

    # ABC METHOD
    def update_data(self): 
        """ Sets n or e arrays.  All subclasses must overwrite this!"""
        pass

    def update_mview(self): 
        self.mview.update(self.lambdas, self.earray, self.narray, self.x_unit)	


    def _mviewbutton_fired(self): 
        self.mview.data=None  #This will force a redraw which forces resizing of the plot.  Remove if you can fix the "auto_size" axis reset issue
        self.update_mview()
        self.mview.edit_traits()

        
    # Property Interface
    # ------------------
    def _get_narray(self): 
        return complex_e_to_n(self.earray)

    def _set_narray(self, narray):
        self.earray = complex_n_to_e(narray)

    def _get_karray(self): 
        return (2.0*math.pi*self.narray)/(self.lambdas) 


    def simulation_requested(self):
        """Dictionary of various traits that are useful for outputting as parameters. Overwrite
        with personal tastes.
        """
        return {'name':self.mat_name, 
                'source':self.source, #(not useful for simulation, right)                
                'earray':self.earray,
                'narray':self.narray}


if __name__ == '__main__':
    a=BasicMaterial() 
