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

