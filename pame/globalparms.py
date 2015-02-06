""" Variables with shared names which are accessed by different components of programs.  Good
practice to have these here incase change names on a whim in one place and forget that they
are used elsewhere.
"""

from collections import OrderedDict

'''
* r--reflection amplitude
    * t--transmission amplitude
    * R--reflected wave power (as fraction of incident)
    * T--transmitted wave power (as fraction of incident)
    * A--total absorbed power (as fraction of incident) = (1 - (R+T) )
    * power_entering--Power entering the first layer, usually (but not always)
      equal to 1-R (see manual).
    * vw_list-- n'th element is [v_n,w_n], the forward- and backward-traveling
      amplitudes, respectively, in the n'th medium just after interface with
      (n-1)st medium.
    * kz_list--normal component of complex angular wavenumber for
      forward-traveling wave in each layer.
    * th_list--(complex) propagation angle (in radians) in each layer
    * pol, n_list, d_list, th_0, lam_vac--same as input
'''

_flat_suffix = 'L'  # For layer-dependent optical props like kz_1, kz_2 --> kz_L1, kz_L2

_header = (
    # Dimension F(wavelength) for a given angle
    ('r_amp','Reflection Amplitude'), 
    ('t_amp','Transmission Amplitude'),
    ('R', 'Reflectance'),
    ('T', 'Transmittance'),
    ('A', 'Absorbance'),
    ('pe', '1st Layer Power'),  # Basically 1-R
    
    # All below have dimension F(wavelength, layers) for a given angle
    ('vn', 'Forward Traveling Amp.'),  
    ('wn', 'Backward Traveling Amp.'),
#    ('vw','vw_list'),
    ('kz','Wavenumber Normal Comp.'),
    ('absorb', 'Proportion Light Absorbed'),    
    ('ang_prop','Propagation angle (rad)')
    )

# http://en.wikipedia.org/wiki/Ellipsometry
#http://www.aps.org/units/fiap/meetings/presentations/upload/tompkins.pdf
_ellipsometry = (
    ('r_delta', 'Reflectance Phase'),
    ('r_psi', 'Reflectance Amp Ratio')
    )

header = OrderedDict((k, v) for k, v in _header+_ellipsometry)
selected = ['R','T','A'] #<--- Default selected traits for primary view

# Names of Categories used in View and in Simulation output
globsname = 'Main' # Globals
strataname = 'Substrate'
stackname = 'Stack'
materialname = 'Material'

optresponse = 'Optical Response'
spectralparameters = 'Spectral Parms.'

semiinf_layer = 'semi-infinite' #Substrate/Solvent designator
