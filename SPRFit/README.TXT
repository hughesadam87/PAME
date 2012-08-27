Padova, April 2009
MGFit Version 1.0 and LNMGFit Version 1.0 
Vincenzo Amendola & Moreno Meneghetti

Details about fitting model and parameters are described in the paper:
"Size evaluation of gold nanoparticles by UV-vis spectroscopy", 
V.Amendola and M.Meneghetti; J.Phys. Chem. C 2009, 113 (11), pp 4277 - 4285 - DOI : 10.1021/jp8082425

The following files are included in the folder SPRFit:

1- MGFit 1.0.nb
It is a fitting program working under Wolfram Mathematica 4.0 or 6.0 for Windows, which use a combination 
of the mie model and the gans model for the estimation of the size of metl nanoparticles 
from their surfae plasmon resonance (SPR) in the UV-Vis wavelength interval.

2- LNMGFit 1.0.nb
It is a fitting program working under Mathematica 4.0 or 6.0 for Windows, which use a combination 
of the mie model and the gans model for the estimation of the size of metl nanoparticles 
from their surfae plasmon resonance (SPR) in the UV-Vis wavelength interval. It differs 
from MGFit because here a LogNormal distribution of size is considered for spherical metal 
nanoparticles.

3- PalikAu.txt
It is a sample dielectric constant file extracted by the values tabled for gold by E. D. Palik in the 
 the Handbook of Optical Constants of Solids; Academic Press: New York, 1985. 
The file format is the correct one for the fitting programs. 

4- J&CAu.txt
It is a sample dielectric constant file with the values tabled for gold by P.B. Johnson and R.W. 
Christy in Phys. ReV. B 1972, 6, 4370-4379.
The file format is the correct one for the fitting programs. 
This dielectric constant is more reliable than the Palik one for wavelenghts larger than 600 nm.
  
5- Sample.dat
It is a sample UV-vis spectrum of free gold nanoparticles (AuNP) in water solution obtained by LASiS+size reduction.
The file format is the correct one for the fitting programs. 

6- MFitting of Sample.dat
It is a sample of the output file of the MGFit or LNMGFit after the fitting with the Mie model for 
spheres only.

7- MGFitting of Sample.dat
It is a sample of the output file of the MGFit after the fitting with the Mie Gans model.

8- LNMGFitting of Sample.dat
It is a sample of the output file of the LNMGFit after the fitting with the LogNormal Mie Gans model.

9- SampleNormalized.dat
It is the normalized input file as used by the fitting programs.
