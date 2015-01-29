from traits.api import Str, HasTraits, Instance, Button, implements, File, Property, Bool
from traitsui.api import View, Item, Group, Include
from interfaces import IMaterial, IAdapter
from os.path import basename

class BasicAdapter(HasTraits):
    """ Adapter for previewing, other things.  What is shown in "MATERIAL" tab. 
    populate_object() method used to show an instance of the material.
    """
    from basic_material import BasicMaterial
    implements(IAdapter)
    
    name=Str('Basic Material')
    source=Str('Abstract Base Class for material')
    notes=Str('Not Found')
    matobject = Instance(IMaterial)
    preview = Button

    def _preview_fired(self): 
        """ View the material as plot"""
        if self.matobject == None:
            self.populate_object()
        self.matobject.edit_traits(kind='livemodal')      #Modal screws up objects for some reason
        self.destory_object()

    def populate_object(self): 
        """Method used to instantiate an object to conserve resources"""
        self.matobject=self.BasicMaterial()

    def destory_object(self):
        """Method used to destroy an object; not sure if ever will be useful"""
        self.matobject=None

    basicgroup=Group(
        Item('name', style='readonly'),   #THESE ARENT READ ONLY!
        Item('source', style='readonly'),
        Item('notes'),
        Item('preview'), 
    )

    traitsview= View(Include('basicgroup'),              
                     resizable=True, width=400, height=200)


class ConstantAdapter(BasicAdapter):
    from material_models import Constant
    name="Constant"
    source="Custom Made"
    notes="Simply provide a constant value for the dielectric/index of refraction and it will return a constant array of values.  Can enter complex values in the form"

    def populate_object(self): 
        self.matobject=self.Constant()
        

class SellmeirAdapter(BasicAdapter):
    from material_models import Sellmeir
    name="Sellmeir Model (defaults to optical fiber glasss)"
    source="Gupta Paper" #CITE
    notes="Preserves Kramers Kronig relation"

    def populate_object(self): 
        self.matobject=self.Sellmeir()
        
class CauchyAdapter(BasicAdapter):
    from material_models import Cauchy
    
    name="Cauchy Model (defaults to fused silicate)"
    source="http://en.wikipedia.org/wiki/Cauchy%27s_equation" 
    notes="Does not necessarily preserve Kramers Kronig relation (non-physical materials)"

    def populate_object(self): 
        self.matobject=self.Cauchy()    
    


class DrudeBulkAdapter(BasicAdapter):
    from material_models import DrudeBulk
    name="Drude Bulk"
    source="One of the gupta papers"
    notes="Uses lamplasma and lamcollision to predict dielectric function based on Drude model"

    def populate_object(self):
        self.matobject=self.DrudeBulk()

        
class NKJsonAdapter(BasicAdapter):
    """ Reads data from JSON database.  Json data must be of form:
    {dataset/filename : {
         x:xvals, n:nvals, k:kvals
         }
    With canonical form N = n + ik
    """

class ABCFileAdapter(BasicAdapter):
    from material_files import ABCExternal
    source="N/A"
    notes="Basic File of unknown type"
    file_path = File
    matobject = Instance(ABCExternal)
    name=Property(Str, depends_on='file_path')

    openfile = Button
    contents = Str #Only for opening file
    
    def _openfile_fired(self):
        self.contents = open(self.file_path, 'r').read()
        self.contents.edit_traits(kind='livemodal')      #Modal screws up objects for some reason
        
    def populate_object(self): 
        self.matobject=self.ABCFile(file_path=self.file_path)

    def _get_name(self): 
        return '%s' % basename( self.file_path )
    
    def _set_name(self, newname): 
        self.name = newname


class SopraFileAdapter(ABCFileAdapter):
    from material_files import SopraFile
    
    source="Sopra file"
    notes="http://www.sspectra.com/sopra.html"

    def _get_name(self): 
        return basename(self.file_path)
    
    def populate_object(self): 
        self.matobject = self.SopraFile(file_path=self.file_path)
        

class XNKFileAdapter(ABCFileAdapter):
    from material_files import XNKFile, XNKFileCSV
    csv = Bool(False) 
    source="NK_Delimited File"
    notes="Assumes real and imaginary parts of the index of refraction in "\
    "delimited columns.  If header present, must be first line and begin with "\
    "a '#' character"

    def populate_object(self): 
        if self.csv:
            self.matobject = self.XNKFileCSV(file_path=self.file_path)            
        else:
            self.matobject = self.XNKFile(file_path=self.file_path)

    def _get_name(self): 
        return 'NK Delimited Object:  %s' % basename( self.file_path )




if __name__ == '__main__':
    BasicAdapter().configure_traits()

