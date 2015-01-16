""" Storage object for simulation data.  Intended to be used while fibersimulation application is running
for piping data to special chacoplots, OR, for standalone use.  
save() and load() methods will serialize properly for use outside of the simulation program.

Can call the initialization with a pickled filename for faster use (eg):
   s=SimParser('sim.pickle')
   print s.results
     ...  

Stores simulation results in a pandas Panel object, with each increment
being an item, and the state of the system at that point as a dataframe. 

The simulated parameter values are stored separately in a dataframe called sim_parms.  

Other important parameters in the program are stored in parms dictionary.

Special methods like list_parms() and parms_to_csv() provide nice formats for readability."""

# Python imports
import cPickle, types, collections, sys, os #For type checking, collections only used in one method

#3rd party imports
from traits.api import *
from traitsui.api import message
from pandas import DataFrame, Panel

#Local imports
from handlers import FileOverwriteDialog
import globalparms
import customjson
import custompp #<--- Custom pretty-print

class SimParser(HasTraits):
    """ Used to mediate storage and IO of the intermediate datastructures of simulations (dictionaries and such)
    into nice output (CSV) and pandas objects.  Just too bulky to stuff into gensim program.  Downstread analysis
    programs will use this to get info about the simulation parameters in compliment to the panel object
    saved in conjunction.

    Decideded to leave complete control over outfilenames/saving to objects that call this, and so have no
    file-related traits.  Also has load method and stuff for interfacing to scikit-spectra.  """

    # Entire simulation results, panel of increments, storing many arrays
    _about = Dict()   #<--- Private because change output of real representation
    _static = Dict()
    _summary = Dict()
    _results = Dict()
    
    # Public traits available to user, formatter to various forms of output
    about = Property()
    static = Property()
    summary = Property()
    results = Property()

    summarypanel = Instance(Panel)
    
    @classmethod
    def load_json(cls, path_or_fileobj):
        """ Initialize from json file, output of simulation.save_json. """
        stream = customjson.load(path_or_fileobj)
        
        return cls(_about = stream[globalparms.about],
                    _static = stream[globalparms.static],
                    _summary = stream[globalparms.summary],
                    _results = stream[globalparms.results]
                    )
        
    # Properties
    # ----------
    def _get_results(self):
        return self._results

    # This can be used to promote metadata to main namespace if desirable.  Strictly for convienence.
    def promote_parms(self, verbose=True):
        """ Takes all keys in passive parms dictionary and makes the class attributes (that are not 
        instance methods) for easier access.  Will make sure no name conflicts are occurring.  
        If this ever becomes especially useful,then consider adding option to update from simulation 
        or non-simulation parameters only."""

        # List all attributes that are not instance methods 
        allatts=[att for att in dir(self) if type(getattr(self, att)) != types.MethodType]

        for attr in self.parms:
            if attr not in allatts:
                setattr(self, attr, self.parms[attr])
                if verbose==True:
                    print 'Promoting attribute, %s, to toplevel namespace'%attr
            else:
                print 'Name conflict, %s attribute already exists in main namespace.'%attr

    def demote_parms(self, verbose=True):
        """ Opposite of promote_parms, use to cleanup namespace."""
        for attr in self.parms:
            try:
                getattr(self, attr)
            except AttributeError:
                pass
            else:
                delattr(self, attr)
                if verbose==True:
                    print 'Removing attribute, %s, from toplevel namespace'%attr                

    def write_parms(self, full=True, outfile=None):
        """ Print simulation parameters to screen.  If full=True, prints values as well.  
        full:
           If false, program will only print names of parameters, not values (e.g. lite version)
        outfile:
           If true, lazy use of stdout to redirect output (instead of using loggin module which is better for this)."""
        if outfile:
            if os.path.exists(outfile):
                test=FileOverwriteDialog(filename=outfile)
                ui=test.edit_traits(kind='modal')
                # break out and don't save#
                if ui.result==False:
                    print '\n\t Aborting write_parms()'
                    return            


            o=open(outfile, 'w')
            sys.stdout=o

        if full==True:
            print '**Results panel** (self.results)\n\n', self.results
            print '\n**Parameters Dataframe** (self.sim_parms)\n\n', self.sim_parms

        print '\nVariable parameters:\n'

        for key in sorted(self.simparms):
            if key in self.translator:
                key=key+' ('+self.translator[key] +')'  #These are awlays strings so get away with +
            print '\t',key


        print '\nStatic parameters:'  #dict of dicts like {A: {B:(c,d), E:(f,g) }} (strict type check)
        for major in sorted(self.parms):
            print '\n\t',major+':'
            for minor in self.parms[major]:
                if full==True:
                    value=self.parms[major][minor]

                # Output iterables separate from rest (str is iterable so be carefule) 
                    if isinstance(value, collections.Iterable) and not isinstance(value, basestring):
                        value=' , '.join(str(i) for i in value)

                    out=':  '.join([minor,str(value)])                      
                else:
                    out=minor
                print '\t\t',out

        if outfile:
            sys.stdout=sys.__stdout__
            o.close()
            message('Parameters copied to file %s'%outfile, title='Success')




    # Quick interface to save/load this entire object.  This entire object can itself pickle normally,
    # so downstream processing can open it up and then output data as necessary.
    def save(self, outfilename):
        """ Saves active and passive parms.  Does not attempt to save dataframe, since it is constructed 
        upon the property call anyway. """
        with open(outfilename, 'wb') as o:
            cPickle.dump(self, o)

    def load(self, infilename):
        with open(infilename, 'r') as f:
            sp=cPickle.load(f)
            self.copy_traits(sp, traits=['results', 'parms', 'simparms', 'translator'], copy='deep')
