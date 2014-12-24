''' All of these classes are used for visualizing and plotting simulations.  The actual
simulation data is made in the gensim.py file, where each simulation is stored as a dictionary
of arrays.  That later is passed to this file as the trials_dic trait.  These are later used to
set chaco plot interfaces (OpticalView, MaterialView etc...).  At this point, its best to just
output the data to dataframes and rely on pyuvvis to do the visualization and analysis.  This
can be resurrected when in-house visualization and realtime chaco plotting is important.'''

from traits.api import Dict, Property, Any, Instance, HasTraits, List, cached_property, Int, Enum, Str
from traitsui.api import Item, View, VGroup, ListStrEditor, HGroup
from basicplots import OpticalView, MaterialView
from interfaces import IView
import sys
from operator import itemgetter

### THESE ARE THE SAME EXACT THING, JUST MAKE THEM ONE GENERAL OBJECT ###

class GeneralSimStorage(HasTraits):
	''' General holder object to contain sorted dictionaries.  Inhereting classes will utilize these to generate ViewList objects and
	    CurveAnalysis interfaces.'''

	### Basic storage of runs keyed by trialname storing array data of the format "get_sexy_data()" from Mview and OpticalView plots
	trials_dic=Dict #Dictionary of array data specifically suited for simview
	trials_delimiter=Str #This is passed in through gensim to make sure dictionary is split correctly
	trials_keys=Property(List, depends_on='trials_dic, trials_delimiter')  #Requires special format of Str Str(int)
	selected_variable=Any  #Basically key from trials_keys

	@cached_property
	def _get_trials_keys(self): 
		''' Stores trials keys in sorted fashion by number.  Because sort(str) will not properly store numerical order for A1 vs A11 vs A2 for example,
		    this uses itemgetter to split the list, sort it by the integer value, then reassemble.'''
		vals=[(key.split(self.trials_delimiter)[0], int( key.split(self.trials_delimiter)[1] ) ) for key in self.trials_dic.keys()]
		vals_sorted=sorted(vals, key=itemgetter(1))
		return [j[0]+(self.trials_delimiter)+str(j[1]) for j in vals_sorted]

class GeneralViewList(GeneralSimStorage):
	''' General object to store simulations by interfacing a dictionary to a plot.
	    The user stores data in the dictionary and upon selection it is piped to a plot.
	    3/29 added support to format a curve_analysis_dic (basically just data structure to fit curve analysis program
	    so that piping can be done in real time instead of saving into intermediate files (handled in gensim.py) '''

	### Traits to build a selectable table which pipes data into a plot in real time as user changes selection.  (Maybe phase out later...)
	plot_storage=Instance(IView,())#Instance Simview

	def _selected_variable_changed(self): self.plot_storage.set_sexy_data(self.trials_dic[self.selected_variable])

	traits_view=View(
			VGroup(
			Item('trials_keys', show_label=False, editor=ListStrEditor(selected='selected_variable')), 
			Item('plot_storage', show_label=False, style='custom'),
				),
			)
  	 		

class MaterialViewList(GeneralViewList):
	plot_storage=Instance(MaterialView,())  #Instance Material View, used for E,N simulations

class OpticalViewList(GeneralViewList):
	plot_storage=Instance(OpticalView,())   #Instance Sim View, used for storing reflectance simulations

class CurveAnalysisStorage(GeneralSimStorage):
	''' Old version to store dictionaries of arrays in curve analysis programs.  Going to update to store Series
	and work with pyuvvis.
	'''

	### Curve analysis required imports ###
	names=['glue','reeves','hugadams']
	for name in names:
		sys.path.append("/home/"+name+"/Dropbox/Curve_Analysis_Traits/Old_versions/Curve_analysis_traits_v3")
	from rundata import RunData
	from spec_data import spec_dtype
	from numpy import array

	#### Traits used to interface simulation results directly into the Curve Analysis programs ###
	curve_analysis_dic=Property(Dict, depends_on='trials_dic, data_column')  #Primary storage to interface to Curve Analysis Program	
	data_column=Int #Depending on the plot in question (reflectance vs. material) the column that is piped out is set in inheriting modules
	curve_storage=Instance(RunData)

	@cached_property
	def _get_curve_analysis_dic(self):	
		''' Format a file_data_info dictionary directly to be passed into a RunData object, which then builds curve analysis plots '''
		if self.trials_keys != []:
			xvalues=self.trials_dic[self.trials_keys[0]][0]  #Arbitrarily chosen
			return {trial : [(self.array(zip(xvalues, self.trials_dic[trial][self.data_column]),
					 dtype=self.spec_dtype)),()] for trial in self.trials_keys}
		
	def _curve_analysis_dic_changed(self):
		''' Sync dictionaries between simulation and curve analysis rundata which then will update itself accordingly '''
		if self.curve_storage is None:	self.curve_storage=self.RunData(file_data_info=self.curve_analysis_dic, source='Simulation')
		else: self.curve_storage.file_data_info=self.curve_analysis_dic

	traits_view=View(
			VGroup(
				Item('data_column'),
				Item('curve_storage', style='simple'), 
				),
			)	


class ReflectanceStorage(CurveAnalysisStorage):
	data_column=Enum(4, [1,2,3,4]) #0= xarray,  1=angles, 2=RefArray, 3=TransArray, 4=Reflectance_AVG] (1,2,3 are not average so they probably wont work anyway)
	
	### If I ever decide to make a MaterialStorage class, keep in mind that data columns 2,3 refer to complex narray and earray, so I'd need to be sure
	### to pipe the complex array into my program.  This brings up a complex truncation error if I try as currently written (3/29/12)

class ScattStorage(CurveAnalysisStorage):
	data_column=Enum(3, [1,2,3]) #0=x, 1=scattering, 2=absorption, 3=extinction

class MaterialStorage(CurveAnalysisStorage):
	data_column=Enum(3, [1,2,3,4])  # 0=self.xarray, 1=self.ereal, 2=self.nreal, 3=self.eimag, 4=self.nimag


