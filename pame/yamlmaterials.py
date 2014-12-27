from traits.api import Str, HasTraits, Instance, Button, implements,\
     File, Property, Bool, Any, Enum
from traitsui.api import View, Item, Group, Include
from interfaces import IMaterial, IAdapter
from simple_materials_adapter import ABCFileAdapter
from material_files import ABCExternal
import numpy as np

import yaml

class YamlMaterial(ABCExternal):
    """ """

    file_spec_unit = Str('Micrometers')        

    # New traits
    datatype = Enum(['nk','k'])
    datastring = Str  #This is actual data that yamel gets as str

    def _datastring_changed(self):
        """ THIS HANDLES MAIN EVENT! 
        1. Read file Data 
        2. Convert Unit 
        3. Interpolate
        """    
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

        # Convert unit
        self.convert_unit()

        #Interpolate
        self.update_interp()

class YamlAdapter(ABCFileAdapter):
    """ Adapter to parse yaml.dump and figure out if experimental data, or 
    which type of model (2-8) and call corresponding material. 
    """

    implements(IAdapter)

    source=Str('YAML-encoded datafile')
    notes=Str('Not Found')
    REFERENCES = Str('Not Found')
    DATA = Any()
    COMMENTS = Str('Not Found')
    FORMULA = Any

    _is_model = Property(Bool)

    def _get__is_model(self):
        """ If yaml has a FORMULA key, this is a model. """
        if self.FORMULA:
            return True
        else:
            return False


    # CALL THIS LATER ON SELECTION
    def parse_file(self):
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


    def populate_object(self): 
        """Method used to instantiate an object to conserve resources"""

        if self._is_model:
            print 'THIS IS A MODEL'
            raise NotImplementedError('YAML models not hooked up yet' % datatype)


        else:
            print 'THIS IS NOT A MODEL'
            datatype = self.DATA['type']
            data = self.DATA['data']
            self.matobject = YamlMaterial(datastring=data, datatype=datatype)
            print self.DATA

#        self.matobject=self.BasicMaterial()


    # VIEW
    basicgroup=Group(
        Item('name', style='readonly'),   #THESE ARENT READ ONLY!
        Item('source', style='readonly'),
        Item('REFERENCES', style='readonly'),
        Item('FORMULA', style='readonly'),
        Item('preview'), 
        Item('openfile')

    )

    traitsview= View(Include('basicgroup'),              
                     resizable=True, width=400, height=200)


if __name__ == '__main__':
    f = YamlAdapter(file_path = '/home/glue/Desktop/fibersim/pame/data/RI_INFO/main/Ag/Johnson.yml')
#    f = YamlAdapter(file_path = '/home/glue/Desktop/fibersim/pame/data/RI_INFO/glass/schott/N-BASF2.yml')
#    f = YamlAdapter(file_path = '/home/glue/Desktop/fibersim/pame/data/RI_INFO/glass/schott/F2.yml')
    f.parse_file()
    f.populate_object()
    f.configure_traits()