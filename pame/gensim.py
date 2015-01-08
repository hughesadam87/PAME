''' Simulation program. '''

### Python imports
import sys, os
import time
import copy

### ETS imports
from traits.api import * 
from traitsui.api import *
from numpy import linspace, divide, savetxt
from traits.trait_base import xsetattr, xgetattr

###3rd party imports
from pandas import concat, Panel
from numpy import array, empty
import matplotlib.pyplot as plt

### Local imports
from handlers import FileOverwriteDialog, BasicDialog
from simparser import SimParser
from simulationplots import ReflectanceStorage, ScattStorage, MaterialStorage
from main_parms import SpecParms
from interfaces import IMaterial, ISim
from layer_editor import LayerEditor


class SimObject(HasTraits):
    """Basic editor for editing traits and values in these simulations, an adapter basically.  
    Stores an array for incremental updating.
    """
    trait_name=Str('add trait name')
    # THESE VALUES ARE SET WHEN BY CLASSES THAT CONTROL THE SIMS
    inc=Int() 
    start=Float()
    end=Float()
    trait_array=Property(Array, depends_on='start, end, inc')

    @cached_property
    def _get_trait_array(self): 
        ''' Reserves an array large enough to store all the values that the traits will take on when incremented.  For example,
            if iterating between 1,10 by steps of 1, it will store 10 slots '''
        try:
            return linspace(self.start, self.end, self.inc)
        except TypeError:  #Caused by unicode input which seems to happen spontaneously for an unknown reason
            return

class GeneralSim(HasTraits):
    '''Basic simulation for iterating over sets of variables that can be incremented over a shared increment.
       Contains methods to make sure traits that are being iterated over exist, and can be restored easily.  
       Simulation variables can be added quickly by changing the simulation_traits attributed'''

    base_app=Any  #THIS IS AN INSTANCE OF GLOBAL SCENE, ALL TRAITS WILL DELEGATE TO THIS.  

    start=Button
    time=Str('Sim not started')   #Stores time that simulation ended
    outname=Str('Testsim') #Output name, can be overwritten when output called
    outdir=DelegatesTo('base_app')

    implements(ISim)
    inc=Range(low=1,high=20,value=1)

    notes=Str('<NOTES GO HERE>')

    key_title=Str('Trial')  #This is used to give each increment a name rather than 1,2,3
    key_delimiter=Str('_')	#Needed to put in this way to ensure proper sorting in simulationplots.py
    ## Also set to % in composite plots but that doesn't seem to be a problem

    ### Restore all traits to original values after simulation is over
    restore_status=Bool(True) 

    ### Used to store most common simulation names in a user-readable fashion, Enum for dropdown list.
    translator=Dict()
    translist=Property(List, depends_on='translator')
    tvals=Enum(values='translist')

    ### Output Storage Objects
    outpanel=Instance(Panel) 
    _completed=Property(Bool, depends_on='outpanel') #Used to track if simulation is run
    csvout=Bool(True)  
    sparser=Instance(SimParser)

    ### Table for selecting objects
    selected_traits=Instance(SimObject) 

    sim_obs=List(SimObject)
    simulation_traits=Dict  #Dictionary of required trait names, with start, end values in tuple form for iteration.  For example "Volume": (13.2, 120.0)"
    sim_traits_list=Property(List, depends_on='simulation_traits')  #Only used for presenting a nice view to user
    original_values=Dict
    missing_taits=List
    warning=Str

    simeditor =\
        TableEditor(
            columns=[
                ObjectColumn(name='trait_name', label='Trait Name'),         #Add these in general sim class
                ObjectColumn(name='start', label='Start Value'),
                ObjectColumn(name='end', label='End Value'),
                ],
            deletable   = True, 
            auto_size = True,
            orientation='vertical',    #Orientation between built-in split between table and edit view
            show_toolbar=True,
            selected           = 'selected_traits',   #String name is arbitrary and passed as a global variable to other instances
            selection_color    = 0x000000,
            selection_bg_color = 0xFBD391,
            row_factory=SimObject
        )

    @cached_property
    def _get_sim_traits_list(self): 
        return self.simulation_traits.keys()

    def get_usefultraits(self):
        '''Method for returning parameters/metadata about the simulation'''
        return {'Simulation Name':self.outname, 
                'Steps':self.inc, 
                'Run Time':self.time, 
                'Run Notes':self.notes,
                'Simulated Traits':self.sim_traits_list
                }

    def get_alltraits(self):
        ''' Aggregates all interesting simulation-wide parameters for output'''
        dic={}
        ### Keys must be single string for correct attribute promotion if desirable ###
        dic['Simulation_Parameters'] = self.get_usefultraits()
        dic['Selected_Material_Parameters'] = (self.base_app.selected_material.get_usefultraits())
        dic['Spectral_Parameters'] = (self.base_app.specparms.get_usefultraits())
        dic['Fiber_Parameters'] = (self.base_app.fiberparms.get_usefultraits())
        ### Layer editor is already KEY:List, so already has proper heirarchy
