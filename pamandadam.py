from traits.api import *
from traitsui.api import *

class Love(HasTraits):
	rent=Float(2000)
	food=Float(250)
	livingexp=Float(300)
	loans=Float(340)
	total=Property(Float, depends_on='rent, food, livingexp')
	diff=Property(Float, depends_on='total, adaminc, paminc')

	adaminc=Float(2200)
	paminc=Float(1000)


	def _get_total(self): return self.rent + self.food +self.livingexp + self.loans
	def _get_diff(self): return (self.adaminc + self.paminc) - self.total

	view=View(
		HGroup(Item('rent'), Item('food'), Item('livingexp'), Item('loans')),
		HGroup(Item('adaminc'), Item('paminc')),
		HGroup(Item('total'), Item('diff')),
		)





Love().configure_traits()
