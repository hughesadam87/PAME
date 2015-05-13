
from traits.api import Str, HasTraits, Instance, Button, implements, File, \
     Property, Bool, Any
from traitsui.api import View, Item, Group, Include, InstanceEditor, VGroup
from interfaces import IMaterial, IAdapter
import os.path as op 

class BasicAdapter(HasTraits):
    """ Adapter for previewing, other things.  What is shown in "MATERIAL" tab. 
    populate_object() method used to show an instance of the material.
    """
    implements(IAdapter)
    mat_class = 'bulk' #<-- Don't change, needed by layer_editor
    
    name=Str('Basic Material')
    source=Str('Abstract Base Class for material')
    notes=Str('Not Found')
    matobject = Instance(IMaterial)
    preview = Button
    hide_preview = Button
    testview = Any # SHows material after preview fired
    apikey = 'basic' #<-- Materials API identifier
     
    def _preview_fired(self): 
        """ View the material as plot"""
        if self.matobject == None:
            self.populate_object()
        self.testview = self.matobject.mview
    #    self.matobject.edit_traits(kind='livemodal')      #Modal screws up objects for some reason
    #    self.destroy_object()

    def populate_object(self): 
        """Instantiate selected object."""
        # Imports must be in here because some objects need to access apikey,
        # but have infinite recursion if importing materials.  For example,
        # if composite materials needs to set materia1 to a composite material,
        # this will lead to recursive imports.
        from materialapi import ALLMATERIALS
        self.matobject = ALLMATERIALS[self.apikey]()

    def destroy_object(self):
        """Method used to destroy an object; not sure if ever will be useful
        or if it even destroys the object..."""
        self.matobject = None
        self.testview = None
        
    def _hide_preview_fired(self):
        self.destroy_object()

    basicgroup=Group(
        Item('name', style='readonly'),   #THESE ARENT READ ONLY!
        Item('source', style='readonly'),
        Item('notes'),
        Item('preview', show_label=False, visible_when='testview is None'), 
        Item('hide_preview', show_label=False, visible_when='testview is not None'),
        Item('testview', 
             visible_when='testview is not None',
             show_label=False,
             editor=InstanceEditor(),
             style='custom',
             )       
        )

    traitsview= View(Include('basicgroup'),              
                     resizable=True, 
                     )


class AirAdapter(BasicAdapter):
    name="Air"
    source="n=1.0 commonly used for air"
    notes="Shortcut for constant index of n=1.0 with no dispersion"        
    apikey = 'air'

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
    name="Drude"
    source="Gupta and Sharma.  Journ. of App. Phys. On the performance of " \
           "different bimetallic combinations in surface plasmon resonance " \
           "based ofiber optic sensors. 101, 093111 (2007)"
    notes="Computes dielectric funcion from plasma and collision wavelengths of "\
           "gold, silver, aluminum and copper.  Does not take into account size"\
           " corrections for small nanomaterials."
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

    # File Trai
    openfile = Button
    hidecontents = Button
    contents = Str 

    filegroup = Group(
                      Item('openfile', 
                           show_label=False, 
                           visible_when="contents == ''",
                           label='Show File Contents'
                           ),
                      Item('hidecontents', 
                           show_label=False,
                           label='Hide File Contents',
                           visible_when="contents != ''"
                           ),
                      Item('contents', 
                           style='readonly',
                           show_label=False, 
                           visible_when="contents != ''"
                           )
                     )
    
    traitsview= View(VGroup(
                       Include('basicgroup'),              
                       Include('filegroup'),
                       ),
                     resizable=True, 
                  
                  #   width=400,
                  #   height=200
                     )    
    
    def _openfile_fired(self):
        self.contents = open(self.file_path, 'r').read()
        
    def _hidecontents_fired(self):
        self.contents = ''
        
    def _get_name(self): 
        return op.splitext(op.basename(self.file_path))[0]        
        
    def populate_object(self): 
        """ FileAdapters make the object and set the default name separately.  Default
        material name is slightly different than self.name for display aesthetics.
        """
        self._set_matobject()
        self._set_matname() 
        
    # Let's me change keywords for file-to-file instantiation/populate_object?
    def _set_matobject(self):
        """ Create material.  THIS IS WHAT SUBCLASSES SHOULD OVERLOAD"""
        self.matobject = self.ABCFile(file_path=self.file_path)

    def _set_matname(self):
        """ Sets material name after populating object.  This name is:
        Source : filename  instead of just filename.  Need to separate or
        Source will end up in table when looking through DB
        """    
        self.matobject.mat_name = self.name
    
    def _set_name(self, newname): 
        self.name = newname


class SopraFileAdapter(ABCFileAdapter):   
    from material_files import SopraFile
    source="Sopra: http://www.sspectra.com/sopra.html"
    notes=""
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

