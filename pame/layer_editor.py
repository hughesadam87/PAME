from traitsui.api import TableEditor, ObjectColumn, ExpressionColumn,InstanceEditor, \
     View, Item, HGroup
from traits.api import HasTraits, Instance, List, Button, Int, Property, Float, Any,\
     on_trait_change
from main_parms import SHARED_SPECPARMS
from layer_traits_v2 import * 
from interfaces import ILayer, IMaterial
from traitsui.table_filter \
     import EvalFilterTemplate, MenuFilterTemplate, RuleFilterTemplate, \
     EvalTableFilter
from collections import OrderedDict

from pame.modeltree_v2 import SHARED_TREE
from pame.materialapi import ALLMATERIALS

class StackError(Exception):
    """ """

class LayerEditor(HasTraits):
    
    specparms = Instance(HasTraits, SHARED_SPECPARMS)
    selectedtree = Instance(HasTraits, SHARED_TREE) 

    sync_rad_selection = Any

    stack = List(ILayer)  #Tables of layer and data
    solvent = Instance(ILayer) #Set when _stack_default returns
    substrate = Instance(ILayer)  

    sync_solvent = Bool(False)      #Syncs solvent of composite materials with stack; changes with selected_layer
    sync_d_radius = Bool(False)     #Syncs interface spacing, d, with properties of NP's

    selected_layer = Instance(ILayer)

    selected_d=Any  #Property/delgatesto messed up for this, perhaps because a table is involved.  Leave this way
    selected_material = Instance(IMaterial)

    tablesize = Property(Int, depends_on='stack')
    selected_index = Int(1)

    add_basic=Button
    remove=Button
    changematerial=Button 

    layereditor = \
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

    traits_view=View(
        #	HSplit(
        HGroup(
            Item('add_basic', show_label=False), 
            Item('remove', show_label=False, 
                 enabled_when='selected_layer != solvent and selected_layer != substrate'),
            Item('changematerial', label='Configure Layer Material',
                 show_label=False, enabled_when='selected_layer is not None'),
            ), 

        HGroup(
            Item('selected_d', enabled_when='selected_layer != solvent and selected_layer != substrate', label='Layer thickness(nm)'),
            Item('sync_solvent', label='Sync solvent material', enabled_when='selected_layer.designator != "basic"'),
            Item('sync_d_radius', enabled_when='selected_layer.designator == "nanoparticle"'), 
            Item('sync_rad_selection',enabled_when='selected_layer.designator == "nanoparticle"'),
            Item('selected_index', style='readonly', label='Stack position'),
            ),
        Item('stack', editor=layereditor, show_label=False),
        resizable=True)
    
    def simulation_requested(self, materials_only=False):
        """ Nested dictionary keyed by layer number:
        {layer0 : {layer_name, layer_d, ...}, layer1 : {layer_name, layer_d, ...}}
        If materials_only, {layer_0} : {material_0}, and layermetadata like
        layer_d, layer_designatore are lost.  Option is selected by gensim.
        """
        # No underscore!   Be consistent with how users enter in inputs of sim
        out = OrderedDict(('layer%s' % idx, layer.simulation_requested()) 
                    for idx, layer in enumerate(self.stack))        

        if materials_only:
            out = OrderedDict(('layer%s' % idx, layer.material.simulation_requested()) 
                        for idx, layer in enumerate(self.stack))  

        return out          

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

        self.selected_layer=self.stack[self.selected_index]

    def _remove_fired(self): 
        self.stack.remove(self.selected_layer)
        #        self.selected_layer.material.remove_trait('lambdas')        
        self.selected_layer=self.stack[self.selected_index-1]   #Simply moves the selected layer one down from the one deleted


    def _changematerial_fired(self):        
        """ Change material sets a new layer by prompting user to choose a material
        from model tree, then it populates the adapter.
        """
        self.selectedtree.configure_traits(kind='modal')

        try:
            selected_adapter=self.selectedtree.current_selection  
            mat_class = selected_adapter.mat_class
            # If user doesn't choose material, selected_adapter becomes a MaterialList isntead of None, why??
            selected_adapter.populate_object()
            newmat=selected_adapter.matobject	

            # If changing substrate or solvent
            if self.stack[self.selected_index] == self.solvent:
                newlayer = Solvent(material=newmat)
                self.solvent=newlayer
            elif self.stack[self.selected_index] == self.substrate:
                newlayer = Substrate(material=newmat)		
                self.substrate=newlayer

            # If changing normal layer
            else:
                if mat_class=='mixed':
                    newlayer=Composite(material=newmat, 
                                       d = float(self.selected_d),
                                       ) 
               
                elif mat_class== 'bulk':
                    newlayer=BasicLayer(material=newmat, 
                                        d = float(self.selected_d),
                                        )

                elif mat_class == 'nano':
                    newlayer=Nanoparticle(material=newmat, 
                                          d = float(self.selected_d),
                                          )
                else:
                    raise Exception('mat_class "%s" not understood' % mat_class)

            self.stack[self.selected_index] = newlayer
            self.selected_layer = self.stack[self.selected_index]

        except (TypeError, AttributeError) as exc:  #If user selects none, or selects a folder object, not an actual selection
            print 'In exception in layereditor change materal\n', self.stack[self.selected_index], self.selected_layer
            raise exc


    def _stack_default(self):
        '''Initialize the stack with some layers'''
        mats=[Substrate(),
#              Composite(d=24.0),
              Nanoparticle(d=24.0), 
              Solvent()]  #Default layer is nanoparticle with shell
        return mats

    #  Important to declare these here instead of on the delcaration of the stack; otherwise tableeditor trips ###
    def _solvent_default(self): 
        return self.stack[-1]

    def _substrate_default(self): 
        return self.stack[0]

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

    #def __getattr__(self, attr):
        #""" Simulation needs to access stack by integer sometimes, IE
        #layer1, layer2 so can do self.layer1 akin to self.selected_layer.
        #"""
        ## Layer1, layer2, Layer_3
        #if attr.lower().startswith('layer'):
            #layer_int = int(attr.lstrip('layer_')) #Works with _ or no _
            #if layer_int not in range(len(self.stack)):
                #raise StackError("Invalid layer index %s on stack of length %s" 
                                 #% (layer_int, len(self.stack)))
            #return self.stack[layer_int]
                    
        

# Basically a global
# ------------------
SHARED_LAYEREDITOR = LayerEditor()


if __name__ == '__main__':
    LayerEditor().configure_traits()

