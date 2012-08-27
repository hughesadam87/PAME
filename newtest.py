from traits.api import *
from traitsui.api import *

class Test(HasTraits):
	a=Int()
	b=Float()
	traits=Str()

	def _traits_default(self): return str('a','b')

	@on_trait_change('traits')
	def ya(self):	
		print 'ya'

Test().configure_traits()
