from traits.api import Str, HasTraits, Instance, Button, implements,\
     File, Property, Bool, Any, Enum
from traitsui.api import View, Item, Group, Include, InstanceEditor, VGroup
from interfaces import IMaterial, IAdapter
from simple_materials_adapter import ABCFileAdapter
from material_files import ABCExternal
import os.path as op
import numpy as np

import yaml

class YamlMaterial(ABCExternal):
    """ """

    file_spec_unit = Str('Micrometers')        

    # New traits
    datatype = Enum(['nk','k'])
    datastring = Str  #This is actual data that yaml gets as str

    # This is main trigger from yaml adapter I think
    def _datastring_changed(self):
        self.update_data()
        self.update_interp()
        
    def update_data(self):
        """ Yaml Files are always Micrometers.
        """    
        # Already a long string, so this seems best way to parse...
        if self.datatype == 'nk':
            x = []
            n = []
            k = []
            for line in self.datastring.split('\n'):
                line = line.strip().split()
                if line:
                    x.append(line[0])
                    n.append(line[1])
                    k.append(line[2])

            self.file_x = np.array(x, dtype=float)
            n, k = np.array(n, dtype=float), np.array(k, dtype=float)
            self.file_n = n + 1j*k

        else:
#         elif datatype == 'k':
            raise NotImplementedError('YAML datatype not understood %s' % datatype)    

        #Interpolate
        #self.update_interp()

class YamlAdapter(ABCFileAdapter):
    """ Adapter to parse yaml.dump and figure out if experimental data, or 
    which type of model (2-8) and call corresponding material. 
    """

    implements(IAdapter)

    source=Str('YAML-encoded')  #<--- Gets overwrote from modeltree
    notes=Str('Not Found')
    REFERENCES = Str('Not Found')
    DATA = Any()
    COMMENTS = Str('Not Found')
    FORMULA = Any

    root = None #Used for compatibility with modeltree to set special name

    _is_model = Property(Bool)

    def _get_name(self):
        """ Uses folder heirarchy and basename (ie main_AU_Johnson) """
        if not self.root:
            name = '%s' % op.basename( self.file_path )
        
        # Strip root off path
        else:
            relative_path = op.relpath(self.file_path, self.root)
            name = relative_path.replace(op.sep, '_')

        return op.splitext(name)[0]

    def _get__is_model(self):
        """ If yaml has a FORMULA key, this is a model. """
        if self.FORMULA:
            return True
        else:
            return False


    # CALL THIS LATER ON SELECTION
    def read_file_metadata(self):
        """ Opens yaml file, gets the metadata and data. """
        loaded = yaml.load(open(self.file_path, 'r'))

        try:
            self.REFERENCES = loaded['REFERENCES']
        except KeyError:
            pass

        try:
            self.DATA = loaded['DATA']
        except KeyError:
            pass

        try:
            self.COMMENTS = loaded['COMMENTS']
        except KeyError:
            pass

        try:
            self.FORMULA = loaded['FORMULA']
        except KeyError:
            pass        


    def _set_matobject(self): 
        """Method used to instantiate an object to conserve resources"""
    
        if self._is_model:
            raise NotImplementedError('RIINFO DB models not supported up yet!')

        else:
            datatype = self.DATA['type']
            data = self.DATA['data']
            self.matobject = YamlMaterial(datastring=data, datatype=datatype)


    # VIEW (modify basicgroup from BasicAdapter and use filegroup unchanged)
    yamlgroup = Group(
        Item('name', style='readonly'),   #THESE ARENT READ ONLY!
        Item('_is_model', style='readonly', label='Model Material'),
        Item('source', style='readonly'),
        Item('REFERENCES', style='readonly'),
        Item('FORMULA', style='readonly'),
        Item('preview', show_label=False, visible_when='testview is None'), 
        Item('hide_preview', show_label=False, visible_when='testview is not None'),
        Item('testview', 
             visible_when='testview is not None',
             editor=InstanceEditor(),
             style='custom',
             show_label=False),        
        )

    traitsview= View(VGroup(
                         Include('yamlgroup'),              
                         Include('filegroup'),                     
                         ),                     
                     resizable=True, 
                     )