import os, sys, re
from traits.api import HasTraits, Enum, Dict, File, Directory, Array, Str, Property, cached_property, implements, \
     Int, Bool, Float, List, Tuple, cached_property, Instance
from traitsui.api import View, Item, ArrayEditor, HGroup, VGroup
from ct_interfaces import IRun
import numpy as np
import glob
from spec_data import load_spec, load_info, load_formatted_info, load_formatted_data, spec_dtype
from pyface.api import warning
from spec_storage_v2 import RunStorage

class RunData(HasTraits):
    ''' General class for storing data in a specific fashion.  Inheriting classes will change import/outport schemes but
        retain the same basic data structures.  As long as data can be written into the correct file_data_info format, all 
        other methods drawing from it should work without alteration. '''	

    implements(IRun)
    source=Str('None')  #Class indicator really
    run_name=Str('Unnamed Run') #Name the run

    ### I CAN MAKE ALL OF THESE UPDATE WITH THE UPDATE_FILE_DATA_INFO METHOD OR MAKE THEM PROPERTIES.... SHOULD HAVE SAME DIFFERENCE ###

    file_data_info=Dict(Str, Tuple(Array(dtype=spec_dtype), Array) ) #Filename: (xy-Data), (Header)

    storage=Instance(RunStorage)

    spec_consistency = Enum(True, False, 'Unknown')

#	export=Button
#	def _export_fired(self): np.savetxt('test.txt', self.spectral_array, delimiter='\t', newline='\n' header='')

    def _spec_consistency_default(self): return 'Unknown' #How do this on declaration?

    def update_file_data_info(self): pass  #Method to set main data source in program

    def update_storage(self): 
        '''When file_data_info updated, new value passed to storage object which
           results in downstream creation of arrays, resetting of parameter etc... '''
        self.storage.file_data_info=self.file_data_info

    def spec_consistency_test(self):  
        first_wavelengths=self.get_wavelengths(self.sorted_file_array[0])
        for afile in self.sorted_file_array:
            if self.get_wavelengths(afile) != first_wavelengths:
                self.spec_consistency=False
                return
        self.spec_consistency=True
        return

    ### DEFINE EVENT LISTENERS ###
    def _file_data_info_changed(self): 
        if self.storage is None:
            self.storage=RunStorage(file_data_info=self.file_data_info)
        else:
            self.storage.file_data_info=self.file_data_info

    ### INCLUDE EXPORT OPERATIONS HERE ###

    ### OPTIONAL (Import a set of warnings and consistency checks for things like uneven spaced data, non-constant x-array etc...)	

class DeprecatedRunData(RunData):
    ''' Imports old-school data from my previous mods and forces data into a format that's conducive to the IRun interface'''

    ### IRun traits ###

    formatted_datafile=File  
    formatted_timefile=File
    source=Str('Deprecated File Format')
    file_consistency=Enum(True, False, 'Unknown')  #Used to make sure user enteres correct data and time files

    def _file_consistency_default(self): return 'Unknown'

    def _formatted_timefile_changed(self): self.update_file_data_info()
    def _formatted_datafile_changed(self): self.update_file_data_info()

    def file_consistency_test(self, infokeys, datakeys):
        '''Used to make sure filenames are same between user-selected data and timefiles'''
        for afile in infokeys:
            if afile not in datakeys:
                self.file_consistency=False
                return False
        return True

    def update_file_data_info(self):
        file_data_info={}
        if self.formatted_datafile is not '' and self.formatted_timefile is not '':
            temp_data=load_formatted_info(self.formatted_timefile) #array full_info_dtype
            spec_data_dic=load_formatted_data(self.formatted_datafile) #filename_data
            if self.file_consistency_test(list(temp_data['filename']), spec_data_dic.keys() ) == False:
        #		warning(self.control, "Salary too low.  Collect unemployment.", "Salary")
                print '\nmistmatch found between timefile and data file filenames.\n  \
					Data structures not built!\n'
                return

            xvalues=spec_data_dic.pop('#Wavelength')
            for afile in temp_data['filename']:		
                timeindex=np.where(temp_data['filename']==afile)
                file_data_info[afile]=[(),()]  #List of tuples
                ###Force data into primary structure: this should be possible in one operation###
                data_array=np.array(zip(xvalues, spec_data_dic[afile]), dtype=spec_dtype)

                file_data_info[afile]=[(data_array), (temp_data[timeindex,:])] 

            self.file_data_info=file_data_info

    traits_view=View( 
        HGroup(Item('formatted_timefile') , Item('formatted_datafile')), 
        HGroup(Item('file_consistency', style='readonly'), Item('spec_consistency', style='readonly')),
        Item('storage', style='custom', show_label=True),
        resizable=True	)

