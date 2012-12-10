import sys, os
from traits.api import * 
from traitsui.api import *
from numpy import array, empty
import matplotlib.pyplot as plt
from interfaces import IMaterial, ISim
from numpy import linspace, divide, savetxt
import copy
from simulationplots import ReflectanceStorage, ScattStorage, MaterialStorage
from main_parms import SpecParms
from layer_editor import LayerEditor
import time
from traits.trait_base import xsetattr, xgetattr

from pandas import concat, Panel

class SimObject(HasTraits):
    '''Basic editor for editing traits and values in these simulations, an adapter basically.  Stores an array for
       incremental updating.'''
    trait_name=Str('add trait name')
    inc=Range(low=0,high=20,value=3)
    start=Float(0.0)
    end=Float(0.5)
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

    start=Button
    time=Str('Sim not started')   #Stores time that simulation ended
    outname=Str('Testsim') #Output name, can be overwritten when output called

    outpanel=Instance(Panel)
    implements(ISim)
    inc=Range(low=0,high=20,value=3)
    

    notes=Str('Add description')

    key_title=Str('Trial')  #This is used to give each increment a name rather than 1,2,3
    key_delimiter=Str('%')	#Needed to put in this way to ensure proper sorting in simulationplots.py
    ## Also set to % in composite plots but that doesn't seem to be a problem

    base_app=Any  #THIS IS AN INSTANCE OF GLOBAL SCENE, ALL TRAITS WILL DELGATE TO THIS.  

    selected_traits=Instance(SimObject) 

    restore_status=Bool(True) #Restore all traits to original values after simulation is over

    sim_obs=List(SimObject)
    simulation_traits=Dict  #Dictionary of required trait names, with start, end values in tuple form for iteration.  For example "Volume": (13.2, 120.0)"
    sim_traits_list=Property(List, depends_on='simulations_traits')  #Only used for presenting a nice view to user
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
    def _get_sim_traits_list(self): return self.simulations_traits.keys()

    def _sim_obs_default(self): return []

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

    def runsim(self): pass

    def output_simulation(self, outpath, outname=None):
        ''' Method to output a data file with parameters, name and results so that it can be loaded back into this
            program, or easily read into my data analysis programs through a RunData interface class.  As of
            now, this program stores all the trait/sim data in the variable header.  The reflectance of each
            simulation is stored rowwise, with the xvalues being the first non commented row and data
            stored subsequently.  The choice to do this rowwise was because savetxt and loadtxt understand
            rowwise storage natively; however, because savetxt lacks a header feature in v 1.6, I decided
            to just turn the arrays to strings and output them as one big string (arraystring) '''

        wp_ext='.pickle' #.pickle 
        md_ext='.mdat'   #metadata

        if self.outpanel == None:
            print 'Cannot save simulation; outpanel trait is None.  Was a simulation run yet?'
            return

        if outname == None:
            outname=self.outname
        
        ### If outname has file extension, and its not pickle, convert it
        sout, ext=os.path.splitext(outname)
        if ext !='' and ext != wp_ext:
            print 'Dropping file extension %s, please dont use a file extension.'%ext
        outpanel=sout+wp_ext
        outmeta=sout+md_ext

        ### Save runpanel    
        outfile=os.path.join(outpath, outpanel)
        self.outpanel.save(outfile)
        
        ### Save metadata
        outfile=os.path.join(outpath, outmeta)
        with open(outfile, 'w') as o:
            o.write('Put some shit in here')
        
        print '\nSimulation %s saved\n'%outname
        
        



    def _start_fired(self): 
        self.runsim()
        if self.restore_status is True:
            self.restore_original_values()
        self.time=time.asctime( time.localtime(time.time()))

    basic_group=VGroup(
        HGroup(Item('restore_status'),Item('inc'), 
               Item('start', enabled_when='warning=="Simulation ready: all traits found"'), 
               Item('time', label='Sim Start Time', style='readonly')
               ),
        HGroup(
            Item('warning', style='readonly', label='Warning(s):'),Item('outname',label='Run Name'),
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

    ## Need to make a way for the plot types to be modular.  For example, I can pipe a scatt plot out or
    ## a reflectance plot, but this program needs to recognize that scattering plots only exist
    ## for nanoparticle objects for example

    ### Non modular adhoc solution 4_21


#	def _R_list_default(self):=return SimViewList(trials_delimiter=self.key_delimiter)      #Stores reflectance plots per iteration
    def _R_list_default(self): return ReflectanceStorage(trials_delimiter=self.key_delimiter)
    def _M_list_default(self): return MaterialStorage(trials_delimiter=self.key_delimiter)

    ### AdHoc ###
    def _Scatt_list_default(self): return ScattStorage(trials_delimiter=self.key_delimiter)
    
    def _outname_default(self): return 'Layersim'

    def _selected_material_changed(self): self.update_storage()

    def _sim_obs_default(self):
        obs=[]
    #	obs.append(SimObject(trait_name='selected_material.Vfrac', start=0.0, end=0.32, inc=self.inc)),  
    #	obs.append(SimObject(trait_name='selected_material.TotalMix.r_shell', start=0.0, end=10, inc=self.inc)),
        obs.append(SimObject(trait_name='selected_material.r_shell', start=0.0, end=10.0, inc=self.inc)),
        return obs 

    def runsim(self): 
        svl_dic={}  #Dictionary that stores relevant data by variable
        mvl_dic={}
        scatt_dic={}
        
        paneldic={}

        for i in range(self.inc):
            for trait in self.simulation_traits.keys():
                xsetattr(self.base_app, trait, self.simulation_traits[trait][i]) #Object, traitname, traitvalue
            key=self.key_title+self.key_delimiter+str(i)

            ### Update relavent methods in case trait's i'm changing don't necessarily trigger these (for example coefficients of
            ### dispersion relation don't trigger a change in the shell of nanoparticles 

            self.selected_material.FullMie.update_cross()  #This is only in case the trait I'm simulating doesn't automatically trigger an update
            self.base_app.statedata.update_simview()         #Recompute Reflectance		

            ### STUPID HACK TO ALLOW SAMPLING OF SCATTERING CROSS SECTIONS BY WRITING THEM INTO NEW LISTS, THEN MAKING A LIST OF LISTS
            ### FOR SOME REASON, TRYING TO ADD THEM EXPLICITLY TO A DICTIONARY WOULD CAUSE ERRORS AFTER THE ITERATIONS!!!
            scatt_dic[key]=[]  #ext/abs/scattering arrays.
            for field in self.selected_material.FullMie.sview.get_sexy_data():
                new_data=[entry for entry in field]
                scatt_dic[key].append(new_data)

            mvl_dic[key]=self.selected_material.mview.get_sexy_data()     #Get Dielectric plots (Working fine)
            svl_dic[key]=self.base_app.statedata.simview.get_sexy_data()  #Get Reflecatance plots
            
            ### 12/9/12 Dataframes into panel for sim output ###
            mvl_df=self.selected_material.mview.get_dataframe()
            svl_df=self.base_app.statedata.simview.get_dataframe()  
            scatt_df=self.selected_material.FullMie.sview.get_dataframe()
            
            ### Concatenate rowwise
            paneldic[key]=concat([mvl_df, svl_df, scatt_df], axis=1)         

            print "Iteration\t", i, "\t of \t", self.inc, "\t completed"

        ### Make a full panel out of paneldic with trials as the items
        self.outpanel=Panel.from_dict(paneldic, orient='minor')

        ### Update old plotstorage dict objects
        self.Scatt_list.trials_dic=scatt_dic
        self.R_list.trials_dic=svl_dic
        self.M_list.trials_dic=mvl_dic

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