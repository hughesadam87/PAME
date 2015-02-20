from traits.api import *
from traitsui.api import *
import numpy as np
from basic_material import BasicMaterial
from converter import SpectralConverter
import scipy.interpolate as scinterp
import os
import logging
from pame.utils import complex_n_to_e

class MaterialFileError(Exception):
    """ """

class ABCExternal(BasicMaterial):
    """ Base class for files and database linking (ie external) """
    # These are all displayed on Adapter View (Original x values of file)
    xstart = Property(Float)
    xend = Property(Float)
    xpoints = Property(Int)
    file_spec_unit = Str()        

    interpolation = Enum('linear',
                         'nearest', 
                         'zero',
                         'slinear',
                         'quadratic', 
                         'cubic')

    # Store the real data in the file; should be visualized on mview later
    file_x = Array()      
    file_n = CArray() #Complex array nr, ni  
    file_e = Property(CArray, depends_on='file_n')
    xps_in_nm = Array() #<-- x values in file in nanometers
    
    def _get_file_e(self):
        return complex_n_to_e(self.file_n)

    def _get_xstart(self):
        return self.file_x[0]
    
    def _get_xend(self):
        return self.file_x[-1]
    
    def _get_xpoints(self):
        return len(self.file_x)
    
    def _lambdas_changed(self):
       #update data only re-reads file, so don't need udpate_data()
        self.update_interp()        
    
    def _interpolation_changed(self):
        self.update_interp()

    def _extrapolation_changed(self):
        self.update_interp()

    def update_interp(self):
        """Interpolates complex arrays from file data and sets self.narray (real and imaginary),
        could also set dielectric function, since BasicMaterial updates when either is changed."""
        nps = self.file_n
        xps = np.copy(self.xps_in_nm)
        
        # xps is always nm, so if goes large, small, reverse N's
        if xps[0] > xps[-1]:
            nps=nps[::-1] 
            xps=xps[::-1]    #Syntax to reverse an array             

        # Spline interpolation.  
        f = scinterp.interp1d(xps, nps, kind=self.interpolation, bounds_error=False)             
        narray = f(self.lambdas)
                
        if self.extrapolation:
            #Only extrapolate if there are Nans.  Mask by dropping Nans
            #And passing full x, dropped x and narray.  Can't be complex,
            #even though spline interp can be...
            # http://docs.scipy.org/doc/numpy/reference/generated/numpy.interp.html            
            if np.isnan(self.narray).any():
                xmask = self.lambdas[np.logical_not(np.isnan(narray))]
                nmask = narray[np.logical_not(np.isnan(narray))]
                n = np.interp(self.lambdas, xmask, nmask.real)#, left=0, right=0)
                k = np.interp(self.lambdas, xmask, nmask.imag)#, left=0, right=0)
                narray = n + 1j*k

        self.narray = narray

    def _xps_in_nm_default(self):
        """ Store file datapoints in nm (only need once assuming Nanometer
        unit system is used internally in PAME
        """
        conv = SpectralConverter(input_array=self.file_x,
                                 input_units=self.file_spec_unit,
                                 output_units='Nanometers')  
        return conv.output_array

    def update_data(self):
        """ Must set header, set file_x, set file_n and call updated_interp() """
        pass
    

