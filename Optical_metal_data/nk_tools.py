#data_tools.py  (Set of functions to manipulate nk data)
import re, sys
import matplotlib.pyplot as plt
import cmath

def to_nm(unit, value):
	'''Takes in unit parameter of file as well as a value and returns nm equivalent.  For example, unit=1 means EV.  Value of 1.5ev would return 827.5nm '''
	h=4.135667516 * (10**-15) #eV S  
	c=299792458  #m/s
	if unit==1:  #sopra format 1=EV
		lam=(h*c/(value))*(1.0*10**9)
	elif unit==2:  #um
		lam=value*1000.0
	elif unit==3:  #cm
		lam=value*(1.0*10**7)
	elif unit==4:  #nm
		lam=value
	else:
		print '\n Could not convert units, check header, exiting\n';sys.exit()
       	return lam


name=raw_input('\n\nEnter File name of .nk file to use; header format spectral unit, start, end, total data points\n\n')
out=raw_input('\n\nEnter outfile name (ie test.txt)\n\n')

f=open(str(name), 'r')
o=open(str(out), 'w')
o.write('#Wavelength' + '\t' + 'n' + '\t' + 'k' + '\t' + 'er' + '\t' + 'ei'+ '\n') 
firstline=f.readline()
header=firstline.strip()
header=header.split()

unit=int(header[0])
start=float(header[1])
stop=float(header[2])
total=float(header[3])

full_range=abs(stop-start)
spacing=full_range/total

lams=[]
ns=[]
ks=[]
ers=[]
eis=[]

k=start            #Dummy iterator variable
for line in f:
	line=line.strip()
	sline=line.split()
	lam=to_nm(unit, k)
	nreal=float(sline[0])
	nimg=float(sline[1])
#	nimg=-nimg
	lams.append(lam)
	ns.append(nreal)
	ks.append(nimg)

	er=(nreal**2 - nimg**2)
	ei=2.0*nreal*nimg	        #Compute dielectric fcn
	ers.append(er)
	eis.append(ei)

	print nreal, nimg, er, ei, lam
	o.write(str(lam) + '\t' + str(nreal) + '\t' + str(nimg) + '\t' + str(er) + '\t' + str(ei) +'\n')
	k=k+spacing
#plt.scatter(lams, ers, color='red')
plt.scatter(lams, eis, color='blue')
#plt.scatter(lams, ns)
plt.xlim([200,900]) 
plt.ylim([0,8])
#plt.ylim([-40,5])
plt.title('Img dielectric SOPRA database')
plt.xlabel('Wavelength')
plt.ylabel('Relative Dielectric')
plt.show()

