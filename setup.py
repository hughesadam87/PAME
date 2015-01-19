import sys
import os
import os.path as op
from setuptools import setup, find_packages

NAME = 'PAME'

# Python >= 2.7 ?
user_py = sys.version_info
if user_py < (2, 7):
    raise SystemExit('%s requires python 2.7 or higher (%s found).' % \
                     (NAME, '.'.join(str(x) for x in user_py[0:3])))


#XXX Get current module path and do path.join(requirements)
#with open(op.join(sys.path[0], 'requirements.txt')) as f:
with open('requirements.txt', 'r') as f:
    required = f.readlines()
    required = [line.strip() for line in required]
    
# For now, most of these are in here for testing.  Dependency version 
#requirements can probably be relaxed, especially chaco.

# https://docs.python.org/2/distutils/setupscript.html#installing-package-data

# RI_INFO MATERIAL DATABASE
RIDIR = 'pame/data/RI_INFO'
FILETYPE = '.yml'
RIFILES =  [ (d, [os.path.join(d, f) for f in files if f.endswith(FILETYPE)]) 
             for d,folders,files in os.walk(RIDIR)]

# SOPRA MATERIAL DATABASE
RIDIR = 'pame/data/SOPRA'
FILETYPE = '.nk'
SOPRA =  [ (d, [os.path.join(d, f) for f in files if f.endswith(FILETYPE)]) 
             for d,folders,files in os.walk(RIDIR)]

# XNK MATERIALS
RIDIR = 'pame/data/XNK'
FILETYPE = '.nk'
XNK =  [ (d, [os.path.join(d, f) for f in files if f.endswith(FILETYPE)]) 
             for d,folders,files in os.walk(RIDIR)]

# Images
RIDIR = 'pame/images'
IMAGES =  [ (d, [os.path.join(d, f) for f in files]) 
             for d,folders,files in os.walk(RIDIR)]

setup(
    name = NAME,
    version = '0.1',
    author = 'Adam Hughes',
    maintainer = 'Adam Hughes',
    maintainer_email = 'hughesadam87@gmail.com',
    author_email = 'hughesadam87@gmail.com',
    packages = find_packages(), #What's this do?
    
    data_files = RIFILES + SOPRA + XNK + IMAGES,
    
    entry_points = {'console_scripts': 
                    [
                    'pame = pame.pamemain:main',
                    ]
                    },
    
#    url = 'http://hugadams.github.io/scikit-spectra/',
    download_url = 'https://github.com/hugadams/fibersim',
    license = 'LICENSE.txt',
    description = 'GUI for modeling nanoparticles on optical fiber with mixing/shell-filling models',
      classifiers = [
          'Development Status :: 3 - Alpha',
          'Environment :: Console',
          'Intended Audience :: Science/Research',
          'Intended Audience :: Developers',
          'Natural Language :: English',
#          'Operating System :: OSIndependent',  #This is limited only by 
          'Programming Language :: Python :: 2',
          'Topic :: Scientific/Engineering :: Visualization',
          'Topic :: Scientific/Engineering :: Chemistry',
          'Topic :: Scientific/Engineering :: Physics',
          'Topic :: Scientific/Engineering :: Medical Science Apps.',
          ],
 )

