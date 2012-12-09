import scipy as sp
from scipy import interpolate
import re
import matplotlib.pyplot as plt
import numpy as np


def reverse_test(x_array):
	'''check to see if wavelengths are backwards'''
	old=0   #Starting condition
	for entry in x_array:
		if old != 0:
			if entry > old:
				status='fine'
			else:
				status='reverse'
		old=entry		
	return status

###EDIT FILE NAME VARIABLE AND SPLITTING INCREMENT

inname='JC_Gold.txt'
intervals=100   #Splits original file into this man
outname='test.txt'

f=open(inname, 'r')
o=open(outname, 'w')
oldline='blank'   #Starting iterator value

lams=[]
ns=[]
fs=[]

for line in f:
	if not re.match('#', line):
		line=line.strip()
		newline=line.split()

		lam_new=newline[0] ; nr_new=newline[1] ; ni_new=newline[2] 
		er_new=newline[3] ; ei_new=newline[4]

		lams.append(float(lam_new))
		ns.append(float(nr_new))


if reverse_test(lams) == 'reverse':
	print 'REVERSE DATA TO BEFORE INTERPOLATION'
	lams.reverse()
	ns.reverse()


func=sp.interpolate.interp1d(lams, ns, kind='linear', fill_value=10)
func=np.interp(lams, lams, ns)
#new=func(ns)
print func
plt.scatter(lams, ns, color='red')
plt.plot(lams, func, color='blue')
plt.show()




			
