from enable.api import Component, ComponentEditor
from traits.api import HasTraits, Instance, Array, Property, CArray, Str, Float, Tuple, Any, Dict, List, Enum, Bool, cached_property
from traitsui.api import Item, Group, View, Tabbed, Action, HGroup, InstanceEditor, VGroup, ListStrEditor

# Chaco imports
from chaco.api import ArrayPlotData, Plot, AbstractPlotData, PlotAxis, HPlotContainer, ToolbarPlot
from chaco.tools.api import PanTool, ZoomTool
from numpy import where

class MultiView(HasTraits):
	'''Used to store arbitrary plots and selection based on key/plot input'''
	host=Str('Host Unkown')   #Object which calls this, only needed for naming
	nameplot=Dict  #Dictionary with plot designator/name as key, plot itself as value
	plotname=Property(List, depends_on='nameplot, alphabetize')
	chooseplot=Enum(values='plotname')
	selectedplot=Property(depends_on='chooseplot')
	alphabetize=Bool(True)

	
	@cached_property
	def _get_plotname(self): 
		print 'nameplot passed'
		keys=self.nameplot.keys()
		if self.alphabetize == True:
			keys.sort()
		return keys 

	def _get_selectedplot(self): return self.nameplot[self.chooseplot]

	view = View( 
			HGroup(
				Item('host', show_label=False, style='readonly'),
				Item('chooseplot', label='Choose selected plot', show_label=False, style='simple'),
				Item('alphabetize', label='Order objects alphabetically'),
				),
			Item('selectedplot', show_label=False, editor=ComponentEditor()),
			width=800, height=600, resizable=True   )


class MultiViewTest(HasTraits):
	'''Used to store arbitrary plots and selection based on key/plot input'''
	host=Str('Host Unkown')   #Object which calls this, only needed for naming
	nameplot=Dict  #Dictionary with plot designator/name as key, plot itself as value
	plotname=Property(List, depends_on='nameplot')
	chooseplot=Enum(values='plotname')

	selectedplot=Property(depends_on='chooseplot')

	def _get_plotname(self): 
		keys=self.nameplot.keys()
		keys.sort()
		return keys 

	def _get_selectedplot(self): return self.nameplot[self.chooseplot]

	view = View( 
			HGroup(
				Item('host', show_label=False, style='readonly'),
				Item('chooseplot', label='Choose selected plot', show_label=False, style='simple'),
				),
			Item('selectedplot', show_label=False, editor=InstanceEditor(), style='custom'),
			width=800, height=600, resizable=True   )

