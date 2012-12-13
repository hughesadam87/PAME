import copy, pickle, os

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

### Used to present a summary of the state of the program.   ###
###This may be deprecated or unuseful and is not all that important I think ###

state_editor =\
    TableEditor(
        auto_size=False,  #Set in View
        columns=[
            ExpressionColumn(expression='object.Mode', label='Fiber Mode'),
            ExpressionColumn(expression='object.angles', label='Angle'),
            ExpressionColumn(expression='object.stack', label='Stack'),
            ExpressionColumn(expression='object.ds', label='DS'),
            ObjectColumn(name='sim_designator', label='State Designator'),
            ],
        deletable=False,
        selected='current_state',
        show_toolbar=True,
        row_height=1
    )


class GlobalScene(HasTraits):
    '''Global class to define all view-based stuff'''

    specparms=Instance(SpecParms,())
    fiberparms=Instance(FiberParms,())
    modeltree=Instance(Main,())
    lambdas=DelegatesTo('specparms')  #Actually not used except for making it easy to run sims

    fview=Instance(FiberView,())     #May want to pass specparms and fiberparms to this later if it requries them

    current_state = Instance(ISim)
    statedata = Instance(ISim)

    save=Button
    load=Button
    
    ## For simulations
    outdir=Directory 

    def _load_fired(self):
        self.simulations=pickle.load(open("test.p", "rb") )

    def _save_fired(self):
        pickle.dump(self.simulations , open( "test.p", "wb" ) )
        
    def _outdir_default(self):
        return os.path.join( os.path.abspath('.'),'Simulations')

    ####Simulation Stuff ####

    simulations=List(ISim)  
    selected_sim=Instance(ISim)

    sims_editor=\
        TableEditor(
            auto_size=False,  #Set in View
            columns=[
                ExpressionColumn(expression='object.runname', label='Simulation Time'),
                ExpressionColumn(expression='object.inc', label='Number of points in the sim'),
                ExpressionColumn(expression='object.sim_traits_list', label='Traits being simulated'), #Perhaps present start, end values to user somehow
                ObjectColumn(name='notes', label='Notes'),
                ],
            deletable=True,
            selected='selected_sim',
            show_toolbar=True,
            row_height=1,
        )

    ###Editors####
    layereditor=Instance(LayerEditor)
    stack= DelegatesTo('layereditor')               #Variables are stored here just because they can be useful for future implementations
    selected_layer = DelegatesTo('layereditor')
    selected_material=DelegatesTo('layereditor')
    selected_d=DelegatesTo('layereditor')
    angle_avg=DelegatesTo('current_state')

    ####Stack Actions####
    showreflectance=Action(name="Interface View", action="conf_ref")  #PHASE THIS OUT LATER WITH UNIFIED VIEW FRAMEWORK
    appendsim=Action(name="Store Current Simulation", action="store_sim")
    savesim=Action(name="Save Simulation", action="save_sim")  #action gets underscore

    mainmenu=MenuBar(
        Menu(showreflectance, name='Layer Options'), 	
        Menu(appendsim, savesim, name='Simulations'), 	
    )                      

    fibergroup=Group(
        Item('angle_avg', label='Angle Averaging Method',show_label=False),
        Item('fiberparms', editor=InstanceEditor(), style='custom', show_label=False),
        Item('fview', style='custom', show_label=False),
        label='Fiber'
    )

    layergroup=Group(
        Item('layereditor', editor=InstanceEditor(), style='custom', show_label=False),
        label='Stack')  

    materialgroup=Group(
        Item('selected_material', editor=InstanceEditor(), style='custom', show_label=False),
        label='Material'
    )            

    summarygroup=Group(
        Item('simulations', editor=sims_editor, show_label=False),

        ### Can't remove this or program trips, so I just hide it permanently
        Item('statedata', editor=state_editor, show_label=False, visible_when='8==9'),
        label='Parameter Summary'
    )

    simgroup=Group( Item('selected_sim', style='custom', editor=InstanceEditor(),
                         show_label=False), label='Simulations')



    fullgroup=VSplit(
                HSplit(
                  VGroup(
                    Item('specparms',show_label=False, style='custom'),
                    Item('outdir', label='Output Directory'),
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
                    resizable=True, buttons=['Undo'], title='SIM X')

    def __init__(self, *args, **kwargs):
        super(GlobalScene, self).__init__(*args, **kwargs)
        self.layereditor=LayerEditor()
        self.sync_trait('specparms', self.layereditor, 'specparms')
        self.sync_trait('modeltree', self.layereditor, 'modeltree')

        ### NEED TO RENAME AND REWRITE THIS... ITS NOT "STATEDATA"
        self.statedata=BasicReflectance()
        self.sync_trait('specparms', self.statedata, 'specparms')
        self.sync_trait('fiberparms', self.statedata, 'fiberparms')
        self.sync_trait('layereditor', self.statedata, 'layereditor')

      #self.simulations.append(LayerVfracEpsilon(base_app=self))   #Pass self to a simulation environment
        self.simulations.append(LayerVfrac(base_app=self))   #Pass self to a simulation environment
        
    ### Store copy of current simulation 
    def store_sim(self): self.simulations.append(self.selected_sim)
    def save_sim(self): self.selected_sim.output_simulation(self.outdir)

    ### Show Reflectance ###
    def conf_ref(self):
    #	self.statedata.update_R()   #FOR SOME REASON EVEN THOUGH I UPDATE THE STACK WHEN LAYERS ARE CHANGED, IT ONLY UNDERSTANDS WHEN LAYERS ARE REMOVED ORA DDED
        self.statedata.update_simview()
        self.statedata.simview.edit_traits(view='view2')
    #	pass




if __name__ == '__main__':
    popup=GlobalScene()
    popup.configure_traits()

