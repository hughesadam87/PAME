from traits.api import *

class A(HasTraits):
    a=Instance(Str)
    
test=A()
print test.a