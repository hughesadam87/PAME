""" Storage object for simulation data.  Intended to be used while fibersimulation application is running
for piping data to special chacoplots, OR, for standalone use.  
save() and load() methods will serialize properly for use outside of the simulation program.

Can call the initialization with a pickled filename for faster use (eg):
   s=LayerSimParser('sim.pickle')
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
from pame import globalparms
import customjson
import custompp #<--- Custom pretty-print
import logging
import config

class SimParserError(Exception):
    """ """

class LayerSimParser(HasTraits):
    """ Used to mediate storage and IO of the intermediate datastructures of simulations (dictionaries and such)
    into nice output (CSV) and pandas objects.  Just too bulky to stuff into gensim program.  Downstread analysis
    programs will use this to get info about the simulation parameters in compliment to the panel object
    saved in conjunction.

    Decideded to leave complete control over outfilenames/saving to objects that call this, and so have no
    file-related traits.  Also has load method and stuff for interfacing to scikit-spectra.  
    
    ** Will look in self.static for wavelenghts!
    """


    # Public traits available to user, formatter to various forms of output
    about = Dict()
    static = Dict()
    primary = Dict()
    results = Dict()
    inputs = Dict()

    primarypanel = Instance(Panel)
    backend = Str('pandas')#Enum(['skspec', 'pandas'])

    def _backend_default(self):
        return config.SIMPARSERBACKEND
    
    @classmethod
    def load_json(cls, path_or_fileobj, **traitkwds):
        """ Initialize from json file, output of simulation.save_json. """
        stream = customjson.load(path_or_fileobj)
        
        return cls (about = stream['about'],      #<-- use **stream?
                    static = stream['static'],
                    primary = stream['primary'],
                    results = stream['results'],
                    inputs = stream['inputs'], 
                    **traitkwds
                    )

    
    @classmethod
    def load_pickle(cls, path_or_fileobj, **traitkwds):
        """ Initialize from a pre-serialized instance of  """
        # Creates instance, calls .load(), returns
        newobj = cls(**traitkwds)
        newobj.load(path_or_fileobj) 
        return newobj
        
            
    def summary(self, style='short'):
        """ Summarizes all dictionaries in nice, formatted output.  Arrays/
        Lists are formatted for clarity."""
        if style not in ['short', 'full']:
            raise AttributeError('Style must be "short" or "full", got %s' % style)
        
        def _smart_format(array_or_numeric):
            """ If iterable, returns min and max values as a range string,
            otherwise just returns value.  Useful for string formatting 
            objects of mixed arrays and floats"""
            if isinstance(array_or_numeric, basestring):
                return array_or_numeric
            try:
                return '(%s - %s)' % (array_or_numeric[0], array_or_numeric[-1])
            except Exception:
                return str(array_or_numeric)
        
        # Dictionaries loopings should be refactored into a function, but it
        # would probably have to be recursive since sometimes have dict
        # of dict, sometimes dict of scalars, some times mixed scalars/dict
        
#        if style == 'short':  
        panel_printout = 'Primary:'
        panel_printout += '\n\t%s' % self.primary_panel().__repr__().replace('\n', '\n\t')
        #panel_printout += '\n\t  ".primary_panel()" to access full panel'
        
        input_printout = 'Inputs:'
        for k,v in self.inputs.items():
            input_printout += '\n\t%s : %s' % (k, _smart_format(v) )
            
        about_printout = 'About:'
        for k,v in self.about.items():
            # TOTAL HACK FOR SINGLE ATTRIBUTE: Storage, which is dict
            if isinstance(v, dict): #or ORderedDIct
                about_printout += '\n\t%s:\n' % (k)        
                for subk, subv in v.items():
                    about_printout += '\t\t%s : %s\n' % (subk, _smart_format(subv) )                            
            else:
                about_printout += '\n\t%s : %s' % (k, _smart_format(v) )        
            
        static_printout = 'Static Parameters:'
        # Static is a dict of dicts
        for mainkey in self.static.keys():
            static_printout += '\n\t%s:' % mainkey
            for k,v in self.static[mainkey].items():
                static_printout += '\n\t\t%s : %s' % (k, _smart_format(v) )
                                         

        return '\n\n'.join([input_printout,
                            panel_printout, 
                            about_printout,
                            static_printout])
            
    def primary_panel(self, minor_axis=None, prefix=None):
        """ Returns primary as a Panel if possible, if fails, raises warning
        and returns as dict.
        """        
        primary_of_df = {} #Create a primary of dataframes, so has to convert all values to DF's
        ignoring = [] # If can't convert a value to df, let user know

        try:
            wavelengths = self.static[globalparms.spectralparameters]['lambdas']
        except Exception:
            logging.warning('Could not find lambdas in self.static, primary panel will'
                            ' not be indexed by wavelength...')
            wavelengths = None

        # Try to convert to dataframes.   If fails on one step, should fail on all the steps
        for step, data in self.primary.items():
            primary_of_df[step] = DataFrame(data, index=wavelengths)
        
        # Panel with as simulation variabless as major axis (ie A_avg, R_0)
        outpanel = Panel.from_dict(primary_of_df, orient='minor')
        
        # Sort Items alphabetically (R_avg, R_0, R_1, T_avg, ...)
        outpanel = outpanel.reindex_axis(sorted(outpanel.items),
                                     axis=0, #items axis
                                     copy=False) #Save memory

#        XXXXX HERE
#        if self.backend == 'skspec':
#            raise NotImplementedError('scikit spec nto builtin')

        # REORIENTATION OF MINOR AXIS LABELS
        if minor_axis:
            if isinstance(minor_axis, basestring):
                inputarray = self.inputs[minor_axis] # values like 50, 60, 70, so want prefix/?
                newaxis = dict(zip(outpanel.minor_axis, inputarray)) 
                # end of day, want basically {'step_1':'vfrac_0.5, 'step_2', 'vfrac_0.10' ...
                if prefix:
                    # No delimiter (ie %s_%s) because prefix can set that eg prefix = layerd_ or layerd=
                    newaxis = dict((k,'%s%.4f' % (prefix, v)) for k, v in newaxis.items())
            elif isinstance(minor_axis, int):
                pass
            else:
                raise SimParserError('Can only map strings or integers to primary_panel, get type %s.'
                   ' These should correspond to the keys in %s' % (type(minor_axis, self.inputs)))

            outpanel = outpanel.rename(minor_axis = newaxis)

        return outpanel
            
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

    def load(self, path_or_fileobj):
        """ Load and set self.about, static, primary, results """
        if isinstance(path_or_fileobj, basestring):
            path_or_fileobj = open(path_or_fileobj, 'r')        
        sp = cPickle.load(path_or_fileobj)
        self.copy_traits(sp, traits=['about',
                                     'static',
                                     'primary',
                                     'results',
                                     'inputs'
                                     ], copy='deep')
