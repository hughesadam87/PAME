from traits.api import Interface, Array, Str, CArray, Instance
from chaco.api import ArrayPlotData

class IView(Interface):
    """ Basic plot elements that store data and update in a custom way to ensure repeated methods in plot design.  This 
    interface is really just serving as a reminder of how I design basic plots for future reference.  """

    data = Instance(ArrayPlotData)

    def create_plots(self):
        """ Makes plots from data, standard"""

    def add_tools_title(self):
        """ Adds tools and title to plots """

    def update(self):   
        """ Method to be called by simulations which will create plots or update the data in plots """

    def update_data(self):
        """ Custom method which basically uses set_data() to set all the trait values at once """

    ### Probably a smart way to change all of these update methods to a simplier dictionary notation ###

    def get_sexy_data(self):
        '''Returns the data in a list that is specfic to a plot and is really just used as an interface for simulations and output plots'''

    def set_sexy_data(self, data_list):
        ''' Same as above, used to restore trait values and things '''

class ICompositeView(Interface):
    '''Used mainly when simple plots are ported into more composite objects for better comparisons '''


class IMixer(Interface):
    """ Interface to distinguish mixer objects """

    def update_mix(self):
        """ Does the actual mixing and updates mixedarray """

class IMie(Interface):
    '''Interface to distinguish mixer objects'''
    lambdas=Array
    emedium=CArray    #Outter medium dielectric
    ecore=CArray      #Core particle dielectric

    def update_cross(self):
        '''A function to compute the scattering cross section of particles'''

class ILayer(Interface):
    """Interface to distinguish mixer objects """
    name=Str
    designator=Str

class ISim(Interface):
    """ Interface to distinguish mixer objects """
    
    def update_storage(self):
        '''A function to update internal objects.  For now, only one type of
           sim is used and i'm just making the interface for completeness'''

class IMaterial(Interface):
    lambdas=Array
    earray=CArray
    mat_name=Str
#	def update_data(self, na):
#		'''Method generally called to make the material traits all dynamically intertwined'''

class IStorage(Interface):
    """ Interface to distinguish material storage facilities """

        #RIGHT NOW THIS HAS NO REAL USE JUST SO THAT USERS CAN SEE WHEN THESE TYPES OF TRAITS ARE REQUIRED

        #Should make current_selection and Return a required trait because supermodel doesn't distinguish these on any other facility

class IAdapter(Interface):
    """Adapter used to show materials to user without instantiating the objects"""
    name=Str
    source=Str
    notes=Str
    matobject=Instance(IMaterial)

    def populate_object(self):
        """Method used to populate a given material"""