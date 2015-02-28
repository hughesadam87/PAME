""" Simulation program. """

# Python imports
import sys
import os.path as op
import time
import copy
from collections import OrderedDict
from pame import globalparms
import textwrap

# ETS imports
from traits.api import * 
from traitsui.api import *
from numpy import linspace, divide, savetxt
from traits.trait_base import xsetattr, xgetattr

#3rd party imports
from pandas import concat, Panel
from numpy import array, empty

# Local imports
from handlers import FileOverwriteDialog, BasicDialog
from simulationplots import ReflectanceStorage, ScattStorage, MaterialStorage
from main_parms import SpecParms
from interfaces import IMaterial, ISim
#from layer_editor import StackError
import config
import hackedvtree
import customjson
import utils
from layer_editor import SHARED_LAYEREDITOR
from simparser import LayerSimParser

WRAPWIDTH = 100 # Text characters for wrapping lines

class StackError(Exception):
    """ """

class SimError(Exception):
    """ """

class SimAdapter(HasTraits):
    """Shows selected simulation in table on main view.  Maps name shortcuts
    like layer1.material to actual storage of 'b_app.stack[1]'
    """
    trait_name = Str('add trait name')
    trait_name_full = Property(Str, depends_on = 'trait_name')
    trait_array=Property(Array, depends_on='start, end, inc')
    # THESE VALUES ARE SET WHEN BY CLASSES THAT CONTROL THE SIMS
    inc=Int() 
    start=Float()
    end=Float()
    
    def _get_trait_name_full(self):
        """ Given a name like layer1.material, maps it to the true dept of
        b_app object like b_app.stack[1].material.  Intended to be used by
        ABCSim, which will call this on b_app, so relative to base_app.
        """
        prefix = self.trait_name.split('.')[0].lower()
        #substrate, solvent or layer_1, Layer2 etc... go to layereditor
        if prefix in ['substrate', 'solvent'] or prefix.startswith('layer'):
            return 'layereditor.%s' % self.trait_name
     
        elif prefix.startswith('material'):
            # material1 ---> layereditor.layer1.material
            mat_index = prefix.lstrip('material_') #Works with _ or no _
            
            # This will update in real time as user types, so if user type
            # material but doesn't have time to type integer, prevents a 
            # crash.  
            try:
                mat_index = int(mat_index)
            except ValueError:
                pass # return self.trait_name
            else:
                suffix = '.'.join(self.trait_name.split('.')[1::]) #ie .Vfrac
                return 'layereditor.layer%s.material.%s' % (mat_index, suffix)

        return self.trait_name
            

    def _get_trait_array(self): 
        """ Reserves an array large enough to store all the values that the
        traits will take on when incremented.  For example,
        if iterating between 1,10 by steps of 1, it will store 10 slots """
        try:
            return linspace(self.start, self.end, self.inc)
        except TypeError:  #Caused by unicode input which seems to happen spontaneously for an unknown reason
            return

