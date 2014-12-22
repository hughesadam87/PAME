from traits.api import *

class A(HasTraits):
    c=Dict(Str, Dict)
    
c={'2':{3:3}}
b=A(c=c)

print b