import numpy as np

from chaco.api import AbstractPlotData
from traits.api import Dict, Instance
from pandas import DataFrame

class PandasPlotData(AbstractPlotData):
    
    # The dataframe
    df = Instance(DataFrame)

    # Dict mapping data series name to a mask array holding the arrays
    arrays = Dict()

    # Consumers can write data to this object (overrides AbstractPlotData).
    writable = True

    def __init__(self, dataframe):
        """PandasPlotData exposes a PlotData interface from a DataFrame.
	   It is chosen that this object MUST be initialized with a dataframe.
           The intializer in ArrayPlotData will assign the names "seriesN" to
	   any unlabeled arrays passed into the program through the *data argument.
	   Because dataframes are inherently labeled, this behavior is unnecessary 
	   for basic use.
		
	   All data is stored as rows; however, column data is accessible through list_column_data()
           since chaco plots may want it for axis labels"""

	for name in dataframe.index: 
		self.arrays[name]=np.asarray(dataframe.xs(name))
        self.df = dataframe

    def list_data(self, force_strings=False):
	''' Return row keys in dataframe.  Option to return as strings is a convienence function. '''
	if force_strings:
		return [str(i) for i in self.df.index] 
	else:
		return list(self.df.index)

    def list_column_data(self, force_strings=False):
	''' Return column keys in dataframe object '''
	if force_strings:
		return [str(i) for i in self.df.columns]
	else:
	        list(self.df.columns)

    def get_data(self, name):
	return np.asarray(self.df.xs(name))  #Changed to .get()


    def set_data(self, name, new_data):
        """ Sets the specified array as the value for either the specified
        name or a generated name.

        Implements AbstractPlotData.  
	THIS WILL ONLY SET ROW DATA IN A PANDA DATAFRAME OBJECT UNDER CURRENT SELECTION

        Parameters
        ----------
        name : string
            The name of the array whose value is to be set.
        new_data : array
            The array to set as the value of *name*.
        generate_name : Boolean
            I've eliminated this functionality for this datatype 

        Returns
        -------
        The name under which the array was set.
        """
        if not self.writable:
            return None

        event = {}
        if name in self.arrays:
            event['changed'] = [name]
        else:
            event['added'] = [name]

        if isinstance(new_data, list) or isinstance(new_data, tuple):
            new_data = np.array(new_data) #Convert to array data

        self.arrays[name] = new_data
        self.data_changed = event

        return name

    def del_data(self, name):
        """ Deletes the array specified by *name*, or raises a KeyError if
        the named array does not exist.
        """
        if name in self.arrays:
            del self.arrays[name]
        else:
            raise KeyError("Data series '%s' does not exist." % name)

######## These are used by chaco to inform the plot that a certain region of data is selected

    def get_selection(self, name):
        """ Returns the selection for the given column name """
        return self.selections.get(name, None)

    def set_selection(self, name, selection):
        # Store the selection in a separate dict mapping name to its
        # selection array
        self.selections[name] = selection
        self.data_changed = True


