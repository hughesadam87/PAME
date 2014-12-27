from traits.api import *
from traitsui.api import *
import numpy as np
from basic_material import BasicMaterial
from numpy import empty, interp, linspace
from converter import SpectralConverter
import os
import logging

class MaterialFileError(Exception):
    """ """

class ABCExternal(BasicMaterial):
    """ Base class for files and database linking (ie external) """
    # These are all displayed on Adapter View (Original x values of file)
    xstart = Property(Float)
    xend = Property(Float)
    xpoints = Property(Int)
    file_spec_unit = Str()        

    # Store the real data in the file
    file_x = Array()       
    file_n = CArray() #Complex array nr, ni  

    def _get_xstart(self):
        return self.file_x[0]
    
    def _get_xend(self):
        return self.file_x[-1]
    
    def _get_xpoints(self):
        return len(self.file_x)

    def update_interp(self):
        """Interpolates complex arrays from file data and sets self.narray (real and imaginary),
        could also set dielectric function, since BasicMaterial updates when either is changed."""
#        if len(self.file_x) != 0:  #If array populated

        nps = self.file_n
        xps = self.file_x

        # Reverse (This happens even in wavelength = nm data, just how files formatted)
        # Problem is, units like wavenumber should do this by default, so need to build that in...
        if self.file_x[0] > self.file_x[-1]:  #If last value is larger than first! (Then backwards)
            nps=nps[::-1] 
            xps=xps[::-1]    #Syntax to reverse an array 
            print "Had to sort values in material_files.update_interp\n"
            print 'nps.shape, xps.shape:', nps.shape, xps.shape

        n = interp(self.lambdas, xps, nps.real, left=0, right=0)
        k = interp(self.lambdas, xps, nps.imag, left=0, right=0)

        # Create complex array from two real arrays        
        self.narray = n + 1j*k

        
    def convert_unit(self):
        """ If file unit is not same as current unit"""
        if self.file_spec_unit != self.x_unit:
            # NEED AT ADD LAYER WHERE COMMON SYNONMYMS FOR WAVELENGTH ARE USED
            f = SpectralConverter(input_array=self.file_x,
                                  input_units=self.file_spec_unit,
                                  output_units=self.x_unit)
            self.file_x = f.output_array    

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
 
    delimiter = None #If not none, will split on a certain character.  Used for csv file
                     #Otherwise, default split()/genfromtxt will split on all whitespace

    header = Str()     
  
    
    def _file_path_changed(self):
        """ THIS HANDLES MAIN EVENT! 
           1. Read file Data 
           2. Convert Unit 
           3. Interpolate"""
        self.update_data()
        self.update_interp()
        self.update_mview()
    
    
    # Unit Conversions
    def _file_spec_unit_changed(self):
        self.convert_unit()
    
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
                     Item('mviewbutton'),
                     Item('file_path') )

class XNKFileCSV(XNKFile):
    """ Wavelength, N, K delimited, 3-column file but comma-separated."""
    fileid='xnk_csv'
    delimiter = ','
    file_extension='.csv' 
    

class SopraFile(ABCFile):  

    ###NEEDS FIXED TO WORK W NEW SPECPARMS AND STUFF###

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

        self.file_x = linspace(xstart, xend, xpoints+1) #<< +1?

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
