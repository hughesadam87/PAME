import os.path as op

__docformat__ = 'restructuredtext' #What's this actually do

pkg_dir = op.abspath(op.dirname(__file__))
data_dir = op.join(pkg_dir, 'data')

sopra_dir = op.join(data_dir, 'SOPRA')
riinfo_dir = op.join(data_dir, 'RI_INFO')
misc_dir = op.join(data_dir, 'MISC')
