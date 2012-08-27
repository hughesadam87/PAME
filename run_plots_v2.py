from traits.api import HasTraits, Instance, DelegatesTo, Str, Enum, Property, \
		       Array, Dict, Int, cached_property, on_trait_change, implements,\
		       List, Str, Range, DelegatesTo
from traitsui.api import Item, View, HGroup, VGroup, Group, Include
from chaco.api import ArrayPlotData, ToolbarPlot, LabelAxis
from chaco.tools.api import BetterSelectingZoom, PanTool
from enable.api import ComponentEditor
from ct_interfaces import IPlot, IRunStorage

###
from numpy import array

class AbstractPlot(HasTraits):
	'''Plot with specific handlers and listeners to coordinate local and global
	   changes in the data controlled by the RunStorage class '''

	### Do I need a special object to store lines/plots apart from what is here? ###

	implements(IPlot)
	plot=Instance(ToolbarPlot)
	plothandler=Instance(IRunStorage)  #Must be initialized with this
	plot_title=Str('General Plot')
	color=Str('black')

	### Plot Axis Traits ###	
	x_axis_title=Str('Wavelength')  #For easy editing
	x_axis_samples=Int(10) #Controls number of labels on the x-axis

	t_axis_title=Str('Samples')  #For easy editing
	t_axis_samples=Int(10) #Controls number of labels on the x-axis

	### Runstorage Traits ###
	plotdata=Instance(ArrayPlotData)  #THESE DELEGATE TO PLOTHANDLER IN INHERETING CLASSES
	xlabel=List(Str)
	tlabel=List(Str)

	### Averaging and local sampling variables ###

	x_size=Property(Int, depends_on='xlabel')
	x_samp_style=Enum('Bifurcating', 'Any')
	x_samples=Property(Array, depends_on='x_size, x_samp_style') #This stores a list of i % 2 valid sampling increments
	x_spacing=Enum(values='x_samples', style='custom')
	x_effective=Property(Array, depends_on='x_samples, x_spacing')  

	t_size=Property(Int, depends_on='tlabel')  #THIS TRAIT AINT EVEN IN MY PROGRAM
	t_samp_style=Enum('Bifurcating', 'Any')
	t_samples=Property(Array, depends_on='t_size, t_samp_style') #This stores a list of i % 2 valid sampling increments
	t_spacing=Enum(values='t_samples', style='custom')
	t_effective=Property(Array, depends_on='t_samples, t_spacing')    #This is the effective list of indicies [1,3,5,7] for example depending on spacing variables

	### Local averaging traits ###

	x_avg=Int  #AVERAGING METHODS ARE NOT YET SUPPORTED!
	t_avg=Int  #Autoreset when twoD data is changed
	window=Enum('flat , hanning , hamming , bartlett , blackman')

	######

	def __init__(self, *args, **kwargs):
   	        super(AbstractPlot, self).__init__(*args, **kwargs)
		self.draw_plot()
		#self.update_lines()  ##  IF I CAN THINK OF A WAY TO TRIGGER THIS ON FIRST UPDATE, DON'T NEED THIS

	###Global Event Listeners
	@on_trait_change('plotdata')
	def redrawplot(self):  
		print 'Plot detects data change'
		self.draw_plot()
		self.update_lines()

	###Local Event listeners
	def _t_spacing_changed(self): self.update_lines()
	def _x_spacing_changed(self): self.update_lines()

	def update_lines(self):
		''' Function that will change sampling and other aspects of lines already drawn on plot'''
		pass

	### Averaging methods

#	def _x_bisect_spacing_changed(self):  CAN RESET LOCAL AVERAGING 
#		if self.x_bisect_spacing > 9:
#			self.x_bisect_spacing=3


	### Sampling properties/methods ###

	### Eventually make the bottom two properties the return of a single function to remove the duplication ###

	@cached_property
	def _get_x_size(self): return len(self.xlabel)

	@cached_property
	def _get_t_size(self): return len(self.tlabel)

	@cached_property
	def _get_x_samples(self): 
		if self.x_samp_style=='Bifurcating':  #Factorize by 2
			validx=[]
			i=self.x_size/2 #Ignores the first sampling size
			while i % 2 == 0:
				validx.append(i)
				i=i/2
			validx.append(1)
			validx.reverse()
		elif self.x_samp_style=='Any':  #CHANGE THIS LATER TO ACTUALLY PRESENT A LIST OF PERCENTS (1, 2, 3, 4 ETC...)
			validx=range(1, self.x_size/2) #Any valid number between 1 and half sample size
		return validx

	def _set_x_samples(self, x_samples):
		''' Global overrides through plothandler will pass these down '''
		self.x_samples=x_samples

	@cached_property
	def _get_t_samples(self): 
		if self.t_samp_style=='Bifurcating':
			validt=[]
			i=self.t_size/2 #Ignores the first sampling size
			while i % 2 == 0:
				validt.append(i)
				i=i/2
			validt.append(1)
			validt.reverse()
		elif self.t_samp_style=='Any':
			validt=range(1, self.t_size/2) #Any valid number between 1 and half sample size
		return validt

	@cached_property
	def _get_t_effective(self): return [i for i in range(0, self.t_size, self.t_spacing)]

	@cached_property
	def _get_x_effective(self): return [i for i in range(0, self.x_size, self.x_spacing)]

	### Aesthetic TRAITS ###

	def _plot_title_changed(self): 
		self.plot.title=self.plot_title
		self.plot.request_redraw() #Necessary 
	def _x_axis_title_changed(self): 
		self.plot.index_axis.title=self.x_axis_title
		self.plot.request_redraw()
	def _t_axis_title_changed(self): 
		self.plot.request_redraw()
		self.plot.value_axis.title=self.t_axis_title