# ADD SAVE/LOAD UBTTONS
class SimConfigure(HasTraits):
    """ Configuration what is stored/output in simulation."""

    save = Button
    outpath = File

    _opticalmessage_p1 = Str
    _opticalmessage_p2 = Str
    _layermessage_p1 = Str    
    _layermessage_p2 = Str
    _grabbutton = Button

    # Used to store most common simulation names in a user-readable fashion, Enum for dropdown list.
    translator=Dict()
    translist=Property(List, depends_on='translator')
    traitscommon=Enum(values='translist')

    # Summary storage
    averaging = Enum('Average', 'Not Averaged', 'Both')

    #https://github.com/enthought/traitsui/blob/master/examples/demo/Standard_Editors/CheckListEditor_simple_demo.py
    #http://stackoverflow.com/questions/23650049/traitsui-checklisteditor-changing-the-case-of-values?rq=1 
    choose_optics = List(editor=CheckListEditor(values = globalparms.header.keys(),  
                                                cols=5), 
                         #format_func=lambda x: x.lower(), #<-- no works
                         value=globalparms.selected)
    _ignoreme = Property(List, depends_on='choose_optics')

    # DONT CHANGE VALUE OF THESE, VISIBILITY TRAITS AND SO FORTH DEPEND ON EXACT NAMES/CASE
    choose_layers = Enum('None', 'Selected Layer', 'All Layers')
    mater_only = Enum('Material Data', 'Material and Layer Metadata')
    additional = Str()
    additional_list = Property(List, depends_on = 'additional, traitscommon')

    # Simulation object to be stored
    store_optical_stack = Bool(False)

    traits_view = View(
        Group(
            VGroup(
                Item('_opticalmessage_p1', show_label=False, style='readonly'),
                Item('averaging', style='custom', label='Angle Averaging', show_label=False),
                Item('_'), #Gap
                Item('choose_optics', style='custom', label='Optical Quantities', show_label=False),
                Item('_opticalmessage_p2', show_label=False, style='readonly'),
                Item('store_optical_stack', show_label=False, label='copy'),      
                label='Optics'
                ),

            VGroup(
                Item('_layermessage_p1', show_label=False, style='readonly'),
                HGroup(
                    Item('traitscommon', label='Common'),
                    Item('_grabbutton', label='Browse', show_label=False)
                    ),
                Item('additional', 
                     style='custom',
                     show_label=False,
                     label='<font color="red">Top-level Traits </font>'),
                Item('_layermessage_p2', show_label=False, style='readonly'), 
                HGroup(
                    Item('choose_layers', style='custom', show_label=False, label='Deep Copy'),
                    Item('mater_only', label='Store', visible_when='choose_layers != "None"')
                    ),
                label='Multilayer Stack'              

                ),
            layout='tabbed'),
        buttons = [ 'OK', 'Cancel' ],#'Undo]
    )       
    
    def _choose_layers_default(self):
        return 'Selected Layer'

    def _get__ignoreme(self):
        """ Weird BUG where choose_optics (as defined) doesn't save when 
        simulation requested, so if I make a regular list without defining
        a checklist editor, it just works..."""
        return [i for i in self.choose_optics]

    def _justwrapit(self, text, width=WRAPWIDTH):
        """ Wrap long lines of text to WRAPWIDTH"""
        return '\n'.join(textwrap.wrap(text, width=width))

    # Can't put a newline character before a <font> statment (after is ok), so can't 
    # color code any of this text.
    def __opticalmessage_p1_default(self):
        return self._justwrapit('Select which optical quantities (Reflectance, Transmittance etc...) '
                                'the simulation should store for immediate access when parsing.  Choose to average '
                                'over the angles or to store each quantity at every angle.  For example, for '
                                'three angles, should simulation will output R_1, R_2, R_3 or R_Avg or both?')


    def __opticalmessage_p2_default(self):
        return self._justwrapit('Check the box below and a deep copy of the full optical stack will store the '
                                'unaltered optical quantites in their original, unparsed form for each step of the '
                                'iteration.  This will add appreciably to the size of the saved simulation file.')


    def __layermessage_p1_default(self):
        return self._justwrapit('Choose Material quantites like index of refraction and nanoparticle scattering'
                                ' cross section to be stored for immediate access when parsing.  For example,'
                                '<selected_material.FullMie.Cscatt> stores the scattering cross section of a nanoparticles for a selected material.'
                                ' Some common ones are provided, or browse through the full stack.')


    def __layermessage_p2_default(self):
        return self._justwrapit('In addition to the material you selected for primary storage, the simulation'
                                ' will store many other material attributes which can be accessed by a'
                                ' parser.  Should the simulation store these for layers of the dielectric slab?'
                                ' For just the selected layer, or None?  For each layer, store the material only,'
                                ' or store all metadata about the layer?')

    def __grabbutton_fired(self):
        """ Launch Browser to view traits """
        browser = hackedvtree.ArrayBrowser(traits_tree=SHARED_LAYEREDITOR.stack)
        browser.edit_traits()#kind='modal') #Modal may be necessary when select works
        #foo = browser.configure_traits(kind='modal')
        #common_traits.append(foo.selected)

    def simulation_requested(self):
        """ Return config parameters, will end up in the 'About' portion of
        the simulation dictionary.
        """
        return OrderedDict((k,v) for k,v in \
                           [('Optical Quantities',self._ignoreme),
                            ('Angle Averaging', self.averaging),
                            ('Copy Full Optical Stack', self.store_optical_stack),
                            ('Layer Quantities', self.additional_list),
                            ('Deep Layer Storage', self.choose_layers),
                            ('Layer Storage Style', self.mater_only)
                            ])

    def _get_additional_list(self):
        """ User adds custom traits to additional box, deliminted by newline.
        This removes unicode and returns as a list like:
         [material1.trait1, material2.foo.trait5] etc...
         """
        out = [str(s) for s in self.additional.strip().split('\n') if s] #<-- blank string
        return list(set(out))  #<-- remove duplicates

    def _translator_default(self):	
        # Make ordered dict       
        return {          
            'Selected Layer Dielectric Function':'selected_material.earray',
            'Selected Layer Index of Refraction':'selected_material.narray',
            'Selected Layer Extinction Cross Section (NanoMaterials Only)':'selected_material.FullMie.Cext',
            'Selected Layer Scattering Cross Section (NanoMaterials Only)':'selected_material.FullMie.Cscatt',
            'Selected Layer Absorbance Cross Section (NanoMaterials Only)':'selected_material.FullMie.Cabs',
             }

    def _traitscommon_changed(self): 
        """ Set current layer from the name translator for more clear use. """	
        self.additional += self.translator[self.traitscommon]+'\n' #String

    def _get_translist(self): 
        return self.translator.keys()      


