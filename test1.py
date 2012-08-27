from traits.api import *
from traitsui.api import *

class test(HasTraits):
	valid_list = List
        framesize = Enum(values='valid_list')   #THIS IS HOW YOU DEFER A LIST OF VALUES TO ENUM

	def _valid_list_default(self): return [1,2,34,45]

test().configure_traits()