class ABCFile(ABCExternal):
    """ General model to store data from file.  
    
    Notes
    -----
    In update_data(), readas file, sets header, sets n arrays, also stores original 
    file wavelengths and other metdata.
    
    Metadata includes file id, 
    name, header.  'file_path' must be set on instantiation!! 
    
    Check out file Adapter for how files are stored without storing all their data.
    (basic_materials_adapter.ABCFileAdapter)
    """
    
    source = 'File'
    file_path = File() 
    short_name = Property(depends_on='file_path')
    file_id = Str()  #Used to identify with methods below.  For example, Sopra is "Sopra"
    file_extention = Str() #Again, not all files may have this
    header = Str()     
 
    delimiter = None #If not none, will split on a certain character.  Used for csv file
                     #Otherwise, default split()/genfromtxt will split on all whitespace
  
    def _file_path_changed(self):
        """ THIS HANDLES MAIN EVENT! 
           1. Read file Data 
           3. Interpolate
           """
        self.update_data()
        self.update_interp()    
    
    #def _file_spec_unit_changed(self):
        #raise MaterialFileError('Design choice to disallow changing of file_spec_unit')
    ## This shouldn't happen
    ##    self.update_interp()
    
    def _get_short_name(self):
        return os.path.basename(self.file_path)
    
    def update_data(self):
        """ Must set header, set file_x, set file_n and call updated_interp() """
        pass
        

class XNKFile(ABCFile):
    """3-coloumns header: lambdas, N, K as arrays."""
    fileid='xnk'
    delimiter = None
  #  file_extension='.txt'  #not used/clear

    def update_data(self):
        """ File must have a header of from (specunit, N, K).  From header, 
        specunit is set.  N and K are read into arrays.  
        """
        with open(self.file_path, 'r') as f:
             self.header = f.readline().lstrip('#').strip()
                
            
        try:
            self.file_x, n, k = np.genfromtxt(self.file_path, 
                                          unpack=True, 
                                          skip_header=1,
                                          delimiter=self.delimiter)
        except Exception as exc:
            raise MaterialFileError(r'Could not read %s with np.genfromtxt'
                ' Make sure it is three column, with single header of form'
                ' (specunit, N, K). TracebacK:\n\n%s' %
                (self.short_name, exc) )
        
        
        else:                  
            self.file_n = n + 1j*k

            # Set default unit from header[0]
            self.file_spec_unit = self.header.split(self.delimiter)[0]


    traits_view=View(Item('header', style='readonly'),
                     Item('mviewbutton', show_label=False, label='Show Material'),
                     Item('file_path', style='readonly') )
    

class XNKFileCSV(XNKFile):
    """ Wavelength, N, K delimited, 3-column file but comma-separated."""
    fileid='xnk_csv'
    delimiter = ','
    file_extension='.csv' 
    

class SopraFile(ABCFile):  

    file_id='Sopra'
    file_extension='.nk'

    traits_view=View(  
        Item('mviewbutton', label='Show Material', show_label=False),
        Item('file_path', editor=FileEditor() ) ,
        Item('header' ),
        HGroup(
            Item('xstart', style='readonly') ,
            Item('xend', style='readonly'),
            Item('xpoints', style='readonly'),
            ),
        Item('file_spec_unit', label='File spectral unit', style='readonly'), 
        Item('x_unit', style='readonly', label='Current spectral unit'),
        resizable=True, buttons=['Undo']
        )


    def update_data(self):

        with open(self.file_path, 'r') as f:
            self.header = f.readline().lstrip('#').strip()             
        
        # Parse SOPRA header (ALLOW FOR COMMA OR MATDELIM cuz comma is common)        
        headerlist = self.header.split(self.delimiter)

        code = int(headerlist[0])
        xstart = float(headerlist[1])
        xend = float(headerlist[2])
        xpoints = int(headerlist[3])

        self.file_x = np.linspace(xstart, xend, xpoints+1) #<< +1?

        # Set specunit ...
        if code==1:
            self.file_spec_unit='eV'
        
        elif code==2:
            self.file_spec_unit='Micrometers'

        elif code==3:
            self.file_spec_unit='cm-1'   #Inverse centimeters	

        elif code==4:
            self.file_spec_unit='Nanometers'
        else:
            raise MaterialFileError('Sopra specunit code must be 1,2,3 or 4.  Got: %s' % code)

        # Populate arrays (2 column)
        n, k = np.genfromtxt(self.file_path, 
                            unpack=True,
                            skip_header=1)
        
        self.file_n = n + 1j*k
