from traits.api import * 
from traitsui.api import *
from numpy import array, empty
import matplotlib.pyplot as plt
from interfaces import IMaterial, ISim
from numpy import linspace, divide
import copy
from simulationplots import SimViewList, MaterialViewList
from numpy import linspace
from main_parms import SpecParms
from layer_editor import LayerEditor
import time

class GeneralSim(HasTraits):
    '''Basic simulation for iterating over sets of variables that can be incremented over a shared increment.  For example, xs, xf and ys and yf over the 
       same interval, inc'''

    start=Button
    time=Str()   #Stores time that simulation ended
    notes=Str()

    layereditor=Instance(LayerEditor,())
    specparms=Instance(SpecParms,())
    opticstate=Instance(ISim) #Stack as stored in reflectance portion of code
    lambdas=DelegatesTo('specparms')
    stack=DelegatesTo('layereditor')
    restore_status=Bool(True) #Restore all traits to original values after simulation is over

    selected_material=DelegatesTo('layereditor')    #This is an object that will store the traits required by the sim.  For material objects, for example, this becomes selected_material
    required_traits=Dict  #Dictionary of required trait names, with start, end values in tuple form for iteration.  For example "Volume": (13.2, 120.0)"
    original_values=Property(Dict, depends_on='required_traits, selected_material')  #Original values of traits in required_traits
    missing_traits=Property(depends_on='required_traits, original_values')
    warning=Property(Str, depends_on='missing_traits') 

    inc=Int(3)

#	def __init__(self, *args, **kwargs):
#	   super(GeneralSim, self).__init__(*args, **kwargs)

    @cached_property
    def _get_original_values(self):	return self.layereditor.selected_material.get(self.required_traits.keys())  #Original values of traits in required list	

    @cached_property
    def _get_missing_traits(self): 
        missing=[]
        for trait in self.required_traits.keys():
            if trait not in self.original_values.keys():
                missing.append(trait)
        return missing

    @cached_property
    def _get_warning(self):
        print 'updating warning', self.selected_material
        outstring=''
        if len(self.missing_traits) > 0:
            outstring='Could not find required traits in your selected material\t' + str(self.selected_material)+'\t'
            for trait in self.missing_traits:
                outstring=outstring+'\t'+trait
        else:
            outstring='All Required Traits Found'
        return outstring

    def restore_parameters(self): self.selected_material.trait_set(**self.original_values) #Restore all traits to original values

    def runsim(self): pass

    def _start_fired(self): 
        self.runsim()
        if self.restore_status is True:
            self.restore_parameters()
        self.time=time.asctime( time.localtime(time.time()))

    @on_trait_change('selected_material')
    def _update(self): print self.selected_material.traits()



class MaterialSim(GeneralSim):
    '''Simulation properties that are only specific to a material'''

#	selected_material=DelegatesTo('layereditor')

    R_list=Instance(SimViewList,())      #Stores reflectance plots per iteration
    M_list=Instance(MaterialViewList,()) #Stores dielectric plots per iteration

class LayerVfrac(MaterialSim): 

    def _required_traits_default(self): 
        return {'Vfrac':linspace(0.0, 0.32, self.inc),
                #	'Mix.K':linspace(0.0, 0.5, self.inc),
                }  #Need to make this masked so users only see (0, .32)

    def runsim(self): 
        i=0
        svl_dic={}  #Dictionary that stores relevant data by variable, vf, connects to trials_dic in simulationsplots
        mvl_dic={}

    #       return getattr(object, trait)[row][column]


        for i in range(self.inc):
            for trait in self.required_traits.keys():
                print 'OMG HERE', getattr(self, 'selected_material')
                currentvalue={trait: self.required_traits[trait][i]}  #This just picks the current value of the iteration and makes it a new dic for example Vfrac:.12
                print i, currentvalue
                self.selected_material.trait_set(**currentvalue)   #sets the traits to intermittent values

            self.opticstate.update_opticview()         #Recompute Reflectance



    #		svl_dic[str(vf)]=self.opticstate.opticview.get_sexy_data()
    #		mvl_dic[str(vf)]=self.selected_material.mview.get_sexy_data()
    #		i=i+1
    #		print "Iteration\t", i, "\t of \t", self.inc, "\t completed"


        self.R_list.trials_dic=svl_dic
        self.M_list.trials_dic=mvl_dic


    traits_view=View(
        Item('time', label='Simulation Time', style='readonly'), Item('inc'), Item('restore_status'),  
        Item('warning', style='readonly'), 
        Item('start', enabled_when='warning=="All Required Traits Found"'), 
        Item('selected_material', style='readonly'),  #CHANGE HERE TOO
        Group(Item('R_list', style='custom', show_label=False), Item('M_list', style='custom', show_label=False), layout='tabbed'),
        Item('original_values', style='readonly', label='Selected mat traits'),
        Item('required_traits'),		)






if __name__ == '__main__':
    LayerVfrac().configure_traits()