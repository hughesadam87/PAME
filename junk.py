from traits.api import *
from traitsui.api import *

class test(HasTraits):
	mybutton=Button("click")

	def _mybutton_fired(self):
		print 'just fired'

	traits_view=View(
			Item('mybutton')
			)
a=test()
print 'here'
a._mybutton_fired()
print 'new try'
a.mybutton=True
print 'jew'
a.configure_traits()
