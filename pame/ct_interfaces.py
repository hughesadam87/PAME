from traits.api import Interface, Dict, Str, Tuple, Array, Instance
from spec_data import spec_dtype

class IRun(Interface):
	""" Stores ordered series data from different types of input and formats them into the same object, file_data info. 
	    file_data_info is a dictionary that stores file information and array data.  The IRun is responsible for getting
 	    the data into this format and then all plotting features should be applicable."""

	file_data_info=Dict(Str, Tuple(Array(dtype=spec_dtype), Array) )
	def update_file_data_info(self): 
		'''A method to take in data from a file and format it into the file_data_info format.'''

	def update_storage(self): 
		'''Once file_data_info is updated, this passes the new object into an IRunStorage object
		   which then breaks down the data into arrays and other data types that are useful for plotting '''

class IRunStorage(Interface):
	'''  Whereas the IRun interface is merely responsible for making a file_data_info dictionary and passing it along
	     to this class, this class does most of the manipulation.  It turns the file_data_info dictionary to a
	     series of arrays and ArrayPlotdata Objects.  It also stores all the plot objects and snycs traits and 
	     storage objects between them.  This also controls the specdata instance, so when I build plots, no
	     event listeners are needed since the plot data already delegates!!! '''

class IPlot(Interface):
	''' Plotting interface for my program.  Basically, the plotdata is all handled by the IRunStorage object.  Therefore, 
	    IPlot delegates its plotdata out to these instances and trait changes are automatically registered through the 	
	    set_data events in the IRunStorage object '''

	plothandler=Instance(IRunStorage)  #Must be initialized with this

	def update_lines(self):
		''' Function that will change sampling and other aspects of lines already drawn on plot'''
