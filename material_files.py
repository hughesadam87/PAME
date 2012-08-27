from traits.api import *
from traitsui.api import *
from basic_material import BasicMaterial
from numpy import empty, interp, linspace
from converter import SpectralConverter
import re, os

class BasicFile(BasicMaterial):
    '''Has no implementation of mat_name...maybe that's ok'''
    source='File'
    thefile=File() #Shortname? of file
    file_id=Str()  #Used to identify with methods below.  For example, Sopra is "Sopra"
    file_extention=Str() #Again, not all files may have this

    header=Str()       #Not all files will have this (CHANGE TO BOOL AND MAKE A GET HEADER METHOD IN GENERAL)
    headerlist=Property(List, depends_on='header')
    headerstatus=Bool(False)
    datalines=List()  #Data stored as lines
    datalist=Property(List, depends_on='datalines')

    xstart=Float()
    xend=Float()
    xpoints=Int()
    default_unit=Str()        #DEFAULT SPECTRAL UNIT IN A FILE

    file_x=Array()       #Store the real data in the file
    file_n=Array()

    #FOR NOW THIS DOES NOT INCORPORATE FILE_E BECAUSE OF PROPERTY ISSUES, NEEDS MORE THOUGHT

    def _file_x_changed(self): self.update_interp()
    def _file_n_changed(self): self.update_interp()

    def _thefile_changed(self): 
        self.header_data()	
        self.update_file()  
        self.update_mview()

    def update_file(self): 	pass

    def _get_datalist(self):
        '''Given the data as a list of lines, turns it into a list of lists'''
        data=[]
        for line in self.datalines:
            newline=line.strip().split()
            newlist=[]
            for entry in newline:
                newentry = float(entry)
                newlist.append(newentry)
            data.append(newlist)
        return data

    def _get_headerlist(self): return self.header.strip().split()

    def header_data(self):
        '''Should be general enough to fit all files with comment characters on first line'''
        f=open(self.thefile, 'r')
        data=f.readlines()
        firstline=data[0]
        if re.match('#', firstline):
            self.header=firstline 
            self.headerstatus=True
            data.pop(0)     #IF HEADER FOUND, POP IT OUT

        self.datalines=data  #Datalist is set as property

    def update_interp(self):
        '''Method interpolates complex arrays and also reverses when appropriate'''
        temp=empty( (self.lambdas.shape), dtype='complex')
        if self.file_x[0] > self.file_x[-1]:  #If last value is larger than first! (Then backwards)
            nps=self.file_n[::-1] 
            xps=self.file_x[::-1]    #Syntax to reverse an array 
            print "Had to sort values \n"
        print nps.shape, xps.shape
        a=interp(self.lambdas, xps, nps.real, left=0, right=0)
        b=interp(self.lambdas, xps, nps.imag, left=0, right=0)
        temp.real=a ; temp.imag=b
        self.narray=temp

class NK_Delimited(BasicFile):
    '''Format is Lambdas, N, K'''
    fileid='nk_delim'
    file_extension='.txt'  #FIX LATER

    def update_file(self):
        self.header_data()
        ns=empty(len(self.datalist), dtype=complex)
        lams=empty(len(self.datalist), dtype=float)
        for i in range(len(self.datalist)):
            line=self.datalist[i]
            lams[i]=float(line[0])
            ns[i]=complex(float(line[1]), float(line[2]))
        self.file_n=ns;	self.file_x=lams

    traits_view=View(Item('header', style='readonly'), Item('mviewbutton'), Item('thefile') )


class SopraFile(BasicFile):  

    ###NEEDS FIXED TO WORK W NEW SPECPARMS AND STUFF###

    file_id='Sopra'
    file_extension='.nk'
    lam_code=Enum(1,2,3,4)     #SOPRA-specific integer code to determine name of the lambda unit

    traits_view=View(  
        Item('thefile', editor=FileEditor() ) , Item('header' ),
        HGroup(
            Item('xstart', style='readonly') , Item('xend', style='readonly'),	Item('xpoints', style='readonly'),
            ),
        Item('mviewbutton', label='Show Material', show_label=False),
        Item('default_unit', label='File spectral unit', style='readonly'), 
        Item('x_unit', style='readonly', label='Current spectral unit'),
        resizable=True, buttons=['Undo']
    )

    def lam_decode(self):
        '''Converts sopra unit integer code to forms appropriate to this'''
        if self.lam_code==1:
            self.default_unit='eV'
        elif self.lam_code==2:
            self.default_unit='Micrometers'
        elif self.lam_code==3:
            self.default_unit='cm-1'   #Inverse centimeters	
        elif self.lam_code==4:
            self.default_unit='Nanometers'
        if self.default_unit != self.x_unit:
            f=SpectralConverter(input_array=self.file_x, input_units=self.default_unit, output_units=self.x_unit)
            self.file_x=f.output_array


    def update_file(self):
        if self.headerstatus == True:
            self.lam_code=int(self.headerlist[0])
            self.xstart=float(self.headerlist[1])
            self.xend=float(self.headerlist[2])
            self.xpoints=int(self.headerlist[3])
            self.file_x=linspace(self.xstart, self.xend, self.xpoints+1)
            self.lam_decode()
            ns=empty(len(self.datalist), dtype=complex)
            for i in range(len(self.datalist)):
                line=self.datalist[i]
                ns[i]=complex(float(line[0]), float(line[1]))
            self.file_n=ns

    def header_data(self):
        '''Slightly modified for unusual sopra header'''
        f=open(self.thefile, 'r')
        data=f.readlines()
        firstline=data[0]
        if len(firstline.strip().split()) != 4:         #Crude file format test
            self.header='SOPRA FORMAT INCORRECT'
        else:
            self.header=firstline
            self.headerstatus=True
            data.pop(0)     #IF HEADER FOUND, POP IT OUT
        self.datalines=data