#	def _x_axis_samples_changed(self):
#		self.plot.index_axis.positions=
		#  NEed to define new positions and labels accordingly, or maybe just redraw the axis
	
	### Leve this method intact.  When data changes, if I just dot plot.data=newdata-request_redraw it doesn't work!
	def draw_plot(self):
		'''Use this method as a way to either default a plot or call a full remake
		   for when a global datasource changes.  Datasource as an input also lets
		   me easily adapt plot behavior when using inheritance '''

		plot=ToolbarPlot(self.plotdata)  #CHANGE FOR OTHER PLOTS

		plot.title = self.plot_title
		plot.padding = 50
		plot.legend.visible=False

		plot.tools.append(PanTool(plot))
		zoom=BetterSelectingZoom(component=plot, tool_mode="box", always_on=False)
		plot.overlays.append(zoom)
		plot.index_axis=LabelAxis(plot, orientation='bottom', positions=range(self.x_axis_samples), 
				labels=['X0', 'X1', 'X2', 'X3', 'X4', 'X5'], resizable='hv',
				title=self.x_axis_title)

		plot.value_axis= LabelAxis(plot, orientation='left', positions=range(self.t_axis_samples),
				 labels=['t1', 't2', 't3', 't4','t5', 't6'], resizable='hv', 
				 title=self.t_axis_title)

		self.plot=plot
		return


	axis_traits_group=HGroup(
                                Item('x_axis_title'), Item('t_axis_title'), Item('plot_title')
				)

	sample_group=Group(
			 HGroup(Item('t_spacing'), Item('t_samp_style') )
			  )

	traits_view=View(
			Item('plot', editor=ComponentEditor(), show_label=False),
			Include('sample_group'),
			Include('axis_traits_group')
			)

class SpecPlot(AbstractPlot):
	plotdata=DelegatesTo('plothandler', prefix='specdata')

	def __init__(self, *args, **kwargs):
		''' Not necessary but keep in case I ever use multiple inheritance later '''
   	        super(SpecPlot, self).__init__(*args, **kwargs)

	def update_lines(self):
		print 'updating lines'

		### CHANGES PLOTS BASED ON LOCAL VARIABLES ###

		newplots=[self.tlabel[i] for i in self.t_effective]
		oldplots=[name for name in self.plot.plots]
		toadd=[plot for plot in newplots if plot not in oldplots]
		todelete=[plot for plot in oldplots if plot not in newplots]

	#	print 'zomg here', toadd, self.plotdata["x"]
	
		for name in todelete: self.plot.delplot(name)
		for name in toadd:    self.plot.plot(("x", name), name=name, color=self.color)

		self.plot.request_redraw()  #Needed so still works after zooming


class AbsPlot(AbstractPlot):
	''' Absorbance plot.  This requires a copy of the data to locally modify so this plot deviates from the methodology I put forward for abstractplots.  Namely,
	    a local arrayplotobject (plotdata trait) is stored and completely emptied and repopulated with each event.  Decided to just empty and refil because changes
            in the reference trait, and sampling traits would affect every single sampled line anyway!  When sampling the entire dataset, this plot is probably slower 
	    than its specdata counterparts because of the excess redraw events.'''

	def __init__(self, *args, **kwargs):
   	        super(AbsPlot, self).__init__(*args, **kwargs)

	plot_title=Str('Absorbance')

	### Note: Since absorbance needs to manipulator data, I actually sync a local copy of
	### of array plot data to my plot rather than the original data object ####	

	runstorage_data=DelegatesTo('plothandler', prefix='specdata')
	plotdata=Instance(ArrayPlotData, ())  #Must retain this traitname for plot defaults and things

	### Reference line traits ###
	low=Int(0)

	### THIS IS MESSED UP BECAUSE IT SHOULD BE THE LIST OF T_EFFECTIVES!!!!  AKA [1,4,7] AS THE VALID ONES
	ref_col=Enum(values='t_effective')  #This trips out if low is an integer and high is a string and high should be t_size-1

	def _runstorage_data_changed(self): 
		self.redrawplot()  #This ensures a new plot is created when the runstorage data object changes
		#Replot everything

	def _ref_col_changed(self):
		for i in self.t_effective: self.plotdata.set_data(self.tlabel[i], \
				   self.runstorage_data.get_data(self.tlabel[i])/self.runstorage_data.get_data(self.tlabel[self.ref_col]))  

