from traits.api import *

class Test(HasTraits):
	a=Int(2)
	b=Str('lol')

test=Test()
test.set({'a':32, 'b':'her'})
test.configure_traits()
