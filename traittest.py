from traits.api import *
from traitsui.api import *
from random import random
from traits.trait_base import xsetattr

class SubSubClass(HasTraits):
	foo=Float(32.3)

class SubClass(HasTraits):
	a=Float(1.0)
	c=Instance(SubSubClass,())

class Main(HasTraits):
	b=Float(2.0)
	sub=Instance(SubClass,())
        user_spec_traits=Str('sub.c.foo')

	set_random=Button

	def _set_random_fired(self): 
		split=self.user_spec_traits.split('.')
#		setattr( eval('self.'+".".join(split[:-1])), str(split[-1]), random() )
		xsetattr(self, self.user_spec_traits, random())
		xgetattr(self

	traits_view=View(
		        Item('user_spec_traits'),Item('b'), Item('sub', style='custom'), Item('set_random')
			)

Main().configure_traits()