class MaterialView(HasTraits):

        eplot = Instance(Plot)
        nplot = Instance(Plot)             #Traits are populated on update usually

        data = Instance(AbstractPlotData)

	xarray=Array()
	earray=CArray()
	narray=CArray()
	xunit=Str()
	ereal=Property(Array,depends_on=["earray"])     #Storing as traits just in case I want to have the array view     
	eimag=Property(Array,depends_on=["earray"])
	nreal=Property(Array,depends_on=["narray"])
	nimag=Property(Array,depends_on=["narray"])

        ToggleReal=Action(name="Toggle Real", action="togimag")
	ToggleImag=Action(name="Toggle Imaginary", action="togreal")

        view = View(
        Tabbed(
            Item('eplot', editor=ComponentEditor(), dock='tab', label='Dielectric'),
            Item('nplot', editor=ComponentEditor(), dock='tab', label='Index'), 
            show_labels=False         #Side label not tab label
        ),
	width=800, height=600,  buttons=['Undo'],             #Buttons work but only respond to trait changes not plot changes like zoom and stuff
        resizable=True
        )


        def _get_ereal(self): return self.earray.real
        def _get_eimag(self): return self.earray.imag
        def _get_nreal(self): return self.narray.real
        def _get_nimag(self): return self.narray.imag

        def create_plots(self):
	        self.eplot = ToolbarPlot(self.data)
		self.nplot= ToolbarPlot(self.data)
	        self.eplot.plot(("x", "er"), name="ereal", color="red", linewidth=4)
		self.eplot.plot(("x", "er"), name="ereal data", color="orange", type='scatter', marker_size=2)
	        self.eplot.plot(("x", "ei"), name="eimag", color="green", linewidth=4)
		self.eplot.plot(("x", "ei"), name="eimag data", color="orange", type='scatter', marker_size=2)

	        self.nplot.plot(("x", "nr"), name="nreal", color="red", linewidth=4)
		self.nplot.plot(("x", "nr"), name="nreal data", color="orange", type='scatter', marker_size=2)
	        self.nplot.plot(("x", "ni"), name="nimag", color="green", linewidth=4)
		self.nplot.plot(("x", "ni"), name="nimag data", color="orange", type='scatter', marker_size=2)	

		self.add_tools_title(self.eplot, 'Dielectric ')
		self.add_tools_title(self.nplot, 'Index of Refraction ')

	def add_tools_title(self, plot, title_keyword):
		'''Used to add same tools to multiple plots'''
	        plot.title = title_keyword + 'vs. Wavelength'
        	plot.legend.visible = True

     		bottom_axis = PlotAxis(plot, orientation='bottom', title=self.xunit, label_color='red', label_font='Arial', tick_color='green', tick_weight=1)
        	vertical_axis = PlotAxis(plot, orientation='left',
       	                        title='Relative'+str(title_keyword))

	        plot.underlays.append(vertical_axis)
        	plot.underlays.append(bottom_axis)

        	# Attach some tools to the plot
        	plot.tools.append(PanTool(plot))
        	zoom = ZoomTool(component=plot, tool_mode="box", always_on=False)
        	plot.overlays.append(zoom)


	def togimag(self):      #NOT SURE HOW TO QUITE DO THIS
		print 'hi'

	def togreal(self):
		print 'hi'

        def update(self, xarray, earray, narray, xunit):    
		'''Method to update plots; draws them if they don't exist; otherwise it simply updates the data'''     
		self.xunit=xunit ;  self.xarray=xarray
		self.earray=earray; self.narray=narray
		if self.data == None:
			self.data = ArrayPlotData(x=self.xarray, er=self.ereal, nr=self.nreal, ei=self.eimag, ni=self.nimag)
			self.create_plots()
		else:
			self.update_data()

	def update_data(self):
		self.data.set_data('x',self.xarray) ; self.data.set_data('er', self.ereal)
		self.data.set_data('nr', self.nreal) ; self.data.set_data('ei', self.eimag)
		self.data.set_data('ni', self.nimag)
		self.eplot.request_redraw() ; self.nplot.request_redraw()

	####### USED FOR SIMULATION STORAGE MOSTLY #####

	def get_sexy_data(self):
		'''Returns the data in a list that can be immediately read back in another instance of simview.  Note this is not the same as the arrayplotdata getdata() function'''
		return [self.xarray, self.earray, self.narray, self.xunit]

	def set_sexy_data(self, data_list):
		'''Takes in data formatted deliberately from "get_sexy_data" and forces an update'''
		self.update(data_list[0], data_list[1], data_list[2], data_list[3])


class MaterialViewList(HasTraits):
	mvl_dic=Dict #Dictionary of array data specifically suited for simview
	mvl_keys=Property(List, depends_on='mvl_dic')
	selected_variable=Any  #Basically key from mvl_keys
	MView=Instance(MaterialView,())#Instance Simview

	def _selected_variable_changed(self):
		print 'you changed your selection'
		self.MView.set_sexy_data(self.mvl_dic[self.selected_variable])

	def _get_mvl_keys(self): 
		vals=self.mvl_dic.keys()#.sort()  ##Sorting I think only works for numbers
		vals.sort()
		return vals


	traits_view=View(VGroup(
			Item('mvl_keys', editor=ListStrEditor(selected='selected_variable')), Item('MView', show_label=False, style='custom'),
  	 			 ), resizable=True
			 )


