from traits.api import HasTraits, Instance, Property, Array, Str, Enum, cached_property, \
			on_trait_change, Dict, Tuple, Int, implements, Any, List, \
			Button 
from traitsui.api import View, Item
from chaco.api import ArrayPlotData
from spec_data import spec_dtype
from ct_interfaces import IRun, IRunStorage, IPlot
from numpy import array, empty, linspace
from run_plots_v2 import AbsPlot, SpecPlot, TimePlot#, AreaPlot
from pandas import DataFrame
from pandasplotdata import PandasPlotData

############
## STILL USES OLD DATASTRUCTURE AND CONVERTS MERE THE MAKE_DFRAME() METHOD
## EVENTUALLY WANT TO BYPASS MY OLD DATASTRUCTURE ALTOGETHER


# Should this include final value (ie n itself?)
def _get_factors(n):
    """ Get factors in a value, ie if 10, returns 1,2,5,10"""
    return [x for x in range(1, n+1) if n % x == 0]

class RunStorage(HasTraits):
	''' This object takes the file_data_info dictionary from the IRun instance, creates Arrays from this and
	    also maintains the ArrayPlotData objects for the full spectral and temporal data. 
	    Event Hierarchy is as follows:
		
		-file_data_info is updated from "update_storage" method form IRun instance
		-tarray, xarray and twoD_data_full arrays are extracted via property calls to file_data_info
		-trait_change listeners are called that create specdata, timedata plot data sources
		-copies of these are stored in the variable specdata, timedata, xarray, tarray
		-changes to filter variables like "x_avg, t_samp" are applied to the specdata/timedata objects
		 while the specdata, timedata are retained intact unless file_data_info changes

	    Label overrides should force overrides in this class and they will filter down to plots
			'''
	implements(IRunStorage)

	file_data_info=Dict(Str, Tuple(Array(dtype=spec_dtype), Array) )

	### Labels are all forced to strings because chaco requries these straight.  The t_label and x_labels are used to both
	### store the full names of the data (eg trial1, trial2) and also used as keys in the array plot data object.  In 
	### addition, chacoplot objects need "xarray" and "tarray" objects that correspond to the t_labels/x_labels.  This is because
	### chaco can't plot a list of strings, so I create intermediate arrays which are the same length as the xarray,tarray values
	### but simple are set as evenly spaced arrays xarray=(1,2,3,... len(x_label))  THEREFORE the shape, size and events that 
	### have to do with labels control all the redraw events and everything.  The label change events must therefore be considered
	### very carefully. The plot objects also rely on these labels exclusviely to do sampling and get correct sizes.  

	test_override=Button

	x_label=Any    
	t_label=Any
	_x_size=Int #Store the full size of the arrays (used for averaging)
	_t_size=Int #Autoset when labels updated

        twoD_data_full = Array #TWO D DATA 
        twoD_data_avg  = Array #TWO D DATA after averaging.  Keep both in case needed to compare both plots later 
	_valid_x_averages=List  #These are automatically set when twoD data is created
	_valid_t_averages=List

	specdata=Instance(ArrayPlotData,())  #Automatically update when twoD_data_full is changed
	timedata=Instance(ArrayPlotData,())

	dframe=Instance(DataFrame)