#	dic.update(self.base_app.layer_editor.get_usefultraits())
        return dic


    def _tvals_changed(self): 
        ''' Set current layer from the name translator for more clear use. '''	
        self.selected_traits.trait_name=self.translator[self.tvals]

    ### Need to make a class tot
    def _get_translist(self): 
        return self.translator.keys()  

    def _get__completed(self):
        if self.outpanel == None:
            return False
        else:
            return True

    def _sim_obs_default(self): 
        return []

    @on_trait_change('inc, selected_traits')  #Updates with user selection, for some reason selected_traits.start, selected_traits.end notation not makin a difference
    def update_storage(self):
        '''Method to update various storage mechanisms for holding trait values for simulations.  
           Takes user data in table editor and stores it in necessary dictionaries so that 
           traits can be set and things automatically.  Decided to use this over a system
           properties because the properties were conflicting with delegation and other stuff'''
        sim_traits={};originals={}; missing=[]; warning=''

        for obj in self.sim_obs:
            obj.inc=self.inc  #Ensures proper increments whether adding new objects to the table or just changing global inc

        for obj in self.sim_obs:
            sim_traits[obj.trait_name]=obj.trait_array        #Simulation traits

        for key in sim_traits.keys():
            try:
                originals[key]=xgetattr(self.base_app, key)  #If trait found, store its original values
            except AttributeError:
                missing.append(key)  #If not, put it in missing

        if len(missing) > 0:
            warning='Could not find required traits:'
            for trait in missing:
                warning=warning+'\t'+trait + '\t'
        else:
            warning='Simulation ready: all traits found'
        self.simulation_traits=sim_traits
        self.warning=warning
        self.missing_traits=missing
        self.original_values=originals

    def restore_original_values(self): 
        for trait in self.simulation_traits.keys():
            xsetattr(self.base_app, trait, self.original_values[trait]) #Restore all traits to original values

    def runsim(self): 
        pass

    def output_simulation(self, outpath=None, outname=None, confirmwindow=True):
        ''' Output simulation into a SimParser object and save.  Simparser object is then suited
        for integration with pylab/pyuvvis, or also can be read internally by fibersim plotting tools.

            outpath: must be passed in by calling class.
            outname: if not passed, self.outname will be used.
            confirmwindow:  Popup message on successful save'''

        md_ext='.mdat'   #metadata extensions

        ### Make sure simulation has taken place
        if self.outpanel is None:
            message('Cannot save simulation, %s, outpanel trait is None. \
	    Perhaps simulation was not run yet?'%self.outname, title='Warning')
            return

        ### If no explicitly passed, outname and outpath delegate to stored defaults
        if outname is None:
            outname=self.outname
        else:
            self.outname=outname  #Not sure if I'll ever use, but useful for overwriting

        if outpath is None:
            outpath=self.outdir #delegate from base_app

        ### If outname has file extension, and its not pickle, convert it
        sout, ext=os.path.splitext(outname)
        if ext !='' and ext != md_ext:
            message('Dropping file extension %s, please enter a root filename.'%ext, title='Warning')
        outdata=sout+md_ext

        ### Ceck for file overwriting    
        outfile=os.path.join(outpath, outdata)
        if os.path.exists(outfile):
            test=FileOverwriteDialog(filename=outfile)
            ui=test.edit_traits(kind='modal')
            ### break out and don't save###
            if ui.result==False:
                return

        ### Translator is actually reversed in scope of use in simparser
        trans_rev=dict((v,k) for k,v in self.translator.items())

        ### Assign proper traits (avoid delegation because that class needs to stand alone)  
        self.sparser=SimParser(translator=trans_rev, results=self.outpanel,
                               simparms=self.simulation_traits, parms=self.get_alltraits())

        ###Save entire object
        self.sparser.save(outfile)

        if confirmwindow==True:
            message('Simulation data saved to file %s'%outdata, title='Success')


    def _start_fired(self): 
        self.runsim()
        if self.restore_status is True:
            self.restore_original_values()
        self.time=time.asctime( time.localtime(time.time()))

    basic_group=VGroup(
        HGroup(Item('restore_status', label='Restore state after simulation' ),
               Item('inc',label='Steps'), 
               Item('start', enabled_when='warning=="Simulation ready: all traits found"', show_label=False), 
               Item('time', label='Sim Start Time', style='readonly'), 
               Item('tvals', label='Common traits'),
               ),
        HGroup(
            Item('outname',label='Run Name'), Item('warning', style='readonly', label='Warning(s):'),
            ),
        Item('sim_obs', editor=simeditor, show_label=False),
        Item('notes', style='custom'),
        label='Parameters')


