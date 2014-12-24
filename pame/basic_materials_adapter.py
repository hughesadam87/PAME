from traits.api import Str, HasTraits, Instance, Button, implements, File, Property
from traitsui.api import View, Item, Group, Include
from interfaces import IMaterial, IAdapter
from os.path import basename


class BasicAdapter(HasTraits):
    """ Adapter for previewing, other things.  What is shown in "MATERIAL" tab. 
    populate_object() method used to show an instance of the material.
    """
    from basic_material import BasicMaterial
    
    name=Str('Basic Material')
    source=Str('Has Traits object to understand material')
    notes=Str('No notes Provided')
    matobject=Instance(BasicMaterial)
    preview=Button
    implements(IAdapter)

    def _preview_fired(self): 
        if self.matobject == None:
            self.populate_object()
        self.matobject.edit_traits(kind='livemodal')      #Modal screws up objects for some reason
        self.destory_object()

    def populate_object(self): 
        '''Method used to instantiate an object to conserve resources'''
        self.matobject=self.BasicMaterial()

    def destory_object(self):
        '''Method used to destroy an object; not sure if ever will be useful'''
        self.matobject=None

    basicgroup=Group(
        Item('name', style='readonly'), 
        Item('source', style='readonly'),
        Item('notes', style='readonly'), 
        Item('preview')
    )

    traitsview= View(Include('basicgroup'),
                     resizable=True, width=400, height=200)

class ConstantAdapter(BasicAdapter):
    from material_models import Constant
    name="Constant"
    source="Custom Made"
    notes="Simply provide a constant value for the dielectric/index of refraction and it will return a constant array of values.  Can enter complex values in the form"
    matobject=Instance(Constant)

    def populate_object(self): 
        self.matobject=self.Constant()

class SellmeirAdapter(BasicAdapter):
    from material_models import Sellmeir
    name="Sellmeir dispersion for optical-fiber glass"
    source="Gupta Paper"
    matobject=Instance(Sellmeir)

    def populate_object(self): 
        self.matobject=self.Sellmeir()


class DrudeBulkAdapter(BasicAdapter):
    from material_models import DrudeBulk
    name="Drude Bulk"
    source="One of the gupta papers"
    notes="Uses lamplasma and lamcollision to predict dielectric function based on Drude model"
    matobject=Instance(DrudeBulk)

    def populate_object(self):
        self.matobject=self.DrudeBulk()


class BasicFileAdapter(BasicAdapter):
    from material_files import BasicFile
    source="N/A"
    notes="Basic File of unknown type"
    thefile=File
    matobject=Instance(BasicFile)
    name=Property(Str, depends_on='thefile')

    def populate_object(self): 
        self.matobject=self.BasicFile(thefile=self.thefile)

    def _get_name(self): 
        return 'Basic Object:  %s' % basename( self.thefile )
    
    def _set_name(self, newname): 
        self.name=newname


class SopraFileAdapter(BasicFileAdapter):
    from material_files import SopraFile
    
    source="Sopra file format-based object"
    notes="Sopra files are defined by header of interesting type... expand later"

    def _get_name(self): 
        return 'Sopra Object:  %s' % basename( self.thefile )

    def populate_object(self): 
        self.matobject = self.SopraFile(thefile=self.thefile)
        

class NKDelimitedAdapter(BasicFileAdapter):
    from material_files import NK_Delimited
    source="NK_Delmited object"
    notes="Assumes real and imaginary parts of the index of refraction in delimited columns.  If header present, must be first line and begin with a '#' character"

    def populate_object(self): 
        self.matobject = self.NK_Delimited(thefile=self.thefile)

    def _get_name(self): 
        return 'NK Delimited Object:  %s' % basename( self.thefile )




if __name__ == '__main__':
    BasicAdapter().configure_traits()

