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
import cPickle, re 
#3rd party imports
from traits.api import *
from traitsui.api import message
from pandas import DataFrame, Panel
import pame.utils as putil
import numpy as np
import functools, types

#Local imports
from handlers import FileOverwriteDialog
from pame import globalparms
import customjson
import custompp #<--- Custom pretty-print
import logging
import config

ORIGINAL_getitem = Panel.__getitem__

def skspec_getitem(*args, **kwargs):
    """ Overload __getitem__ of panel so can return Spectra.  Can't
    set panel items to Spectra; it's forbidden."""
#    print args, kwargs
#    kwargs.pop('s', None)
    specunit = kwargs.pop('specunit', 'nm')
    name = kwargs.pop('name', '')
    panel, slice_attr = args[0], args[1] #<-- R_avg, A_avg etc...
    dfout = super(Panel, panel).__getitem__(slice_attr)#*args, **kwargs)
    from skspec import Spectra, Unit
    
    # First item in columns (e.g. steps_1, unit becomes step)
    # http://stackoverflow.com/questions/4998629/python-split-string-with-multiple-delimiters    
    try:
        varname = dfout.columns[0].strip()
        unit = re.split('[_ =]', varname)[0]
        # One big hack and should be set from "alias" parameter in primary_panel
    except Exception:
        varunit = None
    else:
        varunit = Unit(short=unit, full=unit)
    dfout.columns = np.arange(dfout.shape[1]).astype(float) # Floats 0,1,2 to replace step_1, step_2
        
        
    specout = Spectra(dfout, 
                specunit=specunit,
                name=name,
                varunit=varunit,# Since monkey-patching, so screwed
                iunit=slice_attr)            
    return specout

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
    results = Instance(putil.AttrDict) #<-- Actually a special dictionary with attribute access
    inputs = Dict()
    
    primarypanel = Instance(Panel)
    backend = Enum(['skspec', 'pandas'])

    def __init__(self, *args, **kwargs):
        #Initialize traits
        results = kwargs.pop('results', {})
        super(LayerSimParser, self).__init__(*args, **kwargs)
        # Change results to putil.AttrDict
        self.results = putil.AttrDict(results)

    def _backend_default(self):
        return config.SIMPARSERBACKEND


    def _backend_changed(self):
        """ Change between pandas and skspec slicing."""
        if self.backend == 'skspec':
            if not config.SKSPEC_INSTALLED:
                raise SimParserError('Scikit-spectra is not installed; cannot'
                                     ' support backend.')
            #http://stackoverflow.com/questions/28355896/monkeypatch-with-instance-method
            def _partial_getitem(*args, **kwargs):
                """ Acts like a partial function to skspec_getitem with custom
                keywords.   Called like Panel['A_avg'] and Panel passed in, and 
                'A_avg' becomes attr/varunit.
                """
                from skspec.units.specunits import _specunits
                SPECDICT = dict((obj.full, obj.short) for obj in _specunits)

                panel, attr = args
                x_short = self.static[globalparms.spectralparameters]['x_unit'].lower()

                out = skspec_getitem(panel, 
                                     attr, 
                                     name = self.about['Simulation Name'],
                                     specunit = SPECDICT[x_short]
                                     )
                return out
            
            Panel.__getitem__ = _partial_getitem#types.MethodType(skspec_getitem, Panel, self)            
        else:
            Panel.__getitem__ = ORIGINAL_getitem
    
    
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
                return '%s(%s - %s)' % (type(array_or_numeric), 
                                        array_or_numeric[0], 
                                        array_or_numeric[-1])
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
                            static_printout,
                            'plotting backend: %s' % self.backend
                            ])
            
    def promote(self, attr, alias=None):
        """ Takes results attribute of form 'a.b.c' corresponding to 
        'step.results.a.b.c and promotes it for each step into 
        primary.  Alias is name of attr put into primary.
        """
        out = []
        if not alias:
            alias = attr 
        if alias in self.primary:
            raise SimParserError('"%s" already exists in primary, please choose different alias.' % alias)
        for step in self.results:
            try:
                longattr = '%s.%s' % (step, attr)
                value = getattr(self.results, longattr)
            except AttributeError:
                raise SimParserError('Could not find attribute %s on step %s')
            
            # Just adds it to primary at each step
            self.primary[step].update({alias:value})
            
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
        outpanel = outpanel.reindex_axis(sorted(outpanel.items))  #<-- Sorted items alphabetically
        
        # Sort Minor axis with integer suffix (step_0, step_1, step_2)
        # http://stackoverflow.com/questions/4287209/sort-list-of-strings-by-integer-suffix-in-python
        outpanel = outpanel.reindex_axis(putil.stepsort(outpanel.minor_axis),
                                        axis=2, #items axis
                                        copy=False) #Save memory        

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
