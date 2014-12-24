from numpy import empty
import math
from numpy.lib import scimath as SM
from enable.api import ComponentEditor
import re, os, sys
from traits.api import *    #Not worth it to do otherwise
from traitsui.api import *
from basicplots import MaterialView, ScatterView
from composite_plots import MultiView  
from converter import SpectralConverter
from main_parms import SpecParms
from interfaces import IMaterial, IMie, ICompositeView
from chaco.api import Plot
import copy

class BasicMaterial(HasTraits):
    implements(IMaterial)

    specparms=Instance(SpecParms,())
    lambdas=DelegatesTo('specparms')	
    x_unit=DelegatesTo('specparms')   
    valid_units=DelegatesTo('specparms') #ONLY NEEDED IF YOU WANT X-UNITS IN VIEW SINCE THESE ARE LINKED VIA METADATA

    earray=CArray()  
    narray=Property(CArray, depends_on=['earray'])
    karray=Property(CArray, depends_on=['narray'])  #Wave vectors

    mat_name=Str()
    source=Enum('Model', 'File', 'Custom')
    c=Float(299792458)     #Speed of light m/s

    ### VIEW AND RELATED TRAITS###
    mview=Instance(MaterialView,())  
#	eplot=DelegatesTo('mview')     #Only needed if I want to include an instance of this view in the object itself
#	nplot=DelegatesTo('mview')

    eplot=Instance(Plot)
    nplot=Any

    allview=Instance(ICompositeView) #Test)
    allplots=Dict

    mviewbutton=Button 
    allbutt=Button

    basic_group=VGroup( Item('mat_name', label='Material Name', style='simple'),
                        Item('mviewbutton', label='Show Material'), Item('allbutt', label='Show allview'),
                       #Item('specparms', style='custom'),  #INCLUDE FOR TESTING PURPOSES
                                )

    traits_view=View(
        Include('basic_group'),
        resizable=True
    )

    def __init__(self, *args, **kwargs):
        super(BasicMaterial, self).__init__(*args, **kwargs)
        self.update_data(); self.update_mview() ; self.update_allplots()  #Needs to be run because the update_data generates the earray for all objects
        self.sync_trait('allplots', self.allview, 'nameplot')

    def _earray_default(self): return empty(self.lambdas.shape, dtype='complex')   #Used later so not always redeclaring this

    def _lambdas_changed(self): 
        self.update_data()
        self.update_mview()

    def _earray_changed(self): 
        self.update_mview()

    def _x_unit_changed(self): 
        self.update_mview()

    def update_data(self): pass

    def update_mview(self): 
        self.mview.update(self.lambdas, self.earray, self.narray, self.x_unit)	
        self.eplot=self.mview.eplot
        self.nplot=self.mview.nplot

    def get_usefultraits(self):
        """Dictionary of various traits that are useful for outputting as parameters. Overwrite
        with personal tastes.
        """
        return {'Material':self.mat_name}

    def update_allplots(self): 
        self.allplots={'KEY':self.eplot, }#'ni': self.nplot}  #Format is better than _allplots_defaults() for composite objects
    #	self.allplots={'di':self.mview, 'ni':self.mview}

    def _allview_default(self): 
        return MultiView(nameplot=self.allplots, host=self.mat_name)

    def _mviewbutton_fired(self): 
        self.mview.data=None  #This will force a redraw which forces resizing of the plot.  Remove if you can fix the "auto_size" axis reset issue
        self.update_mview()
        self.mview.edit_traits()


    def _allbutt_fired(self): 
        self.allview.edit_traits()

    def complex_n_to_e(self, narray): 		
        self.earray = empty(narray.shape, dtype='complex')  #This is necessary if changing lambdas, so everything works
        nr = narray.real
        nk = narray.imag          #NEED TO VERIFY THESE WORK SEE PLOT VS OLD VALUES
        self.earray.real = nr**2 -nk**2
        self.earray.imag = 2.0*nr*nk

    def complex_e_to_n(self): 
        return SM.sqrt(self.earray)  #Return narray given earray

    #@cached_property
    def _get_narray(self): 
        return self.complex_e_to_n()                #get/set format used to ensure dual-population

    def _set_narray(self, narray):
        self.complex_n_to_e(narray)  

    #@cached_property
    def _get_karray(self): 
        return (2.0*math.pi*self.narray)/(self.lambdas) 

if __name__ == '__main__':
    a=BasicMaterial() ; a2=a.clone_traits(copy='deep')
    print '-----------------'
    print a.eplot, a.allplots
    print '-----------------'
    print a2.eplot, a2.allplots
    print '-----------------'

