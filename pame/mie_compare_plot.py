from enable.api import Component, ComponentEditor
from traits.api import HasTraits, Instance, on_trait_change
from traitsui.api import Item, Group, View
from chaco.api import GridContainer, Plot, ToolbarPlot
from basicplots import ScatterView 

##########
# Don't feel like doing it now, but this could be a very general program
# If I pass in objects and the extended trait name that corresponds to the plot
# It would instantly make a multiplot 
# Aka  Objs=[ {Obj1:'myplot', Obj3:'dumbplot'}  ]
# For object in Objs, container.add(Objs[object]) 

class MieComparePlot(HasTraits):
	''' Developed 4_14_12, container object that stores two instances of plots and a creates
	    a third plot to combine both plots.  Especially useful for comparing scattering cross section
	    plots for full nanoparticles and composite nanoparticles '''

#	Mie1=Instance(ScatterView)  #Try making Plot if doesn't work
#	Mie2=Instance(ScatterView)

#	plot1=DelegatesTo('Mie1', prefix='sigplot')
#	plot2=DelegatesTo('Mie1', prefix='sigplot')

	plot1=Instance(ToolbarPlot)

	def _plot1_default(self): return ToolbarPlot()

	def _plot1_changed(self): 
		print 'changed in mie_compare'

		print self.plot1

     #   container = GridContainer(padding=40, fill_padding=True,
      #                        bgcolor="lightgray", use_backbuffer=True,
       #                       shape=(2,3), spacing=(20,20))
#	TotalPlot=Instance(Component)


        traits_view=View(
		Item('plot1',show_label=False, editor=ComponentEditor()),
                ),

	
	        
#container.add(plot)


if __name__ == '__main__':
	MieComparePlot().configure_traits()

