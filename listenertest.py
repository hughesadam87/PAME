from traits.api import *
from traitsui.api import *

class Test(HasTraits):
	string=Str("Change me")

class Main(HasTraits):
	test=Instance(Test,())
	string=DelegatesTo('test')

	listener_string=Str
	property_string=Property(depends_on='string')

        @on_trait_change('string')
	def update_listener_string(self): 
		print 'Updating new string through on_trait_change_listener'
		self.listener_string=self.string

	@cached_property
	def _get_property_string(self): 
		print 'Updating new string through properties event listener'
		return self.string

	traits_view=View( Item('string', label='Original String'),Item('listener_string', style='readonly'), Item('property_string', style='readonly'), width=500, height=500)

Main().configure_traits()
