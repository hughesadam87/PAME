from enable.api import Component, ComponentEditor
from traits.api import HasTraits, Instance, Array, Property, CArray, Str
from traitsui.api import Item, Group, View, Tabbed, Action

# Chaco imports
from chaco.api import ArrayPlotData, Plot, AbstractPlotData, PlotAxis, HPlotContainer
from chaco.tools.api import PanTool, ZoomTool
from layer_plotter import ScatterView


class DoubleScatterView(HasTraits):
	sv1=Instance(ScatterView)
	sv2=Instance(ScatterView)

	plot1=Instance(Plot)
	plot2=Instance(Plot)

        totalplot = Instance(Component)

        traits_view = View(
                    Group(
                        Item('totalplot', editor=ComponentEditor(),
                             show_label=False),
#			Item('plot1',editor=ComponentEditor()),
 #                       orientation = "vertical"),
                    ),resizable=True, title='Test'
                    )

       # def _totalplot_default(self):
        #	return self.create_plots()

	def create_plots(self):
		container = HPlotContainer()
		container.add(self.plot1)
		container.add(self.plot2)
		self.totalplot=container

	
	def update(self, sv1, sv2):
		self.sv1=sv1
		self.sv2=sv2
		self.plot1=self.sv1.sigplot
		self.plot2=self.sv2.sigplot
		self.create_plots()

if __name__ == '__main__':
	from mie_traits_delegated import *
	from material_traits_v3 import Drude_new, Disp_water, Constant, Sellmeir  #For testing purposes
	
	e=Drude_new(); f=Disp_water() ; g=Sellmeir()

	a=sphere_shell(CoreMaterial=e, MediumMaterial=f , ShellMaterial=g)
	b=sphere_full(CoreMaterial=e, MediumMaterial=f)


	f=DoubleScatterView(sv1=a.sview, sv2=b.sview)
#	f.update(sv1=a.sview, sv2=b.sview)
	print b.Cext	
	f.configure_traits()
