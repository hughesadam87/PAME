import copy, pickle, os
import logging

### Enthought imports
from traits.api import *
from traitsui.api import *
from enable.component_editor import ComponentEditor
from sim_traits import BasicReflectance
from basicplots import SimView
from layer_editor import LayerEditor
from main_parms import FiberParms, SpecParms
from interfaces import ISim, ILayer, IMaterial, IStorage
from fiberview import FiberView
from modeltree_v2 import Main
from gensim import LayerVfrac, GeneralSim
from handlers import WarningDialog

### Used to present a summary of the state of the program.   ###
###This may be deprecated or unuseful and is not all that important I think ###

# Reflectance/Mode summary (don't think its used; think its deprecated)
state_editor =\
    TableEditor(
        auto_size=False,  #Set in View
        columns=[
            # These are all sim_traits.BasicReflectance traits
            ExpressionColumn(expression='object.Mode', label='Fiber Mode'),
            ExpressionColumn(expression='object.angles', label='Angle'),
            ExpressionColumn(expression='object.stack', label='Stack'),
            ExpressionColumn(expression='object.ds', label='DS'),
            ExpressionColumn(expression='object.angle_avg', label='Averaging Style'),            
            ObjectColumn(name='sim_designator', label='State Designator'), #What ist his?
            ],
        deletable=False,
        selected='current_state',
        show_toolbar=True,
        row_height=1
    )

# Table stores simulations, top right.  Renders fine!
sims_editor=\
    TableEditor(
        auto_size=False,  #Set in View
        columns=[
            ObjectColumn(name='outname', label='Sim Name'),
            ExpressionColumn(expression='object.inc', label='Increments'),
            ExpressionColumn(expression='object.time', label='Start Time'),
            ObjectColumn(name='notes', label='Notes'),
            ],
        deletable=True,
        selected='selected_sim',
        show_toolbar=True,
        row_height=1,
    )


class GlobalScene(HasTraits):
    '''Global class to define all view-based stuff'''

    specparms=Instance(SpecParms,())
    fiberparms=Instance(FiberParms,())
    modeltree=Instance(Main,())
    lambdas=DelegatesTo('specparms')  #Actually not used except for making it easy to run sims

    fview=Instance(FiberView,())     #May want to pass specparms and fiberparms to this later if it requries them

    current_state = Instance(ISim)
    opticstate = Instance(ISim)

    save=Button
    load=Button
    refresh = Button  #FOR TESTING, DELETE AFTER DONE
    
    
    ## For simulations
    outdir=Directory 

    def _load_fired(self):
        self.simulations=pickle.load(open("test.p", "rb") )

    def _save_fired(self):
        pickle.dump(self.simulations , open( "test.p", "wb" ) )
        
    def _refresh_fired(self):
        print 'refresh fired'
        self.opticstate.update_simview()
        
    def _outdir_default(self):
        return os.path.join( os.path.abspath('.'),'Simulations')

    ####Simulation Stuff ####

    simulations=List(ISim)  
    selected_sim=Instance(ISim)

    ###Editors####
    layereditor=Instance(LayerEditor)
    stack= DelegatesTo('layereditor')               #Variables are stored here just because they can be useful for future implementations
    selected_layer = DelegatesTo('layereditor')
    selected_material=DelegatesTo('layereditor')
    selected_d=DelegatesTo('layereditor')
