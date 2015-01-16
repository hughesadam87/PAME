""" Simulation program. """

# Python imports
import sys
import os.path as op
import time
import copy
from collections import OrderedDict
from pame import globalparms

# ETS imports
from traits.api import * 
from traitsui.api import *
from numpy import linspace, divide, savetxt
from traits.trait_base import xsetattr, xgetattr

#3rd party imports
from pandas import concat, Panel
from numpy import array, empty
import matplotlib.pyplot as plt

# Local imports
from handlers import FileOverwriteDialog, BasicDialog
from simparser import SimParser
from simulationplots import ReflectanceStorage, ScattStorage, MaterialStorage
from main_parms import SpecParms
from interfaces import IMaterial, ISim
from layer_editor import LayerEditor
import config
import customjson

class SimError(Exception):
    """ """

# ADD SAVE/LOAD UBTTONS
class SimConfigure(HasTraits):
    """ Configuration what is stored/output in simulation."""
    
    save = Button
    outpath = File

    # Used to store most common simulation names in a user-readable fashion, Enum for dropdown list.
    translator=Dict()
    translist=Property(List, depends_on='translator')
    traitscommon=Enum(values='translist')

    # Summary storage
    averaging = Enum('Average', 'Not Averaged', 'Both')
        
    #https://github.com/enthought/traitsui/blob/master/examples/demo/Standard_Editors/CheckListEditor_simple_demo.py
    choose_optics = List(editor=CheckListEditor(values = globalparms.header.keys(), cols=3))

    choose_layers = Enum('Selected Layer', 'All Layers', 'None')
    additional = Str()
    additional_list = Property(List, depends_on = 'additional, traitscommon')
    
    # Simulation object to be stored
    store_optical_stack = Bool(False)
    
    traits_view = View(
        HGroup(
            Item('choose_optics', style='custom', label='Optical Parameters'),
            Item('averaging', style='custom', label='Optical Averaging'),
            Item('store_optical_stack', label='Save deepcopy of full optical stack')
        ),

          Item('choose_layers', style='custom'),
          Item('traitscommon', label='Add Common Trait'),
          Item('additional', style='custom', label='Top-level Traits'),
        buttons = [ 'Undo', 'OK', 'Cancel' ]  
                   )       
    
    def _get_additional_list(self):
        """ User adds custom traits to additional box, deliminted by newline.
        This removes unicode and returns as a list like:
         [material1.trait1, material2.foo.trait5] etc...
         """
        out = [str(s) for s in self.additional.strip().split('\n') if s] #<-- blank string
        return list(set(out))  #<-- remove duplicates
        
    # Eventually replace with tree editor
    def _translator_default(self):	
        return {
           'Selected Layer Extinction Cross Section (NanoMaterials Only)':'selected_material.FullMie.Cext',
           'Selected Layer Scattering Cross Section (NanoMaterials Only)':'selected_material.FullMie.Cscatt',
           'Selected Layer Absorbance Cross Section (NanoMaterials Only)':'selected_material.FullMie.Cabs',
            }
    
    def _traitscommon_changed(self): 
        """ Set current layer from the name translator for more clear use. """	
        self.additional += self.translator[self.traitscommon]+'\n' #String

    def _get_translist(self): 
        return self.translator.keys()      
    
    

class SimAdapter(HasTraits):
    """Shows selected simulation in table on main view """
    trait_name = Str('add trait name')
    # THESE VALUES ARE SET WHEN BY CLASSES THAT CONTROL THE SIMS
    inc=Int() 
    start=Float()
    end=Float()
    trait_array=Property(Array, depends_on='start, end, inc')

    @cached_property
    def _get_trait_array(self): 
        """ Reserves an array large enough to store all the values that the traits will take on when incremented.  For example,
            if iterating between 1,10 by steps of 1, it will store 10 slots """
        try:
            return linspace(self.start, self.end, self.inc)
        except TypeError:  #Caused by unicode input which seems to happen spontaneously for an unknown reason
            return

