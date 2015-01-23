import sys
from cx_Freeze import setup, Executable

import os, glob2, numpy, scipy, PyQt4


#python setupbinary.py build && cd build/exe.linux-x86_64-2.7/ && ./pamemain


# https://bitbucket.org/anthony_tuininga/cx_freeze/issue/43/import-errors-when-using-cx_freeze-with
explore_dirs = [
#        os.path.dirname(numpy.__file__),
#        os.path.dirname(scipy.__file__),
#        os.path.dirname(PyQt4.__file__)
    ]

files = []
#for d in explore_dirs:
#    files.extend( glob2.glob( os.path.join(d, '**', '*.pyo') ) ) #PyQt4
#    files.extend( glob2.glob( os.path.join(d, '**', '*.yml') ) )
#    files.extend( glob2.glob( os.path.join(d, '**', '*.so') ) )
#    files.extend( glob2.glob( os.path.join(d, '**', '*.pyx') ) )
#    files.extend( glob2.glob( os.path.join(d, '**', '*.pyd') ) )

    # Now we have a list of .pyd files; iterate to build a list of tuples into 
    # include files containing the source path and the basename
extrafiles_data = []
for f in files:
    extrafiles_data.append( (f, os.path.basename(f) ) )

# folders
extrafiles_data += ['data/']
extrafiles_data += ['images/']


# Dependencies are automatically detected, but it might need fine tuning.

#'kiva.*',
 #'enable.*',
 #'enable.qt4.*',
 #'pyface.*',
 #'pyface.ui.qt4.*',
 #'pyface.ui.qt4.action.*',
 #'pyface.ui.qt4.timer.*',
 #'pyface.ui.qt4.wizard.*',
 #'pyface.ui.qt4.workbench.*',
 #'traitsui.qt4.*',
 #'traitsui.qt4.extra.*',
 #'PyQt4.pyqtconfig',

build_exe_options = {"packages": ["os",
                                  "sys",
                                  "collections",
                                  "enable", 
                                  "kiva", 
                                  "scipy", 
                                  "pyface",
                                  "PyQt4"
                                  ],
                     "includes":[#"sip", "PyQt4.QtCore", #http://openclassrooms.com/forum/sujet/cx-freeze-pyqt4
                                  "pyface.ui.qt4",
                                  "pyface.qt",
                                  "pyface.i_image_resource",
                                  "PyQt4.uic.port_v2",
#                                  "PyQt4.uic.Compiler.proxy_type",
                                  "pyface.ui.qt4.action",
                                  "pyface.ui.qt4.timer",
                                  "pyface.ui.qt4.wizard",
                                  "pyface.ui.qt4.image_resource",
                                  "pyface.ui.qt4.workbench",
                                  "traitsui",                                  
                                  "traitsui.qt4",
                                  "traitsui.qt4.extra",
#                                  "PyQt4.uic.port_v3.proxy_base",
#                                  "PyQt4.pyqtconfig"],
                                  ],

                     "include_files":extrafiles_data,

                     "excludes": ["collections.abc"]#, "PyQt4.uic.port_v3"] 
                     }
# http://stackoverflow.com/questions/15561722/error-in-py2exe-python-app-using-chaco-in-pyside

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(  name = "pamebinary",
        version = "0.1",
        description = "My GUI application!",
        options = {"build_exe": build_exe_options},
        executables = [Executable("pamemain.py", base=base)]
    )

# Good example of better installer
# https://github.com/pathomx/pathomx/blob/master/setup.installers.py
