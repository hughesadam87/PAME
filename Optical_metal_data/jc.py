#jc.py
'''Used to convert johnson/christy text data'''
import re
import matplotlib.pyplot as plt

lams=[]
ns=[]
ks=[]
ers=[]
eis=[]



f=open('JC.txt', 'r')
o=open('JC_Gold.txt', 'w')
o.write('#Wavelength' + '\t' + 'n' + '\t' + 'k' + '\t' + 'er' + '\t' + 'ei'+ '\n') 

for line in f:
	if not re.match('#', line):
		line=line.strip()
		sline=line.split()
		lam=float(sline[0]) * 1000
		lams.append(lam)
		nreal=float(sline[1]); nimg=float(sline[2])
		ns.append(nreal)
		ks.append(nimg)

		er=(nreal**2 - nimg**2)
		ei=2.0*nreal*nimg	        #Compute dielectric fcn
		ers.append(er)
		eis.append(ei)
		o.write(str(lam) + '\t' + str(nreal) + '\t' + str(nimg) + '\t' + str(er) + '\t' + str(ei) +'\n')

#plt.scatter(lams, ns, color='red')
#plt.scatter(lams, ks, color='blue')
#plt.scatter(lams, ers, color='green')
plt.scatter(lams, eis, color='black')
plt.xlim([300,900]) 
plt.ylim([0,6])
plt.title('Img dielectric GOLD John Chris')
plt.xlabel('Wavelength')
plt.ylabel('Relative Dielectric')
plt.show()
