from traitsui.api import TableEditor, ObjectColumn, ExpressionColumn,InstanceEditor, \
     View, Item, HGroup
from traits.api import HasTraits, Instance, List, Button, Int, Property, Float, Any,\
     on_trait_change
from main_parms import SpecParms
from layer_traits_v2 import * 
from interfaces import ILayer, IMaterial
from traitsui.table_filter \
     import EvalFilterTemplate, MenuFilterTemplate, RuleFilterTemplate, \
     EvalTableFilter
from modeltree_v2 import Model
from composite_tree import CompositeMain
from nanotree import NanoMain

from composite_materials_v2 import SphericalInclusions_Disk   #For testing purposes, once tree editors are built for this, discard
from advanced_objects_v2 import NanoSphereShell

class LayerEditor(HasTraits):
    modeltree=Instance(Model,())
    compositetree=Instance(CompositeMain,())
    nanotree=Instance(NanoMain,())

    selectedtree=Property(depends_on='layer_type')  #Determines which tree to use to select materials

    sync_rad_selection=Any

    specparms=Instance(SpecParms,())  #Default spec parms overwritten when called in supermodel  
    stack = List(ILayer)  ##Tables of layer and data
    solvent = Instance(ILayer) #Set when _stack_default returns
    substrate = Instance(ILayer)  

    sync_solvent=Bool(False)      #Syncs solvent of composite materials with stack; changes with selected_layer
    sync_d_radius=Bool(False)     #Syncs interface spacing, d, with properties of NP's

    selected_layer=Instance(ILayer)
    layer_type=Enum('Bulk Material', 'Mixed Bulk Materials', 'Nanoparticle Objects')

    selected_d=Any  #Property/delgatesto messed up for this, perhaps because a table is involved.  Leave this way
    selected_material=Instance(IMaterial)

    tablesize=Property(Int, depends_on='stack')
    selected_index=Int(1)

    add_basic=Button
    remove=Button
    changematerial=Button 

    layereditor =\
        TableEditor(
            columns=[
                ObjectColumn(name='name', label='Layer Name'),         #CAN SET AN INDIVIDUAL COLUMN TO EDITABLE, BUT OBJECTCOLUMN VS EXPRESSION COLUMN IS ALSO WAY TO GO
                ObjectColumn(name='mat_name', label='Material Name'),
                ExpressionColumn(expression='object.d', label='Interface Length(nm)'),
                ExpressionColumn(expression='object.designator', label='Layer Specifier'),
                ExpressionColumn(expression='object.sync_status', label='Synchronized to Medium'),      
                ExpressionColumn(expression='object.material.source',label='Source'),
                ],
            filters = [ EvalFilterTemplate, MenuFilterTemplate, RuleFilterTemplate ],
            deletable   = True, 
            sort_model  = True,
            auto_size = True,
            orientation='vertical',    #Orientation between built-in split between table and edit view
            show_toolbar=False,
            selected           = 'selected_layer',   #String name is arbitrary and passed as a global variable to other instances
            selection_color    = 0x000000,
            selection_bg_color = 0xFBD391,
        )


    def simulation_requested(self):
        return {'Stack':[layer.simulation_requested() for layer in stack]}

    ####BUTTONS MOSTLY FOR TESTING, IF YOU COULD HAVE A ROW FACTORY THAT NEW HOW TO ADD AND ASSIGN SPEC PARMS VARIABLE (AKA A ROW FACTOR THAT WAS AN OBJECT FUNCTION, THIS BE BETTER###

    def _selected_layer_default(self):
        return self.stack[1]

    def _sync_solvent_changed(self):
        '''This is sloppy because when I change the item in the table, this gets called but not all materials have sync/unsync methods,
        	so I accept the attribute error which is bad'''
        try:
            if  self.sync_solvent!= self.selected_layer.sync_status:  #Only called when there's a relative change
                if self.sync_solvent == True:
                    self.selected_layer.sync_solvent(solvent=self.solvent.material)    #Done at layer_traits level
                else:
                    self.selected_layer.unsync_solvent()	
        except (AttributeError):
            pass

    def _sync_d_radius_changed(self):
        self.sync_rad_selection=self.selected_layer.sync_rad_selection

    def _get_selected_d(self): 
        if self.selected_layer is not None:
            return self.selected_layer.d

    def _set_selected_layer(self, d): 
        self.selected_layer.d=d

    def _add_basic_fired(self): 
        layer=BasicLayer()
        position=self.selected_index
        if position==0:  #Glitch where it adds before substrate
            position=1
        self.stack.insert(position, layer)

        self.sync_trait('specparms', layer, 'specparms')
        self.sync_trait('modeltree', layer, 'modeltree', mutual=True)

        self.selected_layer=self.stack[self.selected_index]

    def _get_selectedtree(self): 
        if self.layer_type=='Bulk Material': 
            return self.modeltree
        if self.layer_type=='Mixed Bulk Materials':
            return self.compositetree
        if self.layer_type=='Nanoparticle Objects': 
            return self.nanotree
        

    def _remove_fired(self): 
        self.stack.remove(self.selected_layer)
        self.selected_layer=self.stack[self.selected_index-1]   #Simply moves the selected layer one down from the one deleted


    def _changematerial_fired(self):        
        """ Change material sets a new layer by prompting user to choose a material
        from model tree, then it populates the adapter.
        """
        self.selectedtree.configure_traits(kind='modal')

        try:
            selected_adapter=self.selectedtree.current_selection    #
            selected_adapter.populate_object()
            newmat=selected_adapter.matobject	

            # If changing substrate or solvent
            if self.stack[self.selected_index] == self.solvent:
                newlayer = Solvent(material=newmat)
                self.solvent=newlayer
            elif self.stack[self.selected_index] == self.substrate:
                newlayer = Substrate(material=newmat)		
                self.substrate=newlayer

            ### If changing layer ###

            else:

                if self.layer_type=='Mixed Bulk Materials':
                    newlayer=Composite(material=newmat, 
                                       d = self.selected_d) 
               
                elif self.layer_type=='Bulk Material':
                    print 'entering basic layerl'
                    newlayer=BasicLayer(material=newmat, 
                                        d = self.selected_d)

                elif self.layer_type=='Nanoparticle Objects':
                    newlayer=Nanoparticle(material=newmat, 
                                          d = self.selected_d)

            print self.selected_index
            self.stack[self.selected_index] = newlayer
            self.selected_layer = self.stack[self.selected_index]

            self.sync_trait('modeltree', newlayer, 'modeltree')    #AGAIN NOT SURE IF NECESSARY, if i can just initialize 
            self.sync_trait('specparms', newlayer, 'specparms')

        except (TypeError, AttributeError) as exc:  #If user selects none, or selects a folder object, not an actual selection
            print 'in exception in layereditor change materal', self.stack[self.selected_index], self.selected_layer
            raise exc
            pass


    def _stack_default(self):
        '''Initialize the stack with some layers'''
        solvent=Solvent() ; substrate=Substrate()
        mats=[substrate, Nanoparticle(d=24.0), solvent]  #Default layer is nanoparticle with shell