#	@on_trait_change('ref_col, t_sampling, x_sampling')
	def update_lines(self):
		''' Unlike specplot and timeplot, this actually completely deletes all the lineplot renderers, rewrites the entire local dataarray, and replots everything'''
		#Delete entire dictionary and current lineplots
	#	for plot in self.plot.plots: self.plot.delplot(plot)
		oldplots=[name for name in self.plot.plots]

		for entry in self.plotdata.list_data(): self.plotdata.del_data(entry)  

		#Repopulate data object
		self.plotdata.set_data('x', self.runstorage_data.get_data('x') )
		for i in self.t_effective: self.plotdata.set_data(self.tlabel[i], \
					   self.runstorage_data.get_data(self.tlabel[i])/self.runstorage_data.get_data(self.tlabel[self.ref_col]))  	

		#Replot everything
		for name in self.plotdata.list_data(): 
			if name != 'x':
				self.plot.plot(("x", name), name=name, color=self.color)

		print self.plot.plots, 'number of plots'

		self.plot.request_redraw()  #Needed so still works after zooming

	traits_view=View(
			Item('plot', editor=ComponentEditor(), show_label=False),
			Include('sample_group'),
			Item('ref_col', label='Reference Column'),
			)



class TimePlot(AbstractPlot):
	'''Add desxcriptoin '''
	plot_title=Str('Temporal')
	plotdata=DelegatesTo('plothandler', prefix='timedata')

	def __init__(self, *args, **kwargs):
   	        super(TimePlot, self).__init__(*args, **kwargs)

	def update_lines(self):
		print 'updating lines'

		### CHANGES PLOTS BASED ON LOCAL VARIABLES ###

		newplots=[self.xlabel[i] for i in self.x_effective]
		oldplots=[name for name in self.plot.plots]
		toadd=[plot for plot in newplots if plot not in oldplots]
		todelete=[plot for plot in oldplots if plot not in newplots]

		for name in todelete: self.plot.delplot(name)
		for name in toadd:    self.plot.plot(("x", name), color=self.color)

		self.plot.request_redraw()  #Needed so still works after zooming

 
class AbsPlotDEPRECATE(AbstractPlot):

	### Right now this works by presenting user a range of values for ref,
	### but only updates plot when the actual value is a line in the plot
	### can i implement enum as well using this ref and plot_ref double variable?
	low=Int(0)
	ref=Range(low='low', high='t_size', value=5)  #This trips out if low is an integer and high is a string!
	plot_ref=Int(5)

	ref_color=Str('red')


	####	TRYIGN TO USE ENUM EXCEPT SOMETIMES IT GETS RESET TO 0 !!!! ###


	### Get teh closest value in a list of similar value, ripped off from online ###
	def closest(self, target, collection) :	
		print 'target is', target
		print 'collection is', collection
		new= min((abs(target - i), i) for i in collection)[1]
		print 'returing', new
		return new

	@on_trait_change('ref')
	def update_ref(self):
		if self.closest(self.ref, self.t_effective) != self.plotref: self.update_lines()

	@on_trait_change('t_spacing')
	def update_lines(self):

		### CHANGES PLOTS BASED ON LOCAL VARIABLES ###

		self.plotref=self.ref

		print 'updating plotref', self.plotref

		newplots=[self.tlabel[i] for i in self.t_effective]
		refplot=self.tlabel[self.plotref]
		oldplots=[name for name in self.plot.plots]
		toadd=[plot for plot in newplots if plot not in oldplots]
		todelete=[plot for plot in oldplots if plot not in newplots]

		if self.plot.plots != {}: todelete.append(refplot)
		for name in todelete: self.plot.delplot(name)
		for name in toadd:    
	#		data=self.plothandler.specdata[name]/self.plothandler.specdata[refplot]
	#		print data, 'hewre'
			if name != self.tlabel[self.plotref]:
				self.plot.plot(("x", name), name=name, color=self.color)
			else:
				self.plot.plot(("x", name), name=name, color=self.ref_color)

			#JUST CHANGE COLOR, OR ADD A FIND REFERENCE METHOD!!!

		self.plot.request_redraw()  #Needed so still works after zooming

	traits_view=View(
			VGroup(
				Include('abstract_group'),
				HGroup(Item('ref'), Item('ref', style='readonly'),Item('ref_color'))
				),
			resizable=True)


if __name__ == '__main__':
	scene=plot()
	scene.configure_traits()