#    angle_avg=DelegatesTo('current_state')

    ####Stack Actions####
    showreflectance=Action(name="Interface View", action="compute_optics")  #PHASE THIS OUT LATER WITH UNIFIED VIEW FRAMEWORK
    appendsim=Action(name="Add Simulation", action="new_sim")
    savesim=Action(name="Save Selected Simulation", action="save_sim")  #action gets underscore
    savesim_all=Action(name="Save All Simulations", action="save_allsims")  #action gets underscore
    

    ### Make Menubar
    mainmenu=MenuBar(
        Menu(showreflectance, name='Layer Options'), 	
        Menu(appendsim, savesim, savesim_all, name='Simulation Options'), 	       
    )                      

    fibergroup=Group(
        # Angle_avg depends on the BasicReflectance
#        Item('angle_avg', label='Angle Averaging Method',show_label=False),
        Item('fiberparms', editor=InstanceEditor(), style='custom', show_label=False),
        Item('fview', style='custom', show_label=False),
        label='Fiber'
    )

    layergroup=Group(
        Item('layereditor', 
             editor=InstanceEditor(),
             style='custom', 
             show_label=False),
        label='Stack')  

    materialgroup=Group(
        Item('selected_material',
             editor=InstanceEditor(),
             style='custom',
             show_label=False),
        label='Material'
    )            

    summarygroup=Group(
        Item('simulations', editor=sims_editor, show_label=False),

        ### Can't remove this or program trips, so I just hide it permanently
        Item('opticstate', 
             editor=state_editor, 
             show_label=False, 
             visible_when='8==8'#always vis
             ),
        label='Parameter Summary'
    )

    simgroup=Group( Item('selected_sim', 
                         style='custom',
                         editor=InstanceEditor(),
                         show_label=False), 
                    label='Simulations')

    fullgroup=VSplit(
                HSplit(
                  VGroup(
                    Item('specparms',show_label=False, style='custom'),
                    Item('outdir', label='Output Directory'),
                    Item('refresh', label='REFRESH OPTICAL', show_label=False),                                         
                      ),
                    Include('summarygroup'),
                    ),
        Tabbed(
            Include('fibergroup'), 
            Include('layergroup'),
            Include('materialgroup'),
            Include('simgroup'),
            ),
           )

    Mainview = View(Include('fullgroup'), 
             #       Item('save'), Item('load'),  #FOR SAVING ENTIRE STATE OF SIMULATION
                    menubar=mainmenu,
                    resizable=True, 
                    buttons=['Undo'], 
                    title='Plasmonic Assay Modeling Environment')

    def __init__(self, *args, **kwargs):
        super(GlobalScene, self).__init__(*args, **kwargs)
        self.layereditor=LayerEditor()
        self.sync_trait('specparms', self.layereditor, 'specparms')
        self.sync_trait('modeltree', self.layereditor, 'modeltree')

        ### NEED TO RENAME AND REWRITE THIS... ITS NOT "opticstate"
        self.opticstate=BasicReflectance()
        self.sync_trait('specparms', self.opticstate, 'specparms')
        self.sync_trait('fiberparms', self.opticstate, 'fiberparms')
        self.sync_trait('layereditor', self.opticstate, 'layereditor')

      #self.simulations.append(LayerVfracEpsilon(base_app=self))   #Pass self to a simulation environment
        self.simulations.append(LayerVfrac(base_app=self, outname='Layersim0'))   #Pass self to a simulation environment
        
    ### Store copy of current simulation 
    def new_sim(self): 
        self.simulations.append(LayerVfrac(base_app=self, outname='Layersim'+str(len(self.simulations))))
    
    def save_sim(self): 
        self.selected_sim.output_simulation(self.outdir)
    
    def save_allsims(self):
        ''' Saves all stored simulations in the sims_editor.  Checks for duplicate names and non-run/incomplete
        simulations and prompts user accordingly.'''

        ### Check to make sure all simulations have completed data
        unrun=[s.outname for s in self.simulations if s._completed == False]   
        nrunstring=' '.join(unrun)
        if len(unrun) > 0:
            message('Cannot save simulations:  %s. Results not found.'%nrunstring, title='Warning')
            ### Can't save either way, so force exit instead of user being able to continue
            return               
        
        ### Check for duplicate runnames        
        rnames=[s.outname for s in self.simulations]        
        non_uniq=[r for r in rnames if rnames.count(r) > 1]
        if len(non_uniq) > 0:
            non_uniq=list(set(non_uniq))
            nustring=' '.join(non_uniq)
      
            message('Duplicate simulation outfile names found: %s.'%nustring, title='Warning')
            return        
        
        ### Output completed simulations
        outsims=[s for s in self.simulations if s not in unrun]
        for s in outsims:
            s.output_simulation(self.outdir, confirmwindow=False)
        message('%s simulation(s) saved to directory: "%s"'%(len(outsims),
                  os.path.split(self.outdir)[1]), title='Success')

    ### Show Reflectance ###
    def compute_optics(self):
    #	self.opticstate.update_R()   #FOR SOME REASON EVEN THOUGH I UPDATE THE STACK WHEN LAYERS ARE CHANGED, IT ONLY UNDERSTANDS WHEN LAYERS ARE REMOVED ORA DDED
        print 'showing reflectance'
        self.opticstate.update_simview()
        self.opticstate.simview.edit_traits(view='view2')
    #	pass

def main():
    # HACK FOR DEBUG UNTIL DATA CAN BE IMPORTED CORRECTLY
    # os.chdir('/home/glue/Desktop/fibersim')
    
    
    popup=GlobalScene()
#    popup.opticstate.update_simview() #Necessary?
    popup.configure_traits()    
    
    

if __name__ == '__main__':
    main()

