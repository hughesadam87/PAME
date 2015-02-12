
from traits.api import Str, HasTraits, Instance, Button, implements, File, Property, Bool
from traitsui.api import View, Item, Group, Include
from interfaces import IMaterial, IAdapter
import os.path as op 

class BasicAdapter(HasTraits):
    """ Adapter for previewing, other things.  What is shown in "MATERIAL" tab. 
    populate_object() method used to show an instance of the material.
    """
    implements(IAdapter)
    
    name=Str('Basic Material')
    source=Str('Abstract Base Class for material')
    notes=Str('Not Found')
    matobject = Instance(IMaterial)
    preview = Button
    apikey = 'basic' #<-- Materials API identifier

    def _preview_fired(self): 
        """ View the material as plot"""
        if self.matobject == None:
            self.populate_object()
        self.matobject.edit_traits(kind='livemodal')      #Modal screws up objects for some reason
        self.destory_object()

    def populate_object(self): 
        """Instantiate selected object."""
        # Imports must be in here because some objects need to access apikey,
        # but have infinite recursion if importing materials.  For example,
        # if composite materials needs to set materia1 to a composite material,
        # this will lead to recursive imports.
        from materialapi import ALLMATERIALS
        self.matobject=ALLMATERIALS[self.apikey]()

    def destory_object(self):
        """Method used to destroy an object; not sure if ever will be useful
        or if it even destroys the object..."""
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
    name="Constant"
    source="Custom Made"
    notes="Simply provide a constant value for the dielectric/index of refraction and it will return a constant array of values.  Can enter complex values in the form"        
    apikey = 'constant'
    
class DispwaterAdapter(BasicAdapter):
    name = "Dispersion model for water"
    source = "Don't recall"
    notes = "Better than using a constant index for water"
    apikey = 'dispwater'

class SellmeirAdapter(BasicAdapter):
    from material_models import Sellmeir
    name="Sellmeir Model (defaults to optical fiber glasss)"
    source="Gupta Paper" #CITE
    notes="Preserves Kramers Kronig relation"
    apikey = 'sellmeir'
        
class CauchyAdapter(BasicAdapter):
    name="Cauchy Model (defaults to fused silicate)"
    source="http://en.wikipedia.org/wiki/Cauchy%27s_equation" 
    notes="Does not necessarily preserve Kramers Kronig relation (non-physical materials)"
    apikey='cauchy'

class DrudeBulkAdapter(BasicAdapter):
    name="Drude Bulk"
    source="One of the gupta papers"
    notes="Uses lamplasma and lamcollision to predict dielectric function based on Drude model"
    apikey='drudebulk'

        
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
        
    def _get_name(self): 
        return op.splitext(op.basename(self.file_path))[0]        
        
    def populate_object(self): 
        """ FileAdapters make the object and set the default name separately.  Default
        material name is slightly different than self.name for display aesthetics.
        """
        self._set_matobject()
        self._set_matname() 
        
    def _set_matobject(self):
        """ Create material.  THIS IS WHAT SUBCLASSES SHOULD OVERLOAD"""
        self.matobject = self.ABCFile(file_path=self.file_path)

    def _set_matname(self):
        """ Sets material name after populating object.  This name is:
        Source : filename  instead of just filename.  Need to separate or
        Source will end up in table when looking through DB"""    
        self.matobject.mat_name = '%s: %s' % (self.source, self.name)
    
    def _set_name(self, newname): 
        self.name = newname


class SopraFileAdapter(ABCFileAdapter):    
    source="Sopra"
    notes="http://www.sspectra.com/sopra.html"
    apikey='sopra'

    def _set_matobject(self): 
        self.matobject = self.SopraFile(file_path=self.file_path)
        
class XNKFileAdapter(ABCFileAdapter):
    from material_files import XNKFile, XNKFileCSV
    csv = Bool(False) 
    source="NK_Delimited"
    notes="Assumes real and imaginary parts of the index of refraction in "\
    "delimited columns.  If header present, must be first line and begin with "\
    "a '#' character"
    
    apikey = Property(depends_on='csv')
    
    def _get_apikey(self):
        if self.csv:
            return 'xnk_csv'
        return 'xnk'        

    def _set_matobject(self): 
        if self.csv:
            self.matobject = self.XNKFileCSV(file_path=self.file_path)            
        else:
            self.matobject = self.XNKFile(file_path=self.file_path)


if __name__ == '__main__':
    BasicAdapter().configure_traits()

