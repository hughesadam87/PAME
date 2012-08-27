from traits.api import *
from traitsui.api import *
import copy

class A(HasTraits):
	a=Float(10)

class B(HasTraits):
	b=Float(20)

class Test(HasTraits):
   restore_point=Dict  #Place holder for key/value pairs
   a=Instance(A,())
   b=Instance(B,())
   make_restore=Button
   restore_all=Button

   def _make_restore_fired(self): self.restore_point={'a':copy.copy(self.a), 'b':copy.copy(self.b), 'test':copy.copy(self)}

   def _restore_all_fired(self):       #Button to set program to original values
#	self.a=self.restore_point['a']
#	self.b=self.restore_point['b']
	self=self.restore_point['test']

   traits_view=View(Item('a', style='custom'), Item('b', style='custom'), Item('restore_point'), Item('make_restore'), Item('restore_all'))

Test().configure_traits()