class ABCSim(HasTraits):
    """Basic simulation for iterating over sets of variables that can be incremented over a shared increment.
       Contains methods to make sure traits that are being iterated over exist, and can be restored easily.  
       Simulation variables can be added quickly by changing the simulation_traits attributed"""

    base_app=Any  #THIS IS AN INSTANCE OF GLOBAL SCENE, ALL TRAITS WILL DELEGATE TO THIS.  

    configure_storage = DelegatesTo('base_app') #Instance SimConfiguration

    start = Button
    time = Str('(not started)')   #Stores time that simulation ended
    outname = Str('Testsim') #Output name, can be overwritten when output called
    sim_outdir = DelegatesTo('base_app')

    browse_numerics = Button # Browse avaialable numeric traits for sim

    save_as = Enum(config.SIMEXT, '.json')

    implements(ISim)
    inc=Range(low=1,high=config.MAXSTEPS,value=10) # Need as range for now I think

    notes=Str('<ADD NOTES ON SIMULATION>')

    key_title=Str('step')  #This is used to give each increment a name rather than 1,2,3

    # Select input variables/traits from human-readable dropdown list
    translator = Dict()
    translist = Property(List, depends_on='translator')
    tvals = Enum(values='translist')

    # Output Storage Objects
    primary = Dict
    results = Dict            
    static = Dict
    allstorage = Property(Dict) # Stores all four dicts plus metadata bout self
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
                ObjectColumn(name='trait_name', label='Parameter'),         #Add these in general sim class
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

    selection_group = Group(
        HGroup(
            Item('inc',label='Steps'), #<-- make me nicer after wx works           
            Item('tvals',
                 visible_when='selected_traits is not None', #<-- Should always be selected, but not in qt
                 label='Selected Layer Common Traits'),
            Item('browse_numerics', 
                 show_label=False,
                 label='Browse',
                 visible_when='selected_traits is not None'),
            
            ),       
        # sim_variables is actual table list of traits
        Item('sim_variables', editor=simeditor, show_label=False),
        HGroup(
            Item('restore_status', label='Restore program state after run' ),                
            Item('time', label='Start Time', style='readonly'), 
            ),
        label = 'Selection') 

    notesIO_group = Group(
        # Outdirectory
        HGroup(
            Item('outname',label='Run Name'),   
            Item('save_as',label='ext'),
            Item('sim_outdir', label='directory'),
            ),
        Item('notes',
             style='custom',
             show_label=False),

        label='Notes/IO')

    storage_group = Group(
        Item('configure_storage', 
             style='custom',
             label='Configure Storage',
             show_label=False),                          
        label='Storage')   

    maingroup = Group(
        Include('selection_group'),
        Include('notesIO_group'),
        Include('storage_group'),
        layout='tabbed'
    )    

    def _browse_numerics_fired(self):
        browser = hackedvtree.NumericBrowser(traits_tree=self.base_app.stack)
        browser.edit_traits()#kind='modal') #Modal may be necessary when select works
        #foo = browser.configure_traits(kind='modal')
        #common_traits.append(foo.selected)        
        

    def simulation_requested(self):
        """Method for returning parameters/metadata about the simulation"""
        storage = self.configure_storage.simulation_requested()
        return OrderedDict([(k,v) for k,v in 
                            ('Simulation Name',self.outname), 
                            ('Steps',self.inc), 
                            ('Time/Date',self.time), 
                            ('Notes',self.notes),
                            #Storage objects stored in SimConfigure 
                            # XX IMPORTANT XX
                            ('Storage',storage)
                            ])


    def _tvals_changed(self): 
        """ Set current layer from the name translator for more clear use. """	
        self.selected_traits.trait_name = self.translator[self.tvals]
        self.check_sim_ready() #<-- When user changes simulation traits table

    # a class tot
    def _get_translist(self): 
        return self.translator.keys()  

    def _get__completed(self):
        """ Inspect storage objects and infer if simulation ran successfully.  Basically
        tests if self.results, primary and self.static are all empty.  After successfully 
        completed run_sim(), at least one of these should be populated.  Actually they all 
        should, but in some instances, users can select settings that make these empty.  Like
        if user doesn't want to store anything in the top-level primary.
        """
        if self.results == {} and self.primary == {} and self.static == {}:
            return False
        return True

    def _sim_variables_default(self): 
        return []
    
    @on_trait_change('selected_traits.selected_sim, \
                      base_app.layereditor.selected_layer')
    def _checksim(self):
        self.check_sim_ready()

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
        
        # Retain a mapping between shortnames (layer1.material) and attr path
        # from base_app (layereditor.layer1) etc...
        _trait_name_map = dict((s.trait_name, s.trait_name_full) 
                                           for s in self.sim_variables)       
                
        for obj in self.sim_variables:
            obj.inc=self.inc  #Ensures proper increments whether adding new objects to the table or just changing global inc

        for obj in self.sim_variables:
            sim_traits[str(obj.trait_name)]=obj.trait_array        #Simulation traits
                       #^^^ Remove unicode

        for key in sim_traits.keys():
            _true_trait_val = _trait_name_map[key]
            try:
                originals[key]=xgetattr(self.base_app, _true_trait_val)  #If trait found, store its original values
            except (AttributeError, StackError):
                missing.append(key)  #If not, put it in missing

        ready = True

        # Are traits missing?
        if len(missing) > 0:
            status_message='<font color="red"> Could not find required input: </font>'
            status_message += ', '.join(missing)
            ready = False

        # Did user select duplicates of trait names
        trait_names = [obj.trait_name for obj in self.sim_variables]
        duplicates = set([name for name in trait_names if trait_names.count(name) > 1])
        if duplicates:
            status_message='<font color="red"> Duplicate simulation input(s) found: </font>'
            for trait in duplicates:
                status_message += trait + ',  '
            ready = False                        


        if ready:
            status_message='<font color="green"> Simulation ready: all input found</font>'
            ready = True

        self.ready = ready
        self.status_message = status_message.rstrip(',') #<-- trialling commas for list of one element string
        self.simulation_traits = sim_traits# Remove unicode
        self.missing_traits = missing
        self.original_values = originals
        
        self._trait_namemap = _trait_name_map
        

    def restore_original_values(self): 
        """ Restore all traits to original values """
        for trait in self.simulation_traits:
            xsetattr(self.base_app, 
                     self._trait_namemap[trait], #<--- Use actual variable name
                     self.original_values[trait])  

    def runsim(self): 
        """ ABC METHOD """
        pass

    def save(self):
        """ ABC METHOD """
        pass

    def _get_allstorage(self):
        """ Returns Ordered dict of dicts, where each dictionary is a primary storage dictionary:
        IE self.primary, self.results, self.static and self.simulation_requested(), where
        simuliation requested gives metadata like num steps, simulation etc.. about this 
        particular run.
        """ 
        allout = OrderedDict()
        allout['static'] = self.static
        allout['about'] = self.simulation_requested() #<-- bug: simulation_requested9
        allout['primary'] = self.primary
        allout['results'] = self.results      
        allout['inputs'] = self.simulation_traits
        return allout        


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

