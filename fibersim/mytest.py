from traits.api import *
from traitsui.api import *
from chaco.api import Plot, ToolbarPlot, ArrayPlotData
from enable.api import ComponentEditor
from numpy import array
from numpy.random import rayleigh

class Test(HasTraits):
	a=Int(50)
	b=Int(20)

	ourdata=Instance(ArrayPlotData)    #ArrayPlotData is a special format for data that Plot objects recognize
	ourplot=Instance(Plot)

	arraytrait=Array()

	regen=Button

	traits_view=View(
			 HGroup(
				   VGroup(				  
					Item('regen'), Item('ourplot', editor=ComponentEditor()),
					),
			Item('ourdata', style='custom'), 
			     layout='tabbed'),
			resizable=True)

	def _arraytrait_default(self):
		return rayleigh(scale=15.0, size=1000)

	def _ourdata_default(self):
		arraydata=ArrayPlotData()  #Opening an empty arrayplotdataobject
		arraydata.set_data('test', self.arraytrait)

		return arraydata

	def _ourplot_default(self):
		myplot = ToolbarPlot(self.ourdata)
		myplot.plot( ('test'), color='green'   )

		return myplot

	def _regen_fired(self):
		newdata=rayleigh(scale=15.0, size=1000)
		### FIND DATA MAX  ###
		# self.data_max=...
		self.ourdata.set_data('test', newdata)

#	def _arraytrait_changed(self):
#		self.ourdata.set_data('test', self.arraytrait)
#		self.ourplot.request_redraw()


testobject=Test()
testobject.configure_traits()
