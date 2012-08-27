from enable.api import Component, ComponentEditor
from traits.api import *
from traitsui.api import *
from numpy.random import poisson
from numpy import empty
from chaco.api import ArrayPlotData, Plot

class Basic(HasTraits):
	data=Instance(ArrayPlotData)         
	myplot=Instance(Plot)

	def _data_default(self): 
		'''Populate with empty data points, which are overwritten when the user changes simulation'''
		emptyarray=ArrayPlotData()
		emptyarray.set_data('TestData', empty(100))
		return emptyarray

	def _myplot_default(self): 
		myplot=Plot(self.data)
		myplot.plot('TestData')
		return myplot
	
	traits_viev=View(
			Item('myplot', style='custom', editor=ComponentEditor())
			)
	

class Simulator(HasTraits):
	Basic_placeholder=Instance(Basic,())
	data_dic=Dict
	data_keys=Property(List, depends_on='data_dic')
	selected_sim=Str  #Set by list string editor


	@cached_property
	def _get_data_keys(self): return self.data_dic.keys()

	def _selected_sim_changed(self): 
		selected_data=self.data_dic[self.selected_sim]
		self.Basic_placeholder.data.set_data('TestData',selected_data)

	traits_view=View(
			Item('data_keys', editor=ListStrEditor(selected='selected_sim'), label='Trials'),
			Item('Basic_placeholder', style='custom', editor=InstanceEditor(), show_label=False)
			)

### Generate random data ###

data_dic={}
for i in range(50):
	data_dic['Trial'+str(i)]=poisson(lam=i, size=100)
Simulator(data_dic=data_dic).configure_traits()
		


