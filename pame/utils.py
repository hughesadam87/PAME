# DynamicRange Imports:
from traits.api import HasPrivateTraits, Int, Range, Int
from traitsui.api import View, Group, Item, Label, RangeEditor
from numpy.lib import scimath as SM
import numpy as np


# MATH UTILITIES
# --------------
def complex_n_to_e(narray): 	
    """ Return complex dielectric given index of refraction given. """    
    earray = np.empty(narray.shape, dtype='complex')  
    nr = narray.real
    nk = narray.imag          
    earray.real = nr**2 -nk**2
    earray.imag = 2.0*nr*nk
    return earray

def complex_e_to_n(earray): 
    """ Return complex index of refraction given complex dielectric"""
    return SM.sqrt(earray) 
 
#https://github.com/enthought/traitsui/blob/master/examples/demo/Dynamic_Forms/dynamic_range_editor.py   
#http://stackoverflow.com/questions/9956167/change-property-parameter-from-within-class-constructor-python-traits/28286878#28286878
class DynamicRange( HasPrivateTraits ):
    """ Defines an editor for dynamic ranges (i.e. ranges whose bounds can be
        changed at run time).  ALL CREDIT TO JONATHAN MARCH, Enthought
    """
    value = Int
    low = Int(0.0)
    high = Int(50)
    
    # Traits view definitions:
    traits_view = View(Item('value', show_label=False, 
                            editor = RangeEditor( 
                                low_name    = 'low',
                                high_name   = 'high',
                                format      = '%.1f',
                                label_width = 28,
                                mode        = 'auto' )                            
                            )
                       )

#http://stackoverflow.com/questions/4287209/sort-list-of-strings-by-integer-suffix-in-python
def stepsort(the_list, separator='_'):
    """ Sort a list of items separated by an underscore like:
    's_1, s_3, s_5, s_4, s_10' correclty based on suffix.
    """
    return sorted(the_list, key = lambda x: int(x.split("_")[1]))

#http://stackoverflow.com/questions/28131446/get-nested-arrays-out-of-a-dictionary
def flatten_dict(d, *types):
    """ Flatten a dictionary {a:{b:c}} of arbitrary depths and
    return {'a.b': c}.  Types aregument filters values, so only will
    retain c if c is an array, or an int or so forth."""
    node_map = {}
    node_path = [] 
    def nodeRecursiveMap(d, node_path): 
        for key, val in d.items():
            if type(val) in types: 
                node_map['.'.join(node_path + [key])] = val 
            if type(val) is dict: 
                nodeRecursiveMap(val, node_path + [key])
    nodeRecursiveMap(d, node_path)
    return node_map

#http://stackoverflow.com/questions/28140794/enthought-traits-hastraits-class-as-a-nested-dictionary/28145345#28145345

# DEPCRECATED!  No longer use this for Pame main panel since plots encapsulate
# themselves
def flatten_traitobject(traitobject, *types, **kwargs):
    """ Flatten a trait object, return dictionary.  Use ignore keyword
    to pass over trait names that might cause recursion errors.  For example,
    the mview trait has a reference back to model.  This will cause recursion 
    loop between Material and Mview, so ignore it.
    """
    node_map = {}
    node_path = [] 
    ignore = kwargs.pop('ignore', [])
    def nodeRecursiveMap(traitobject, node_path): 
        for key in traitobject.editable_traits():
            val = traitobject.get(key)[key]
            for type in types:
                if isinstance(val, types[0]):
                    node_map['.'.join(node_path + [key])] = val 
            try:
                
                if key not in ignore:
                    nodeRecursiveMap(val, node_path + [key])
            except (AttributeError, TypeError):
                pass
    nodeRecursiveMap(traitobject, node_path)
    return node_map

#http://stackoverflow.com/questions/3797957/python-easily-access-deeply-nested-dict-get-and-set
class AttrDict(dict):
    def __init__(self, value=None):
        if value is None:
            pass
        elif isinstance(value, dict):
            for key in value:
                self.__setitem__(key, value[key])
        else:
            raise TypeError, 'expected dict'

    def __setitem__(self, key, value):
        if '.' in key:
            myKey, restOfKey = key.split('.', 1)
            target = self.setdefault(myKey, AttrDict())
            if not isinstance(target, AttrDict):
                raise KeyError, 'cannot set "%s" in "%s" (%s)' % (restOfKey, myKey, repr(target))
            target[restOfKey] = value
        else:
            if isinstance(value, dict) and not isinstance(value, AttrDict):
                value = AttrDict(value)
            dict.__setitem__(self, key, value)
            

    def __getitem__(self, key):
        if '.' not in key:
            return dict.__getitem__(self, key)
        myKey, restOfKey = key.split('.', 1)
        target = dict.__getitem__(self, myKey)
        if not isinstance(target, AttrDict):
            raise KeyError, 'cannot get "%s" in "%s" (%s)' % (restOfKey, myKey, repr(target))
        return target[restOfKey]

    def __contains__(self, key):
        if '.' not in key:
            return dict.__contains__(self, key)
        myKey, restOfKey = key.split('.', 1)
        target = dict.__getitem__(self, myKey)
        if not isinstance(target, AttrDict):
            return False
        return restOfKey in target

    def setdefault(self, key, default):
        if key not in self:
            self[key] = default
        return self[key]
            
    
    # Will allow compatibility with pickle
    def __getattr__(self, key):
        if key.startswith('__') and key.endswith('__'):
            return super(AttrDict, self).__getattr__(key)
        return self.__getitem__(key)

    __setattr__ = __setitem__


if __name__ == '__main__':
    DynamicRange().configure_traits()