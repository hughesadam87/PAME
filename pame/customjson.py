""" Json encoding/decoding of dictionary with arbitrary array datatypes.  Thanks to hpaulj:
http://stackoverflow.com/questions/27909658/json-encoder-and-decoder-for-complex-numpy-arrays/27913569#27913569
"""
import base64
import json
import numpy as np
from collections import OrderedDict

class CustomJsonError(Exception):
    """ """

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        """
        if input object is a ndarray it will be converted into a dict holding dtype, shape and the data base64 encoded
        """
        if isinstance(obj, np.ndarray):
            data_b64 = base64.b64encode(obj.data)
            if obj.dtype == np.object:
                raise CustomJsonError('Cannot encode json object types!')
            return dict(__ndarray__=data_b64,
                        dtype=str(obj.dtype),
                        shape=obj.shape)
        # Let the base class default method raise the TypeError
        
#        elif isinstance(obj ,OrderedDict.OrderedDict):
#                return "{" + ",".join( [ self.encode(k)+":"+self.encode(v) for \
#                                         (k,v) in obj.iteritems() ] ) + "}"        
        return json.JSONEncoder(self, obj)


def json_numpy_obj_hook(dct):
    """
    Decodes a previously encoded numpy ndarray
    with proper shape and dtype
    :param dct: (dict) json encoded ndarray
    :return: (ndarray) if input was an encoded ndarray
    """
    if isinstance(dct, dict) and '__ndarray__' in dct:
        print 'hi in here woo', dct
        data = base64.b64decode(dct['__ndarray__'])
        return np.frombuffer(data, dct['dtype']).reshape(dct['shape'])
    return dct

# Overload dump/load to default use this behavior.
# MUST PASS FILE OBJECTS, NOT PATH STRINGS
def dumps(*args, **kwargs):
    kwargs.setdefault('cls', NumpyEncoder)
    return json.dumps(*args, **kwargs)

def loads(*args, **kwargs):
    kwargs.setdefault('object_hook', json_numpy_obj_hook)    
    return json.loads(*args, **kwargs)

def dump(*args, **kwargs):
    kwargs.setdefault('cls', NumpyEncoder)
    # Got tired of forgetting have to pass file object as first arg
    # so let it pass path as first argument
    args = list(args)
    if isinstance(args[1], basestring): #<--- In dump, args[1] is fp
        args[1] = open(args[1], 'w')
    return json.dump(*args, **kwargs)

def load(*args, **kwargs):
    kwargs.setdefault('object_hook', json_numpy_obj_hook)

    # Got tired of forgetting have to pass file object as first arg
    # so let it pass path as first argument
    args = list(args) 
    if isinstance(args[0], basestring): #<--- In load, args[0] is fp
        args[0] = open(args[0], 'r')
    return json.load(*args, **kwargs)

if __name__ == '__main__':
    
    data = np.arange(3, dtype=np.complex)
    
    one_level = {'level1': data, 'foo':'bar'}
    two_level = {'level2': one_level}
    
    dumped = dumps(two_level)
    result = loads(dumped)
    
    print '\noriginal data', data
    print '\nnested dict of dict complex array', two_level
    print '\ndecoded nested data', result