class ABCSim(HasTraits):
    """Basic simulation for iterating over sets of variables that can be incremented over a shared increment.
       Contains methods to make sure traits that are being iterated over exist, and can be restored easily.  
       Simulation variables can be added quickly by changing the simulation_traits attributed"""

    base_app=Any  #THIS IS AN INSTANCE OF GLOBAL SCENE, ALL TRAITS WILL DELEGATE TO THIS.  

    sim_configuration = DelegatesTo('base_app') #Instance SimConfiguration

    start = Button
    time = Str('Sim not started')   #Stores time that simulation ended
    outname = Str('Testsim') #Output name, can be overwritten when output called
    outdir = DelegatesTo('base_app')

    implements(ISim)
    inc=Range(low=1,high=100,value=1) # Need as range for now I think

    notes=Str('<NOTES GO HERE>')

    key_title=Str('step')  #This is used to give each increment a name rather than 1,2,3

    # Select input variables/traits from human-readable dropdown list
    translator = Dict()
    translist = Property(List, depends_on='translator')
    tvals = Enum(values='translist')

    # Output Storage Objects
    summary = Dict
    results = Dict            
    static = Dict
    allstorage = Property(Dict) # Stores all three dicts plus metadata bout self
    _completed = Property(Bool)  # Set to true when results is populated (better criteria?) 

    # Table for selecting objects
    selected_traits=Instance(SimAdapter) 
    
    # Status/meta traits 
    sim_variables = List(SimAdapter) #Actual table of trait sto simulate over
    simulation_traits = Dict  #Dictionary of required trait names, with start, end values in tuple form for iteration.  For example "Volume": (13.2, 120.0)"
    original_values = Dict
    missing_taits = List
    # Restore all traits to original values after simulation is over
    restore_status=Bool(True)     
    status_message = Str #HTML
    ready = Bool(False)

    simeditor =\
        TableEditor(
            columns=[
                ObjectColumn(name='trait_name', label='Trait Name'),         #Add these in general sim class
                ObjectColumn(name='start', label='Start Value'),
                ObjectColumn(name='end', label='End Value'),
                ],
            deletable   = True, 
            auto_size = True,
            orientation = 'vertical',    #Orientation between built-in split between table and edit view
            show_toolbar=True,
            selected           = 'selected_traits',   #String name is arbitrary and passed as a global variable to other instances
            selection_color    = 0x000000,
            selection_bg_color = 0xFBD391,
            row_factory=SimAdapter
        )


    def simulation_requested(self):
        """Method for returning parameters/metadata about the simulation"""
        return {'Simulation Name':self.outname, 
                'Steps':self.inc, 
                'Time/Date':self.time, 
                'Notes':self.notes,
                'Simulated Traits':sorted(self.simulation_traits.keys())
                }

    def _tvals_changed(self): 
        """ Set current layer from the name translator for more clear use. """	
        self.selected_traits.trait_name = self.translator[self.tvals]
        self.check_sim_ready() #<-- When user changes simulation traits table

    # a class tot
    def _get_translist(self): 
        return self.translator.keys()  

    def _get__completed(self):
        """ Inspect storage objects and infer if simulation ran successfully.  Basically
        tests if self.results, summary and self.static are all empty.  After successfully 
        completed run_sim(), at least one of these should be populated.  Actually they all 
        should, but in some instances, users can select settings that make these empty.  Like
        if user doesn't want to store anything in the top-level summary.
        """
        if self.results == {} and self.summary == {} and self.static == {}:
            return False
        return True
        
    def _sim_variables_default(self): 
        return []

    def check_sim_ready(self):
        """Method to update various storage mechanisms for holding trait values for simulations.  
        Takes user data in table editor and stores it in necessary dictionaries so that 
        traits can be set and things automatically.  Decided to use this over a system
        properties because the properties were conflicting with delegation and other stuff.
        """
        sim_traits = {}
        originals = {}
        missing = []
        status_message = ''

        for obj in self.sim_variables:
            obj.inc=self.inc  #Ensures proper increments whether adding new objects to the table or just changing global inc

        for obj in self.sim_variables:
            sim_traits[obj.trait_name]=obj.trait_array        #Simulation traits

        for key in sim_traits.keys():
            try:
                originals[key]=xgetattr(self.base_app, key)  #If trait found, store its original values
            except AttributeError:
                missing.append(key)  #If not, put it in missing

        ready = True

        # Are traits missing?
        if len(missing) > 0:
            status_message='<font color="red"> Could not find required traits: </font>'
            for trait in missing:
                status_message += trait + ',  '
            ready = False
            
        # Did user select duplicates of trait names
        trait_names = [obj.trait_name for obj in self.sim_variables]
        duplicates = set([name for name in trait_names if trait_names.count(name) > 1])
        if duplicates:
            status_message='<font color="red"> Duplicate simulation trait(s) found: </font>'
            for trait in duplicates:
                status_message += trait + ',  '
            ready = False                        
        

        if ready:
            status_message='<font color="green"> Simulation ready: all traits found</font>'
            ready = True

        self.ready = ready
        self.status_message = status_message.rstrip(',') #<-- trialling commas for list of one element string
        self.simulation_traits = sim_traits
        self.missing_traits = missing
        self.original_values = originals

    def restore_original_values(self): 
        for trait in self.simulation_traits.keys():
            xsetattr(self.base_app, trait, self.original_values[trait]) #Restore all traits to original values

    def runsim(self): 
        """ ABC METHOD """
        pass

    def save_json(self, outpath=None, confirmwindow=True):
        """ Output simulation into json dictionary, where four primary
        storage dictionaries (self.allstorage) are written to 
        numpy-aware json.  Errors and confirmation messages in form of
        popups are triggered.

        outpath: 
            Full path to save json object.
            
        confirmwindow:
            Confirms simulation saved with popup window.
        """
                
        if outpath is None:
            outpath = op.join(self.outdir, self.outname)
            
        # Make sure .json 
        ext = op.splitext(outpath)[-1]
        if ext:
            if ext != '.json':
                raise SimError('Simulation save path must be .json file, got ' % outpath)
        # No file path
        else:
            outpath = outpath + '.json'
        

        # Check for file overwriting    
        if op.exists(outpath):
            test = FileOverwriteDialog(filename=outpath)
            ui = test.edit_traits(kind='modal')
            # break out and don't save#
            if ui.result==False:
                return

        # Save
        if not self._completed:
            message('Simulation is incomplete or stored incorrectly.'
                    ' See self._completed to debug', 
                    title='Warning')
            return 
        
        customjson.dump(self.allstorage, outpath)

        if confirmwindow == True:
            message('Simulation data saved to file %s' % outpath, title='Success')


    def _start_fired(self): 

        # Check sim traits one more time in case overlooked some trait that should call 
        # check_sim_ready()
        self.check_sim_ready()
        if not self.ready:
            return

        self.runsim()
        if self.restore_status:
            self.restore_original_values()
        self.time=time.asctime( time.localtime(time.time()))


    basic_group=VGroup(
        Item('status_message', style='readonly', label='Status Message'),
        HGroup(
            Item('sim_configuration', label='Configure Simulation Output'),            
            Item('restore_status', label='Restore state after simulation' ),
            Item('inc',label='Steps'), 
            Item('start', show_label=False), 
            Item('time', label='Sim Start Time', style='readonly'), 
            Item('outname',label='Run Name'), 
            Item('tvals', label='Selected Layer Common Traits') #, visible_when='self.selected_layer is not None'),
            # By default, always a selected layer, so visible_when not needed ^^^
            ),
        Item('sim_variables', editor=simeditor, show_label=False),
        Item('notes', style='custom'),
        label='Parameters')