class LayerSimulation(ABCSim): 
    """ Simulate stack layer traits like selected material traits (ie d_core) and thickness
    of layer. Name is kind of arbitrary because this could simulate any Incremental trait.
    What it couldnt' do is change a value like polarization halfway through the simulation!
    """
    selected_material=DelegatesTo('base_app') #Just for convienence in variable calling
    selected_layer=DelegatesTo('base_app')

    traits_view=View(
        VGroup(
            HGroup( 
                Item('status_message', style='readonly', label='Status'),           
                Item('start', show_label=False), #, enabled_when='ready == True'),   
                # Making start invisible is bad, because clicking chart enforces stat
                ),
            Include('maingroup'),
        )
    )      

    def _outname_default(self): 
        return config.SIMPREFIX

    def _selected_material_changed(self):
        self.check_sim_ready()

    def _selected_layer_changed(self):
        self.check_sim_ready()

    def _translator_default(self):	
        """ Common traits for INPUTS TO simulation.  NOT THE SAME AS STORAGE!"""
        return {
            'Layer Fill Fraction':'selected_material.Vfrac',
            'Layer Thickness':'selected_layer.d',
            'NP Core radius (NanoMaterials Only)':'selected_material.r_core',
            'NP Shell Thickness (NanoShell Only)':'selected_material.shell_thickness',
            'NP Shell Fill Fraction (NanoShell Only)':'selected_material.ShellMaterial.Vfrac' 
             }


    def _sim_variables_default(self):
        """ Initial traits to start with """
        obs=[]
