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
def flatten_traitobject(traitobject, *types):
    """ Flatten a trait object, return dictionary"""
    node_map = {}
    node_path = [] 
    def nodeRecursiveMap(traitobject, node_path): 
        for key in traitobject.editable_traits():
            val = traitobject.get(key)[key]
            for type in types:
                if isinstance(val, types[0]):
                    node_map['.'.join(node_path + [key])] = val 
            try:
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