import copy, pickle, os
import logging
import os.path as op


# Enthought imports
from traits.api import *
from traitsui.api import *
from enable.component_editor import ComponentEditor

# Local imports
import globalparms
from opticalstack import DielectricSlab
from basicplots import OpticalView
from layer_editor import LayerEditor
from main_parms import FiberParms, SpecParms
from interfaces import IOptic, ILayer, IMaterial, IStorage, ISim
from fiberview import ViewMlab, FiberView, EllispometryView
from modeltree_v2 import Model
from plotselector import PlotSelector
from gensim import LayerSimulation, ABCSim, SimConfigure
from handlers import WarningDialog
import config


#http://stackoverflow.com/questions/27790572/traitsui-buggy-view-depending-on-os
#import os 
#os.environ['QT_API'] = 'pyside'
#os.environ['ETS_TOOLKIT'] = 'qt4'#, QT_API=pyside

# Reflectance/Mode summary (don't think its used; think its deprecated)
state_editor =\
     TableEditor(
          auto_size=False,  #Set in View
          columns=[
               # These are all sim_traits.DielectricSlab traits
               ExpressionColumn(expression='object.Mode', label='Fiber Mode'),
               ExpressionColumn(expression='object.angles', label='Angle'),
               ExpressionColumn(expression='object.stack', label='Stack'),
               ExpressionColumn(expression='object.ds', label='DS'),
               ExpressionColumn(expression='object.angle_avg', label='Averaging Style'),            
#            ObjectColumn(name='sim_designator', label='State Designator'), #What ist his?
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
     modeltree=Instance(Model,())
     lambdas=DelegatesTo('specparms')  #Actually not used except for making it easy to run sims
     plot_selector = Instance(PlotSelector)

     fview=Instance(FiberView,())     #May want to pass specparms and fiberparms to this later if it requries them

     current_state = Instance(IOptic)
     opticstate = Instance(IOptic)
     opticview = DelegatesTo('opticstate')

     save=Button
     load=Button

     #Simulation 
     sim_outdir=Directory     
     simulations=List(ISim)  
     selected_sim=Instance(ISim)
     configure_storage = Instance(SimConfigure)   #<--- Want all sims to share this, right?

     #Editors##
     layereditor=Instance(LayerEditor)
     stack= DelegatesTo('layereditor')               #Variables are stored here just because they can be useful for future implementations
     selected_layer = DelegatesTo('layereditor')
     selected_material=DelegatesTo('layereditor')
     selected_d=DelegatesTo('layereditor')
#    angle_avg=DelegatesTo('current_state')

     #Actions
     showreflectance=Action(name="Popout Optics Plot", action="popout_optics")  #PHASE THIS OUT LATER WITH UNIFIED VIEW FRAMEWORK
     showmaterial = Action(name='Popout Material Plot', action="popout_material")
     appendsim=Action(name="Add Simulation", action="new_sim")
     savesim=Action(name="Save Selected Simulation", action="save_sim")  #action gets underscore
     savesim_all=Action(name="Save All Simulation", action="save_allsims")  #action gets underscore


     # Make Menubar
     mainmenu=MenuBar(
          Menu(showmaterial, showreflectance, name='Plot Options'), 	
          Menu(appendsim, savesim, savesim_all, name='Simulation Options'), 	       
     )                      

     fibergroup=Group(
          # Angle_avg depends on the DielectricSlab
#        Item('angle_avg', label='Angle Averaging Method',show_label=False),
               Item('fiberparms', editor=InstanceEditor(), style='custom', show_label=False),
               Item('fview', style='custom', show_label=False),
               label=globalparms.strataname
                    )

     layergroup=Group(
          Item('layereditor', 
               editor=InstanceEditor(),
               style='custom', 
               show_label=False),
          label=globalparms.stackname)  

     materialgroup=Group(
          Item('selected_material',
               editor=InstanceEditor(),
               style='custom',
               show_label=False),
          label=globalparms.materialname
     )            

     choosesimgroup=Group(
          Item('simulations', editor=sims_editor, show_label=False),

          # Can't remove this or program trips
          Item('opticstate', 
               editor=state_editor, 
               show_label=False, 
               visible_when='8==9'#always vis
               ),
          label='Choose Simulation'
     )

     simgroup=Group(
          Item('selected_sim', 
               style='custom',
               editor=InstanceEditor(),
               show_label=False),           
          label='Simulations')

     globalgroup = Group( 
          Item('specparms',show_label=False, style='custom'),      
          Include('choosesimgroup'), #simulation and summary        
          label=globalparms.globsname,
     )


     fullgroup=VSplit(
          HSplit(
               VGroup(
                    Item('plot_selector', show_label=False, style='custom'),
#                    Item('specparms',show_label=False, style='custom'),
#                    Item('sim_outdir', label='Output Directory', show_label=False),
#                    Include('choosesimgroup'), #simulation and summary
),
               # PLOT
               VGroup(
                    Item('opticview', 
                         style='custom',
                         show_label=False),
               )
               ),

          Tabbed(
               Include('globalgroup'),
               Include('fibergroup'), 
               Include('layergroup'),
               Include('materialgroup'),
               Include('simgroup'),
               ),
     )


#     from traitsui.value_tree import ValueTree, value_tree_editor, TreeEditor, _ValueTree, value_tree_nodes, value_tree_editor_with_root
#     from traitsui.editors.value_editor import _ValueEditor, ValueEditor
     Mainview = View(
                     #Item(name='stack', editor=TreeEditor(auto_open=2, 
                                                          #hide_root=False,
                                                          #editable=True,
                                                          #nodes=value_tree_nodes)
                                                          #), 
                     Include('fullgroup'), 
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

          # NEED TO RENAME AND REWRITE THIS... ITS NOT "opticstate"
          self.opticstate=DielectricSlab()
          self.sync_trait('specparms', self.opticstate, 'specparms')
          self.sync_trait('fiberparms', self.opticstate, 'fiberparms')
          self.sync_trait('layereditor', self.opticstate, 'layereditor')

     #self.simulations.append(LayerSimulationEpsilon(base_app=self))   #Pass self to a simulation environment
          self.simulations.append(
               LayerSimulation(base_app=self, outname=config.SIMPREFIX+'0')
                                  )  


     def _load_fired(self):
          self.simulations=pickle.load(open("test.p", "rb") )

     def _save_fired(self):
          pickle.dump(self.simulations , open( "test.p", "wb" ) )

     def _plot_selector_default(self):
          return PlotSelector(layereditor = self.layereditor)

     def _configure_storage_default(self):
          return SimConfigure(b_app=self)

     # Where should this point?  WHAT IF DOESN"T EXIST
     def _sim_outdir_default(self):
          if op.exists(config.SIMFOLDER):
               return config.SIMFOLDER
          else:
               return op.abspath('.')

     # Store copy of current simulation 
     def new_sim(self): 
          self.simulations.append(LayerSimulation(base_app=self,  #<--- LayerSimulation.  Base_app = self.copy?
                                                  outname=config.SIMPREFIX+str(len(self.simulations))))
     def save_sim(self): 
          self.selected_sim.save() #<--- NEED TO CALL TO_JSON NOT OUTPUT_SIMULATION

     def save_allsims(self):
          ''' Saves all stored simulations in the sims_editor.  Checks for duplicate names and non-run/incomplete
          simulations and prompts user accordingly.'''

          # Check to make sure all simulations have completed data
          unrun=[s.outname for s in self.simulations if s._completed == False]   
          nrunstring=' '.join(unrun)
          if len(unrun) > 0:
               message('Cannot save simulations:  %s. Results not found.'%nrunstring, title='Warning')
               # Can't save either way, so force exit instead of user being able to continue
               return               

          # Check for duplicate runnames        
          rnames=[s.outname for s in self.simulations]        
          non_uniq=[r for r in rnames if rnames.count(r) > 1]
          if len(non_uniq) > 0:
               non_uniq=list(set(non_uniq))
               nustring=' '.join(non_uniq)

               message('Duplicate simulation outfile names found: %s.'%nustring, title='Warning')
               return        

          # Output completed simulations
          outsims=[s for s in self.simulations if s not in unrun]
          for s in outsims:
               s.save(confirmwindow=False)
          message('%s simulation(s) saved to directory: "%s"'%(len(outsims),
                                                               op.split(self.sim_outdir)[1]), title='Success')

     # Pop Reflectance/Material Plots
     # ------------------------
     def popout_optics(self):
          """ Refresh and popup optics plot """
          self.opticstate.opticview.edit_traits()

     def popout_material(self):
          #http://code.enthought.com/projects/files/ets_api/enthought.traits.ui.view.html
          # what kind should these use
          self.plot_selector.edit_traits()#kind='panel')

def main():
     # HACK FOR DEBUG UNTIL DATA CAN BE IMPORTED CORRECTLY
     # os.chdir('/home/glue/Desktop/fibersim')    

     popup=GlobalScene()
     
     # Need to force selections for QT to default correctly.  Not a prob in WX...
     popup.selected_layer = popup.layereditor.stack[0] #<-- need to go 0,1 to trigger update
     popup.selected_layer = popup.layereditor.stack[1]
     popup.selected_sim = popup.simulations[0]
     
     popup.opticstate.update_opticview()     
     popup.configure_traits()    



if __name__ == '__main__':
     main()