class UnformattedRunData(RunData):
    ''' Formats data from a directory of unformatted files'''	
    rundir=Directory
    source=Str('Directory of Spec files')
    extension = Enum('.txt', '.py', 'Any', value='.txt')  #May want to put this on editor, not sure

    def _rundir_changed(self): self.update_file_data_info()

    def update_file_data_info(self):
        wd=os.getcwd()  #Store working directory
        os.chdir(self.rundir)  #So glob knows where to look
        file_data_info={}
        if self.extension =='Any':
            files=glob.glob("*.*")
        else:
            files = glob.glob("*"+self.extension+"*")

        ### For each file I open, I will test for consistency in wavelength values.  If they are not consistent file to file,
        ### I don't really correct it, just alert the user.  This method could be replaced by a general method in the rundata
        ### baseclass which looks throught he wavelength data file by file, but this may be superfulous for the deprecated 
        ### rundata class since it uses one spectrum for all the data

        spec_values=None
        for afile in files:
            file_data_info[afile]=[(),()]  #List of tuples
            file_data_info[afile][0]=load_spec(afile)
            file_data_info[afile][1]=load_info(afile)

        os.chdir(wd)  #Change working directory back	
        self.file_data_info=file_data_info

    traits_view=View(
        Item('rundir'), Item('extension'), Item('storage', show_label=False, style='custom'),
        resizable=True)

class FormattedRunData(RunData):
    '''Imports run directly from spectral files formatted in the canonical format of the spectrometer '''
    formatted_file=File
    source=Str('Formatted File')  #Will make this to understand the exported data of a previous run

class SimulationRunData(RunData):
    '''Interface to take in reflectance plots output form simulation program'''
    simfile=File
    source=Str('Simulation File')

    def _simfile_changed(self): self.update_file_data_info()

    def update_file_data_info(self):
        ''' Note, I also create a file_data_info object directly in a similar fashion from the simulation
            programs and can run these objects from simulation.  This is only for building an object
            up from a simulation file that had been saved previously '''
        if self.simfile is not '':
            f=open(self.simfile, 'r')

            ### Read in all the commented lines ###
            headers=[line for line in f if re.match('#', line)]	

            ### The last entry of commented lines is the run titles ###
            runs=headers[-1].strip('#,\n').split('\t')

            ### Load in row-delimited data ###
            data=np.loadtxt(self.simfile)
            xvalues=data[0]
            rundata=np.delete(data, [0], axis=0)  #THIS IS THE EQUIVALENT OF POPPING XVALUES OUT IN LIST SYNTAX
            f.close()			

            ### Set file_data_info in a dictionary comprehension ###
            ### NOT SURE WHAT INFORMATION TO RECORD ABOUT THE DATA IN THE SECOND HEADER PLACEHOLDER... ###
            self.file_data_info= {runs[i] : [(np.array(zip(xvalues, rundata[i]), dtype=spec_dtype) ) ,()] for i in range(len(runs))}



if __name__ == '__main__':
#	scene=UnformattedRunData()
#	scene=RunData()
#	scene=DeprecatedRunData()
    scene=SimulationRunData()
    scene.simfile='testsim.txt'  #Used for testing purposes
#	scene.simfile='testsim_2.txt'
    scene.configure_traits()







