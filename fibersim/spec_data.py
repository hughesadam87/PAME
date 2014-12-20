import numpy as np

#### Defines np dtype and methods for extracting file data, info from spectral data sheet individualy #####

spec_dtype = np.dtype([
	     ('wavelength', float),
   	     ('intensity', float)
			])

full_info_dtype=np.dtype([
	     ('filename', file),
	     ('user', str, 10),
	     ('dark_spec_present', str, 3),  #No or yes
	     ('ref_spec_present', str, 3),
   	     ('year', int),
	     ('month', str, 5), #I'm leaving extra string space, since default is 0, and these are only filling up partially
	     ('day', int),
 	     ('time', str, 8),
	     ('int_time', int),
	     ('int_unit', str, 10),
	     ('avg', int),
	     ('boxcar', int),
	     ('elec_dark_corr', str, 3),
	     ('strobe_enabled', str, 3),
	     ('non_linear_corr', str, 3),
	     ('stray_light_corr', str, 3),
			])

def load_spec(spec_file):
   ''' Extracts spectral data from single spectral file type by skipping all non-data rows,
       skips header as well as the wavelength data'''
   data=np.loadtxt(spec_file, spec_dtype, skiprows=16, comments='>') 
   return data

def load_info(spec_file):
   ''' Extracts data from header of a single spectral file, formats it into a list and forces it into a np array of 
	dtype full_info_dtype.  Verifies file by the first line saying spectrasuite data file, but also if the
	file type was wrong, the np array would not be read in to begin with'''
   f=open(spec_file, 'r')
   header=f.readlines()[0:16]
   if header[0].strip() == 'SpectraSuite Data File':  #This is the only check used to verify data is correct
	header=header[2:15]
        stats=[]  #Stripped down header
        for entry in header:
		entry=entry.strip()
		stats.append(entry.split(': ')[1])
	mdy=stats[0].split()
	int_unit=header[6].split()[2].strip(':,),(')
	month=mdy[1] ; day=mdy[2] ; time=mdy[3] ; year=mdy[5]
	new_stats=tuple([(spec_file), (stats[1]), (stats[2]), (stats[3]), (year), (month), (day), (time), (stats[6].split()[0]), 
			(int_unit),(stats[7].split()[0]), (stats[8].split()[0]), (stats[9].split()[0]),
			 (stats[10].split()[0]), (stats[11].split()[0]), (stats[12].split()[0])  
			  ])
	full_array= np.array(new_stats, dtype=full_info_dtype)
	return full_array
   else:
	## PUT WARNING/ERROR HERE ##
	return None

### Defines np dtype and methods for importing time and spectral data from pre-formatted timefile and runfile ###

timefile_dtype=np.dtype([
	     ('filename', file),  #List of individual run neams
   	     ('year', int),
	     ('month', str, 5), #I'm leaving extra string space, since default is 0, and these are only filling up partially
	     ('day', int),
 	     ('time', str, 8),
	     ('int_time', int),
	     ('int_unit', str, 10),  
	     ('avg', int),
	     ('boxcar', int),
			])
def load_formatted_info(formatted_timefile):
    ''' Returns array data from the formatted file from old-type data files.  This data is made using the data_manipulator module
	and has some information lost which is why I've defined full_info_dtype below'''
    data=np.loadtxt(formatted_timefile, dtype=timefile_dtype, delimiter='\t')  
    return data

def load_formatted_data(formatted_spectralfile):
	''' Simply loads the old-style formatted spectral file and returns filename:data in an array.  
	    Further modifications of data structures are done in the RunData class '''
	file_dic={}; index=0
	f=open(formatted_spectralfile, 'r')
	header=f.readline().strip().split() 
	arraydata=np.genfromtxt(formatted_spectralfile, delimiter='\t', dtype=float) 
	for afile in header:
		file_dic[afile]=arraydata[:, index]
		index=index+1
	f.close()
	return file_dic

###DONT FORGET CAN ACCESS NAMES
###data.dtype.names = names
#In [34]: def reader(filename):
#  ....:     infile = open(filename, 'r')
#  ....:     names = infile.readline().split()
#  ....:     infile.close()
#  ....:     data = N.genfromtxt(filename, names=True)
#  ....:     data.dtype.names = names
#  ....:     return data

###############################
#Following method is deprecated
###############################

def load_formatted_data_deprecate(formatted_spectralfile):
	''' Extracts spectral data from an old-style formatted datafile and uses column labels as access names to array '''
	file_dic={}; outstring=''
	f=open(formatted_spectralfile, 'r')
        header=f.readlines()[0]

	### This is a very nonmodular splitting routine to map the header to the column names for###
	### the genfromtxt module to understand.  It can't use Names because Names gets confused by file extension ###
	header=header.strip('#').split()  #Write header intoa  list
	for entry in header:
		if outstring == '':
			outstring=entry.split('.')[0]
		else:
			outstring=outstring+','+entry.split('.')[0]
	outstring=outstring+','

	### Load data into an array with stripped file names mapped to names attribute ###
        data=np.genfromtxt(formatted_spectralfile, names=outstring, delimiter='\t', dtype=float) 

	### Build dictionary of full file name as key, data value of the stripped name as value 

#>>> x = np.array([(8.0, 7.0), (6.0, 7.0)], dtype=dt)

	for afile in header:
		file_dic[afile]=np.array([
					 (data['Wavelength']), 
					 (data[afile.strip().split('.')[0]])
					 ], dtype=spec_dtype)  #Dictionary of full filename to array
	f.close()
	return file_dic
