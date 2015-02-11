from traits.api import Interface, Array, Str, CArray, Instance, HasTraits
from chaco.api import ArrayPlotData

class IView(Interface):
    """ Basic plot elements that store data and update in a custom way to ensure repeated methods in plot design.  This 
    interface is really just serving as a reminder of how I design basic plots for future reference.  """

    data = Instance(ArrayPlotData)
    model = Instance(HasTraits) #<-- Material object, must be initialized with    

    def create_plots(self):
        """ Makes plot(s) from data, standard"""

    def add_tools_title(self):
        """ Adds tools and title to plots """
        
    def update_data(self):
        """ """

class ICompositeView(IView):
    '''Used mainly when simple plots are ported into more composite objects for better comparisons '''
    # TECHNICALLY THIS SHOULDN"T BE AN INSTANCE OF IVEW BUT HAD TO DO IT TO 
    # GET MAIN PLOTTING OF ALL MATERIALS TO WORK


class IOptic(Interface):
    """ Used for Optical stack modeling.  This is is what would distinguish reflectance from Fiber with averaging
    from just a glass slide that has no Angle dependence.
    """

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