#	plots=List(IPlot)	
	plots=Instance(IPlot)
	
	### Global sampling traits (Not yet synched up in v3 ###
	x_spacing=Int(1)  #Do I want to do sampling or just averaging or both?  
	t_spacing=Int(1)

	### Global averaging filters filtering traits ###
	t_avg=Enum(values='_valid_t_averages')
	x_avg=Enum(values='_valid_x_averages')
	averaging_style=Enum('Reshaping', 'Rolling')  #Need to add rolling later

	def _test_override_fired(self):
		newx=[str(2*float(entry)) for entry in self.x_label]
		newt=[str(entry) + 'lol' for entry in self.t_label]
		self.override_labels(xlDabel=newx, x_label=newx, t_label=newt)

	def make_dframe(self):
		self.dframe=DataFrame(self.twoD_data_full, list(self.x_label), list(self.t_label))
		trans=self.dframe.T #Need to_string to print long rows
		test=PandasPlotData(self.dframe)
		print test.list_data(as_strings=True), 'here'


		### MAY FIND THAT LOOKUP IS BEST METHOD TO USE FOR SAMPLING OPERATIONS


	def _file_data_info_changed(self): 
		''' This used to be a set of properties, but because twoD data listened to t_label and x_label separately, it would cause a double
		    update which would try to draw incomplete data.  Hence, I have this set up sequentially.  The user can pass new labels via keyword
		    using the override_labels function'''
		self.update_t_label()
		self.update_x_label()
		self.update_full_data()
		self.make_dframe()
		self.update_data_and_plots()

	def update_data_and_plots(self):
		'''Helper method to update full data matrix, and then connected plots.  Used if the underlying
		   matrix changes due to new file, new averaging etc...'''
		self.update_plotdata()  ## FIX LISTENERS
		self.update_plots()


	def _averaging_style_changed(self): 
		''' Merely triggers a double update; however, it will average rows first!!!!'''
		self._x_avg_changed() ; self._t_avg_changed()

	### Separated averaging so that user can control the order of averaging, and so that array wasn't being
	### reshaped in both rows and columns if only one dimension was changing
	def _x_avg_changed(self): 
		if self.averaging_style=='Reshaping':
			print 'reshaping x'
			#Return factors to split by, like 1,2,5 for 10 element set corresponding to 
			#no averaging, 50% average, 20%averaging.  Necessary because reshaping operations require
			#factors.  So if I have 6 rows to start with, can end with 3 rows, averaging 2 at a time or 
			#or 2 rows, averaging 3 at a time.
			self._valid_x_averages=_get_factors(len(self.x_label) )

		elif self.averaging_style=='Rolling':
#			validx=range(1, self.size/2) #Any valid number between 1 and half sample size
			print 'Need to build the rolling average method'
			pass	

		#Row reshape (# rows to remain, row spacing, columns)
		#So if 500 rows and user is averaging by 100, .reshape([5, 100, columns])
		avgarray=self.twoD_data_full.reshape([self._x_size/self.x_avg, self.x_avg, self._t_size]).mean(1)  #First avg by rows
		self.twoD_data_avg=avgarray
		self.update_data_and_plots()

	def _t_avg_changed(self):
		if self.averaging_style=='Reshaping':
			print 'reshaping t'
			self._valid_t_averages=_get_factors(len(self.t_label) )

		elif self.averaging_style=='Rolling':
#			validt=range(1, self.size/2) #Any valid number between 1 and half sample size
			print 'Need to build the rolling average method'
			pass	

		#Col reshape (# rows to remain, row spacing, columns)
		#So if 500 columns and user is averaging by 100, .reshape([100, rows, 5])
		avgarray=self.twoD_data_full.reshape([self.t_avg, self._x_size, \
					            self._t_size/self.t_avg]).mean(2).transpose()  #First avg by rows
		self.twoD_data_avg=avgarray
		self.update_data_and_plots()
	


	def update_plotdata(self):
		''' This will create overwrite primary data sources!  Plots are programmed to redraw
		    when these are overwritten.  This should only occur when a global variable is changed
		    all local variabel changes are built into the plot objects already.'''

		#### ALL LISTENERS ARE HOOKED UP, THIS FUNCTION IS PROBABLY CAUSING THE ISSUE... MAYBE
		#### OVERWRITING THE DATA ARRAYS IS CAUSING THIS

		print 'Updating all ctprimary data sources'
	
		specdata=ArrayPlotData() 
		timedata=ArrayPlotData()

		xarray=linspace(0, len(self.x_label), len(self.x_label) )
		tarray=linspace(0, len(self.t_label), len(self.t_label) )

		specdata.set_data('x', xarray)
		timedata.set_data('x', tarray)        #TIME DATA NOT SET EXCEPT FOR LABE

		for i in range(len(tarray)):
			specdata.set_data(self.t_label[i], self.twoD_data_full[:,i])

		for i in range(len(xarray)):
			timedata.set_data(self.x_label[i], self.twoD_data_full[i,:])  #LABELS ARE STRINGED AS KEYS

		self.specdata=specdata ; self.timedata=timedata 


	### Set defaults 
	def update_plots(self):
		''' Make list eventually and sync iterably '''
		print 'updating plots from specstorage object'

		if self.plots is None:
			print 'making new plots in spec storage object'

	#		plots=AreaPlot(plothandler=self)
		#	plots=AbsPlot(plothandler=self)
			plots=SpecPlot(plothandler=self)
		#	self.sync_trait('t_spacing', plots, 'spacing', mutual=False) #WHY DOESNT IT WORK?
			self.plots=plots


		self.plots.set_major_data(maindata=self.specdata, mainlabel=self.t_label)	