#        obs.append(SimAdapter(trait_name='selected_material.Vfrac', start=0.0, end=0.1, inc=self.inc)),  
        obs.append(SimAdapter(trait_name='selected_layer.d', start=10.0, end=20.0, inc=self.inc)),
#        obs.append(SimAdapter(trait_name='selected_material.r_core', start=25., end=50., inc=self.inc)),
        return obs 


    def runsim(self): 
        """ Increments, updates all results.  Thre primary storage objects:

        staticdict --> Traits that are no altered in simulation.  
           Includes simulation inputs, spectral parameters and fiber/strata
           parameters.  In future version, could relax these if needed
           to simulation over a fiber parameter like core size.

        primarydict --> Results that are to be promoted to top level.  
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
        sconfig = self.configure_storage 
        b_app = self.base_app

        # Storage
        primarydict = OrderedDict()   #<-- Keyed by increment, becomes primary panel!
        resultsdict = OrderedDict()   #<-- Keyed by increment, stores deep results, stays as dict

        # Traits not involved in simulation.  For this sim, includes spectral parameters, fiber/strata params
        # at simulation inputs.  Later sims may want to simulate over fiber traits (ie fiber diameter changes)
        # so would migrate these into resultsdict instead
        staticdict = OrderedDict()
        staticdict['Layers in Slab'] = len(b_app.stack)
        staticdict[globalparms.spectralparameters] = b_app.specparms.simulation_requested()         
        staticdict[globalparms.strataname] = b_app.fiberparms.simulation_requested()

        # Begin iterations
        sorted_keys = []
        for i in range(self.inc):
            for trait in self.simulation_traits.keys():
                _true_trait = self._trait_namemap[trait]#<--- Trait stored in memory (ie b_app.layereditor.layer1...)
                xsetattr(b_app, _true_trait, self.simulation_traits[trait][i]) #Object, traitname, traitvalue

            stepname = 'step_%s' % i

            primary_increment = OrderedDict()  #<--- Toplevel/Summary of just this increment (becomes dataframe)
            results_increment = OrderedDict()  #<--- Deep results of just thsi increment (ie selected_material/layer etc..)

            key = '%s_%s' % (str(i), self.key_title)
            sorted_keys.append(key)

            # Update Optical Stack
            b_app.opticstate.update_optical_stack() 

            # Flatten sim attributes.  For example, if attrs selected for Sim are R, A, kz
            # kz actually has value in each layer so R, A, kz_1, kz_2, kz_3 is what needs
            # to be iterated over.
            flat_attributes = []

            # How many layers in optical stack
            layer_indicies = range(len(b_app.opticstate.ns)) #0,1,2,3,4 for 5 layers etc...            

            for attr in sconfig.choose_optics:
                if attr in b_app.opticstate.optical_stack.minor_axis:
                    flat_attributes.append(attr)
                else:
                    # http://stackoverflow.com/questions/28031354/match-the-pattern-at-the-end-of-a-string
                    delim = '_%s' % globalparms._flat_suffix

                    # ['kz', 'vn', 'ang_prop']
                    setkeys = set(name.split(delim)[0] for name in 
                                  b_app.opticstate.optical_stack.minor_axis if delim in name)    
                    if attr in setkeys:
                        for idx in layer_indicies:
                            flat_attributes.append(attr + delim + str(idx)) #kz_L1 etc...)                   
                    else:
                        raise SimError('Cannot simulate over optical stack attr "%s" '
                                       ' not found in optical stack.' % attr)

            # --- PRIMARY RESULTS           
            # Take parameters from optical stack, put in toplevel via sconfig.choose_optics
            if sconfig.averaging in ['Average','Both']:
                for optical_attr in flat_attributes:
                    primary_increment['%s_%s' % (optical_attr, 'avg')] = \
                        b_app.opticstate.compute_average(optical_attr) #<-- IS NUMPY ARRAY, object type

            if sconfig.averaging in ['Not Averaged', 'Both']:
                for optical_attr in flat_attributes:
                    # ITERATE OVER ANGLES! SAVE EACH ANGLE
                    for angle in b_app.opticstate.angles:
                        primary_increment['%s_%.2f' % (optical_attr, angle)] = \
                            b_app.opticstate.optical_stack[angle][optical_attr]  #<-- Save as what, numpy/pandas?        

            # User-set dielectric slab quantites to be in primary
            for trait in sconfig.additional_list:
                traitval = xgetattr(b_app.layereditor, trait)
                primary_increment['%s' % trait]  = traitval

            # --- DEEP RESULTS
            # Store full Optical Stack
            if sconfig.store_optical_stack:
                results_increment[globalparms.optresponse] = b_app.opticstate.optical_stack

            # Save layer/material traits.  If None selected, it just skips
            if sconfig.choose_layers == 'Selected Layer':
                key = 'Layer%s' % (b_app.layereditor.selected_index) #<-- index of selected layer
                results_increment[key] = self.selected_layer.simulation_requested()

            elif sconfig.choose_layers == 'All Layers':
                materials_only = False
                if sconfig.mater_only == 'Material Data':
                    materials_only = True
                    
                results_increment['dielectric_layers'] = b_app.layereditor.simulation_requested(materials_only)


            # resultsdict >>  {step1 : {results_of_increment}, ...}
            resultsdict[stepname] = results_increment               
            primarydict[stepname] = primary_increment

            print "Iteration\t", i+1, "\t of \t", self.inc, "\t completed"

        # SET STORAGE TRAITS
        self.primary = primarydict
        self.results = resultsdict
        self.static = staticdict        

        # Prompt user to save?
        popup = BasicDialog(message='Simulation complete.  Would you like to save now?')
        ui = popup.edit_traits(kind='modal')
        if ui.result == True:
            self.save(confirmwindow=True)


    def save(self, outpath=None, confirmwindow=True):
        """ Output simulation into json dictionary, where four primary
        storage dictionaries (self.allstorage) are written to 
        numpy-aware json.  Errors and confirmation messages in form of
        popups are triggered.

        outpath: 
            Absolute save path.

        confirmwindow:
            Confirms simulation saved with popup window.
        """

        outpath = self._validate_extension(outpath, self.save_as)

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

        # Save json data
        if self.save_as == '.json':
            customjson.dump(self.allstorage, outpath)

        # Save .mpickle by opening simparser instance
        elif self.save_as == config.SIMEXT:
            obj = LayerSimParser(**self.allstorage)
            obj.save(outpath)

        else:
            raise SimError("Don't know how to save simulation of type %s!" % self.save_as)

        if confirmwindow == True:
            message('Simulation data saved to file %s' % outpath, title='Success')      


    def _validate_extension(self, outpath=None, extension=None):
        """ Validate a filepath extension.  If path has no file extension, 
        will add it.  If has a different one, will raise error.
        """
        if outpath is None:
            outpath = op.join(self.sim_outdir, self.outname)

        ext = op.splitext(outpath)[-1]
        if ext:
            if ext != extension:
                raise SimError('Simulation save path (%s) must have file extension %s' %
                               (outpath, extension) )
        # No file path
        else:
            outpath = outpath + extension
        return outpath


if __name__ == '__main__':
    LayerSimulation().configure_traits()