class LayerSimulation(ABCSim): 
    """ Simulate stack layer traits like selected material traits (ie d_core) and thickness
    of layer. Name is kind of arbitrary because this could simulate any Incremental trait.
    What it couldnt' do is change a value like polarization halfway through the simulation!
    """
    selected_material=DelegatesTo('base_app') #Just for convienence in variable calling
    selected_layer=DelegatesTo('base_app')

    def _outname_default(self): 
        return 'Layersim'

    def _selected_material_changed(self):
        self.check_sim_ready()
        
    def _selected_layer_changed(self):
        self.check_sim_ready()

    # Replace with TreeEditor
    def _translator_default(self):	
        return {
           'Layer Fill Fraction':'selected_material.Vfrac',
           'Layer Thickness':'selected_layer.d',
           'NP Core radius (NanoMaterials Only)':'selected_material.r_core',
           'NP Shell Thickness (NanoShell Only)':'selected_material.shell_thickness',
           'NP Shell Fill Fraction (NanoShell Only)':'selected_material.CoreShellComposite.Vfrac' 
            }
    
    
    def _sim_variables_default(self):
        """ Initial traits to start with """
        obs=[]
        obs.append(SimAdapter(trait_name='selected_material.Vfrac', start=0.0, end=0.1, inc=self.inc)),  
        obs.append(SimAdapter(trait_name='selected_layer.d', start=50., end=100., inc=self.inc)),
        obs.append(SimAdapter(trait_name='selected_material.r_core', start=25., end=50., inc=self.inc)),
        return obs 
           

    def _get_allstorage(self):
        """ Returns Ordered dict of dicts, where each dictionary is a primary storage dictionary:
        IE self.summary, self.results, self.static and self.simulation_requested(), where
        simuliation requested gives metadata like num steps, simulation etc.. about this 
        particular run.
        """ 
        allout = OrderedDict()
        allout[globalparms.static] = self.static
        allout[globalparms.about] = self.simulation_requested()
        allout[globalparms.summary] = self.summary
        allout[globalparms.results] = self.results      

        return allout
        
        

    def runsim(self): 
        """ Increments, updates all results.  Thre primary storage objects:
        
        staticdict --> Traits that are no altered in simulation.  
           Includes simulation inputs, spectral parameters and fiber/strata
           parameters.  In future version, could relax these if needed
           to simulation over a fiber parameter like core size.
           
        summarydict --> Results that are to be promoted to top level.  
            Simparaser will try to show these as a panel.
            
        resultsdict ---> Deep, nested results of layer and optical stack.  For 
            example, could access full optical stack on third increment via:
                 resultsdict['step3']['optics']['opticalstack'] 
            or a selected material:
                 resultsdict['step5']['selectedlayer']['material1']['fullmie']
            etc...
            Simparser should have methods to make these data more accessible.
            
        """

        print 'running sim with traits', self.simulation_traits.keys()
        
        # for name brevity
        sconfig = self.sim_configuration 
        b_app = self.base_app

        # Storage
        summarydict = OrderedDict()   #<-- Keyed by increment, becomes summary panel!
        resultsdict = OrderedDict()   #<-- Keyed by increment, stores deep results, stays as dict
                       
        # Traits not involved in simulation.  For this sim, includes spectral parameters, fiber/strata params
        # at simulation inputs.  Later sims may want to simulate over fiber traits (ie fiber diameter changes)
        # so would migrate these into resultsdict instead
        staticdict = OrderedDict()
        staticdict['spectral_parameters'] = b_app.specparms.simulation_requested()         
        staticdict[globalparms.strataname] = b_app.fiberparms.simulation_requested()
                
        # Begin iterations
        sorted_keys = []
        for i in range(self.inc):
            for trait in self.simulation_traits.keys():
                trait = str(trait) # <--- get rid of damn unicode if user entered it
                xsetattr(b_app, trait, self.simulation_traits[trait][i]) #Object, traitname, traitvalue
                
            stepname = 'step_%s' % i
                
            summary_increment = OrderedDict()  #<--- Toplevel/Summary of just this increment (becomes dataframe)
            results_increment = OrderedDict()  #<--- Deep results of just thsi increment (ie selected_material/layer etc..)

            key = '%s_%s' % (str(i), self.key_title)
            sorted_keys.append(key)
            
            # Update Optical Stack
            b_app.opticstate.update_optical_stack() 
            
            # Take parameters from optical stack, put in toplevel via sconfig.choose_optics
            if sconfig.averaging in ['Average','Both']:
                for optical_attr in sconfig.choose_optics:
                    summary_increment['%s_%s' % (optical_attr, 'avg')] = \
                        b_app.optical_stack.compute_average(optical_attr)  
                
            if sconfig.averaging in ['Not Averaged', 'Both']:
                for optical_attr in sconfig.choose_optics:
                    # ITERATE OVER ANGLES! SAVE EACH ANGLE
                    for angle in sconfig.angles:
                        summary_increment['%s_%s' % (optical_attr, angle)] = \
                                    b_app.optical_stack(optical_attr)  #<-- Save as what?!        

            # Store full Optical Stack
            if sconfig.store_optical_stack:
                results_increment[globalparms.optresponse] = b_app.opticalstack.simulation_requested(update=False)
                
            # Save layer/material traits.  If None selected, it just skips
            if sconfig.choose_layers == 'Selected Layer':
                results_increment['selected_layer'] = self.selected_layer.simulation_requested()
                
            elif sconfig.choose_layers == 'All Layers':
                results_increment['dielectric_layers'] = b_app.stack.simulation_requested()
                    
                                  
            # resultsdict >>  {step1 : {results_of_increment}, ...}
            resultsdict[stepname] = results_increment               
            summarydict[stepname] = summary_increment

            print "Iteration\t", i+1, "\t of \t", self.inc, "\t completed"

        # SET STORAGE TRAITS
        self.summary = summarydict
        self.results = resultsdict
        self.static = staticdict

        # Prompt user to save?
        popup = BasicDialog(message='Simulation complete.  Would you like to save now?')
        ui = popup.edit_traits(kind='modal')
        if ui.result == True:
            self.save_json()

    ############
    # This view is for interactive plotting simulations
    ############
    layervfrac_group=VGroup(  
        Item('selected_material', style='readonly'),  #CHANGE HERE TOO
        Group(Item('R_list', style='custom', show_label=False), 
              Item('M_list', style='custom', show_label=False),
              Item('Scatt_list', style='custom', show_label=False), 
              layout='tabbed'),				
        label='Results')


    traits_view=View(
        VGroup(	
            Include('basic_group'),
            #          Include('layervfrac_group'),
            #		Item('simulation_traits', show_label=False),
            layout='split')
    )



if __name__ == '__main__':
    LayerSimulation().configure_traits()