#		self.plots.set_major_data(maindata=self.timedata, mainlabel=self.x_label)


	### Properties that make arrays based on file_data_info dictionary ###
	def update_t_label(self): 
		'''Stores the files in a sorted (by name) fashion, used for parsing the data in a sorted manner and also for axis labels'''
		sortlist=self.file_data_info.keys()
		sortlist.sort()
		self.t_label=sortlist
		self._t_size=len(self.t_label)

	def update_x_label(self):
		firstfile=self.t_label[0]
		self.x_label=self.get_wavelengths(firstfile)  
		self._x_size=len(self.x_label)


	def override_labels(self, **kwargs):
		''' Used to let the user pass new labels either individually or all at once to the plot.  Arrays must be the same length as the plot axis (may want
		   to change later).  Arrays will be autoconverted to strings incase users pass an array of floats for example.  This is built that that new
		   traits can easily be passed in the "valid" variable and everything will still work. This also has a feature that allows users to pass
		   wrong keywords and it will let them know which ones it cannot update and will not try to update them.  This is a nice feature over standard
		   error that occurs when **kwargs is called with an invald keyword'''

		valid={'x_label':self.x_label, 't_label':self.t_label}
		invalid=[]

		##Test for wrong keywords##
		for key in kwargs:
			if key not in valid.keys():
				print '\n\n You entered key\t', key, '\tbut key must be one of the following:\t', \
			               '\t'.join(key for key in valid.keys() ), '\n\n'
				invalid.append(key)

		for key in invalid:kwargs.pop(key)  # Catches errors when users input wrong keywords

		##Make sure new label is same length as old label
		for key in kwargs:
			if len(kwargs[key]) != len(valid[key]):  
				print '\n\n You tried to update\t', key, '\tof length\t', len(kwargs[key]), \
				       '\tbut the current value has length\t', len(valid[key]) 
			else:
				## Update correct trait, but also makes sure each entry is a string!##
				valid[key]=[str(entry) for entry in kwargs[key]]  
				### REQUIRES SETTING TRAITS!!!
				### THIS MAY REQUIRE USING TRAIT.SET_ATTR

		print 'updated labels for the following entries:\t', '\t'.join(key for key in kwargs.keys()), '\n\n'

		self.update_plotdata()



	def update_full_data(self):
		'''Stores 2-d data for easy input into a multiplot'''		
	    	fullarray=empty( (len(self.x_label), len(self.t_label)), dtype=float)
		index=0
		for afile in self.t_label:  #Iterating over this because this is pre-sorted
			fullarray[:,index]=self.get_intensities(afile)
			index=index+1
		self.twoD_data_full=fullarray
		if self.averaging_style=='Reshaping':
			#Return factors to split by, like 1,2,5 for 10 element set corresponding to 
			#no averaging, 50% average, 20%averaging.  Necessary because reshaping operations require
			#factors.  So if I have 6 rows to start with, can end with 3 rows, averaging 2 at a time or 
			#or 2 rows, averaging 3 at a time.
			self._valid_x_averages=_get_factors(len(self.x_label) ) 
			self._valid_t_averages=_get_factors(len(self.t_label) ) 


		elif self.averaging_style=='Rolling':
#			validt=range(1, self.size/2) #Any valid number between 1 and half sample size
			print 'Need to build the rolling average method'
			pass	

		#Row reshape (# rows to remain, row spacing, columns)
		#So if 500 rows and user is averaging by 100, .reshape([5, 100, columns])
		avgarray=self.twoD_data_full.reshape([self._x_size/self.x_avg, self.x_avg, self._t_size]).mean(1)  #First avg by rows
	#	avgarray=avgarray.reshape().mean(2).transpose() #Then avg by columns (transpose is necessary, see bintest.py)
		print avgarray.shape
		self.twoD_data_avg=avgarray
	### Simple Return modules to reduce syntax
	def get_wavelengths(self, afile): return self.file_data_info[afile][0]['wavelength']	
	def get_intensities(self, afile): return self.file_data_info[afile][0]['intensity']

	### Helper Methods

	traits_view=View(	
			Item('t_spacing', label='Global t sampling'),
			Item('plots', style='custom', show_label=False),	
			Item('test_override'),Item('averaging_style'), Item('x_avg'), Item('t_avg'),
			resizable=True)



if __name__ == '__main__':
	scene=RunStorage()
	scene.configure_traits()
