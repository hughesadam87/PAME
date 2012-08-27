from enable.api import Component, ComponentEditor
from traits.api import HasTraits, Instance, Array, Property, CArray, Enum, Str, List, Dict, Any, cached_property
from traitsui.api import Item, Group, View, Tabbed, Action, VGroup, TableEditor, ObjectColumn, ExpressionColumn, ListStrEditor, InstanceEditor, ListEditor
from chaco.example_support import COLOR_PALETTE  #Only ten colors long
from interfaces import IMaterial

# Chaco imports
from chaco.api import ArrayPlotData, Plot, AbstractPlotData, ToolbarPlot
from chaco.tools.api import PanTool, ZoomTool

class SimView(HasTraits):

	name=Str('Test')

        Refplot = Instance(Plot)
        Transplot = Instance(Plot)             #Traits are populated on update usually
	Avgplot= Instance(Plot)

	chooseplot=Enum('Reflectance', 'Transmittance', 'Averaged Reflectance')   #For second view
	selected=Property(depends_on='chooseplot')

        data = Instance(ArrayPlotData)

	xarray=Array()
	angles=Array()
	RefArray=Array()
	TransArray=Array()
	AvgArray=Array()

        traits_view = View(
        Tabbed(
            Item('Refplot', editor=ComponentEditor(), dock='tab', label='Reflectance'),
            Item('Transplot', editor=ComponentEditor(), dock='tab', label='Transmittance'), 
	    Item('Avgplot', editor=ComponentEditor(), dock='tab', label='Theta averaged'),		
            show_labels=False         #Side label not tab label
        ),
	width=800, height=600,
        resizable=True
        )

	view2 = View( Item('chooseplot', label='Choose selected plot', show_label=False, style='custom'),
			Item('selected', show_label=False, editor=ComponentEditor()),
			width=800, height=600, resizable=True   )

	def _get_selected(self): 
		if self.chooseplot=='Reflectance': return self.Refplot
		elif self.chooseplot=='Transmittance': return self.Transplot
		elif self.chooseplot=='Averaged Reflectance': return self.Avgplot

        def create_plots(self):
	        self.Refplot = ToolbarPlot(self.data)
		self.Transplot= ToolbarPlot(self.data)
		self.Avgplot= ToolbarPlot(self.data)

		for i in range(self.angles.shape[0]):
			if i >= 10:
				color='blue'
			else:
				color=tuple(COLOR_PALETTE[i])
			angle=self.angles[i]
			self.data.set_data(('RTheta' + str(i)), self.RefArray[i,:])
			self.Refplot.plot( ("x", ('RTheta' + str(i))), name=('Angle'+ str(angle) ), color=color)

			self.data.set_data(('TTheta' + str(i)), self.TransArray[i,:])
			self.Transplot.plot( ("x", ('TTheta' + str(i))), name=('Angle'+str(angle) ), color=color)
		self.Avgplot.plot( ("x", 'Avg'), name='Averaged Angles', color='red' )

		self.add_tools_title(self.Refplot, 'Reflectance')
		self.add_tools_title(self.Transplot, 'Transmittance')
		self.add_tools_title(self.Avgplot, 'Avg')

	def add_tools_title(self, plot, title):
		'''Used to add same tools to multiple plots'''
	        plot.title = title
        	plot.padding = 50
        	plot.legend.visible = True

        	# Attach some tools to the plot
        	plot.tools.append(PanTool(plot))
        	zoom = ZoomTool(component=plot, tool_mode="box", always_on=False)
        	plot.overlays.append(zoom)

        def update(self, xarray, anglearray, RefArray, TransArray, AvgArray):   
		self.xarray=xarray;		self.angles=anglearray
		self.RefArray=RefArray;		self.TransArray=TransArray
		self.AvgArray=AvgArray

		if self.data == None:
			self.data = ArrayPlotData(x=self.xarray, angs=self.angles, Ref=self.RefArray, Trans=self.TransArray, Avg=self.AvgArray)
			self.create_plots()
		else:
			self.update_data()

	def update_data(self):
		''' This is a set_data function, expect it sets all the data parameters at once'''
		self.data.set_data('x',self.xarray) ; self.data.set_data('angs', self.angles)
		self.data.set_data('Ref', self.RefArray) ; self.data.set_data('Trans', self.TransArray)
		self.data.set_data('Avg', self.AvgArray)
		self.Refplot.request_redraw(); self.Transplot.request_redraw(); self.Avgplot.request_redraw()

	### Probably a smart way to change all of these update methods to a simplier dictionary notation ###

	def get_sexy_data(self):
		'''Returns the data in a list that can be immediately read back in another instance of simview.  Note this is not the same as the arrayplotdata getdata() function'''
		return [self.xarray, self.angles, self.RefArray, self.TransArray, self.AvgArray]

	def set_sexy_data(self, data_list):
		'''Takes in data formatted deliberately from "get_sexy_data" and forces an update'''
		self.update(data_list[0], data_list[1], data_list[2], data_list[3], data_list[4])

class SimViewList(HasTraits):
	svl_dic=Dict #Dictionary of array data specifically suited for simview
	svl_keys=Property(List, depends_on='svl_dic')
	selected_variable=Any  #Basically key from svl_keys
	Sview=Instance(SimView,())#Instance Simview

	def _selected_variable_changed(self):
		print 'you changed your selection'
		self.Sview.set_sexy_data(self.svl_dic[self.selected_variable])

	def _get_svl_keys(self): 
		vals=self.svl_dic.keys()#.sort()  ##Sorting I think only works for numbers
		vals.sort()
		return vals


	traits_view=View(VGroup(
			Item('svl_keys', editor=ListStrEditor(selected='selected_variable')), Item('Sview', show_label=False, style='custom'),
  	 			 ), resizable=True
			 )


class DoubleView(HasTraits):
	from layer_plotter import MultiView
	DV=List(IMaterial)
	my_selection=Instance(IMaterial)
	alview=Property(depends_on='my_selection')
	get2=Property(depends_on='my_selection')
	mytra=Property(depends_on='my_selection')

	@cached_property
	def _get_alview(self): 
		if self.my_selection is not None:
		#	return hex(id(self.my_selection.eplot))
			return self.my_selection
	@cached_property
	def _get_get2(self):
		if self.my_selection is not None:
			print 'can clone', self.my_selection.copyable_trait_names()
			return self.my_selection.mview

	@cached_property
	def _get_mytra(self): 	
		if self.my_selection is not None:
			return self.my_selection.trait_names()
	


	traits_view=View( Item('DV', editor=ListStrEditor(selected='my_selection')), 
			Item('alview', style='simple', editor=InstanceEditor()), Item('get2', style='simple', editor=InstanceEditor()), Item('get2', style='custom', editor=InstanceEditor()),
			resizable=True, width=800, height=600)


