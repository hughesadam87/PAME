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

_header = (
    ('r','ref. Amp'), 
    ('t','trans. Amp.'),
    ('R', 'Reflected'),
    ('T', 'Transmitted'),
    ('A', 'Absorbed'),
    ('pe', '1st Layer Power'),
    ('vw','vw_list'),
    ('kz','kz_list'),
    ('ang_prop','Propagation angle')
    )

header = OrderedDict((k, v) for k, v in _header)
    
print header.values(), 'lol'