#		mats=[substrate, Composite(d=24.0), solvent]     #Default layer is composite material
#		mats=[substrate, BasicLayer(d=24.0), solvent]    #Default layer is basic layer
        for mat in mats:
            self.sync_trait('modeltree', mat, 'modeltree')  
            self.sync_trait('specparms', mat, 'specparms')
        return mats

    ###  Important to declare these here instead of on the delcaration of the stack; otherwise tableeditor trips ###
    def _solvent_default(self): 
        return self.stack[-1]

    def _substrate_default(self): 
        return self.stack[0]
    ######################################################################

    def _get_tablesize(self): 
        return len(self.stack)  #Resets table-end

    def _selected_layer_changed(self):	
        if self.selected_layer is not None:
            self.selected_index=self.stack.index(self.selected_layer)
            self.selected_d=self.selected_layer.d
            self.selected_material=self.selected_layer.material #Used by supermodel in view
            self.sync_solvent=self.selected_layer.sync_status


    def _selected_d_changed(self):
        try:
            if type(self.selected_d)==float:
                self.selected_layer.d=self.selected_d
            elif type(self.selected_d)==unicode:
                new=str(self.selected_d.strip())
                self.selected_layer.d=float(new)
        except ValueError:
            pass

    @on_trait_change('solvent, solvent.material')        #WHEN SOLVENT CHANGES, SYNCS ALL SELECTED MATERIALS
    def sync_solvents(self):
        print 'syncing solvs'
        for layer in self.stack:
            if layer.designator !='basic':
                if layer.sync_status==True:	
                    layer.sync_solvent(self.solvent.material)



    traits_view=View(
        #	HSplit(
        Item('stack', editor=layereditor, show_label=False),
        HGroup(
            Item('add_basic', show_label=False), 
            Item('remove', enabled_when='selected_layer != solvent and selected_layer != substrate', show_label=False),
            Item('changematerial', label='Configure Layer Material', show_label=False, enabled_when='selected_layer is not None'),
            Item('layer_type', label='Choose Material Type', style='simple'),
            ), 

        HGroup(
            Item('selected_d', enabled_when='selected_layer != solvent and selected_layer != substrate', label='Layer thickness(nm)'),
            Item('sync_solvent', label='Sync solvent material', enabled_when='selected_layer.designator != "basic"'),
            Item('sync_d_radius', enabled_when='selected_layer.designator == "nanoparticle"'), 
            Item('sync_rad_selection',enabled_when='selected_layer.designator == "nanoparticle"'),
            Item('selected_index', style='readonly', label='Position in stack'),
            ),
        #	      ),
        resizable=True)


if __name__ == '__main__':
    LayerEditor().configure_traits()