class LayerVfrac(GeneralSim): 

    ######## New variables specific to this simulation ###########

    R_list=Instance(ReflectanceStorage)  #Defaulted below
    M_list=Instance(MaterialStorage) #Stores dielectric plots per iteration
    Scatt_list=Instance(ScattStorage)  
    selected_material=DelegatesTo('base_app') #Just for convienence in variable calling
    selected_layer=DelegatesTo('base_app')

    ## Need to make a way for the plot types to be modular.  For example, I can pipe a scatt plot out or
    ## a reflectance plot, but this program needs to recognize that scattering plots only exist
    ## for nanoparticle objects for example


    def _translator_default(self):	
        return{'Layer Fill Fraction':'selected_material.Vfrac',
               'Layer Thickness':'selected_layer.d',
               'NP Core radius':'selected_material.r_core',
               'NP Shell Fill Fraction':'selected_material.CoreShellComposite.Vfrac' }

#	def _R_list_default(self):=return SimViewList(trials_delimiter=self.key_delimiter)      #Stores reflectance plots per iteration
    def _R_list_default(self): 
        return ReflectanceStorage(trials_delimiter=self.key_delimiter)

    def _M_list_default(self): 
        return MaterialStorage(trials_delimiter=self.key_delimiter)

    ### AdHoc ###
    def _Scatt_list_default(self): 
        return ScattStorage(trials_delimiter=self.key_delimiter)

    def _outname_default(self): 
        return 'Layersim'

    def _selected_material_changed(self): self.update_storage()

    def _sim_obs_default(self):
        ''' Initial traits to start with '''
        obs=[]
        obs.append(SimObject(trait_name='selected_material.Vfrac', start=0.0, end=0.1, inc=self.inc)),  
        obs.append(SimObject(trait_name='selected_layer.d', start=50., end=100., inc=self.inc)),
        obs.append(SimObject(trait_name='selected_material.r_core', start=25., end=50., inc=self.inc)),
        return obs 

    def runsim(self): 

        ### At some point, make better interface to return all this stuff together into the paneldic
        svl_dic={}  #Dictionary that stores relevant data by variable
        mvl_dic={}
        scatt_dic={}

        paneldic={}

        sorted_keys = []
        for i in range(self.inc):
            for trait in self.simulation_traits.keys():
                xsetattr(self.base_app, trait, self.simulation_traits[trait][i]) #Object, traitname, traitvalue
#            key=self.key_title+self.key_delimiter+str(i)
            key = '%s_%s' % (str(i), self.key_title)
            sorted_keys.append(key)

            ### Update relavent methods in case trait's i'm changing don't necessarily trigger these (for example coefficients of
            ### dispersion relation don't trigger a change in the shell of nanoparticles 

            self.selected_material.FullMie.update_cross()  #This is only in case the trait I'm simulating doesn't automatically trigger an update
            self.base_app.opticstate.update_opticview()         #Recompute Reflectance		

            ### STUPID HACK TO ALLOW SAMPLING OF SCATTERING CROSS SECTIONS BY WRITING THEM INTO NEW LISTS, THEN MAKING A LIST OF LISTS
            ### FOR SOME REASON, TRYING TO ADD THEM EXPLICITLY TO A DICTIONARY WOULD CAUSE ERRORS AFTER THE ITERATIONS!!!
            scatt_dic[key]=[]  #ext/abs/scattering arrays.
            for field in self.selected_material.FullMie.sview.get_sexy_data():
                new_data=[entry for entry in field]
                scatt_dic[key].append(new_data)

            mvl_dic[key]=self.selected_material.mview.get_sexy_data()     #Get Dielectric plots (Working fine)
            svl_dic[key]=self.base_app.opticstate.opticview.get_sexy_data()  #Get Reflecatance plots

            ### 12/9/12 Dataframes into panel for sim output ###
            mvl_df=self.selected_material.mview.get_dataframe()
            svl_df=self.base_app.opticstate.opticview.get_dataframe()  
            scatt_df=self.selected_material.FullMie.sview.get_dataframe()

            ### Concatenate rowwise
            paneldic[key]=concat([mvl_df, svl_df, scatt_df], axis=1)         

            print "Iteration\t", i+1, "\t of \t", self.inc, "\t completed"

        ### Make a full panel out of paneldic with trials as the items
        
        print 'HI SAVING PANELDIC'
        self.outpanel = Panel.from_dict(paneldic, orient='minor')
        print sorted_keys
        self.outpanel = self.outpanel.reindex_axis(sorted_keys, 
                                                   axis=2, #minor axis 
                                                   copy=False)
        print sorted_keys
        print self.outpanel
        print 'SAVING PANELDIC FINISHED'

        ####################################
        ### DEPRECATE #####################
        ### Update old plotstorage dict objects
        ###################################
        #self.Scatt_list.trials_dic=scatt_dic
        #self.R_list.trials_dic=svl_dic
        #self.M_list.trials_dic=mvl_dic

        ### Prompt user to save?
        popup=BasicDialog(message='Simulation complete.  Would you like to save now?')
        ui=popup.edit_traits(kind='modal')
        if ui.result == True:
            self.output_simulation()

    ####################################
    ### This view is for interactive plotting simulations
    ####################################
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
    LayerVfrac().configure_traits()