class ScatterView(HasTraits):
	'''Used to view scattering cross sections and other relevant parameters from mie scattering program'''

        sigplot = Instance(Plot)        #Scattering cross section
        data = Instance(AbstractPlotData)

	xarray=Array()
	xunit=Str()

	extarray=Array()    #Scattering, extinction, absorption
	scatarray=Array()
	absarray=Array()

	exmax=Tuple(0,0)     #Technically properties but don't update with view for some reason
	absmax=Tuple(0,0)    #Pukes if 0,0 default not provided, but this is probably due to my program not tuple trait
	scatmax=Tuple(0,0)

        view = View(
            Item('sigplot', editor=ComponentEditor(), dock='tab', label='Cross Section', show_label=False),
	    HGroup(
   	    Item('exmax', style='readonly', label='Extinction Max'),
     	    Item('absmax', style='readonly', label='Absorbance Max'),
   	    Item('scatmax', style='readonly', label='Scattering Max'),
	          ),
            width=800, height=600,
        resizable=True
        )

	def get_max_xy(self, array):
		rounding=3  #Change for rounding of these 
		value=max(array)
		index=int(where(array==value)[0])  #'where' returns tuple since is can be used on n-dim arrays
		x=self.xarray[index]
		return (round(x,rounding), round(value,rounding))

        def create_plots(self):
	        self.sigplot = ToolbarPlot(self.data)
	        self.sigplot.plot(("x", "sig"), name="Scattering", color="green", linewidth=4)
		self.sigplot.plot(("x", "sig"), name="Scattering", color="green", type='scatter', marker_size=2)

	        self.sigplot.plot(("x", "absorb"), name="Absorbance", color="blue", linewidth=4)
		self.sigplot.plot(("x", "absorb"), name="Absorbance", color="blue", type='scatter', marker_size=2)

	        self.sigplot.plot(("x", "ext"), name="Extinction", color="red", linewidth=4)
		self.sigplot.plot(("x", "ext"), name="Extinction", color="red", type='scatter', marker_size=2)

		self.add_tools_title(self.sigplot, 'Extinction')

	def add_tools_title(self, plot, title_keyword):
		'''Used to add same tools to multiple plots'''
	        plot.title = title_keyword + 'vs. Wavelength'
        	plot.legend.visible = True

     		bottom_axis = PlotAxis(plot, orientation='bottom', title=self.xunit, label_color='red', label_font='Arial', tick_color='green', tick_weight=1)
        	vertical_axis = PlotAxis(plot, orientation='left',
       	                        title=str(title_keyword))

	        plot.underlays.append(vertical_axis)
        	plot.underlays.append(bottom_axis)

        	# Attach some tools to the plot
        	plot.tools.append(PanTool(plot))
        	zoom = ZoomTool(component=plot, tool_mode="box", always_on=False)
        	plot.overlays.append(zoom)

        def update(self, xarray, extarray, scatarray, absarray, xunit):         
		self.xunit=xunit ;self.xarray=xarray
		self.extarray=extarray ; self.absarray=absarray ; self.scatarray=scatarray

		if self.data == None:
			self.data = ArrayPlotData(x=xarray, sig=scatarray, absorb=absarray , ext=extarray)
			self.create_plots()
		else:
			self.update_data()

		self.exmax=self.get_max_xy(self.extarray)
		self.absmax=self.get_max_xy(self.absarray)
		self.scatmax=self.get_max_xy(self.scatarray)

	def update_data(self):
		self.data.set_data('x',self.xarray) ; self.data.set_data('sig', self.scatarray)
		self.data.set_data('absorb', self.absarray) ; self.data.set_data('ext', self.extarray)
		self.sigplot.request_redraw()
	


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


	f.configure_traits()


