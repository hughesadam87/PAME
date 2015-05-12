.. image:: https://github.com/hugadams/PAME/blob/master/screenshots/gui.png
   :height: 100px
   :width: 200 px
   :scale: 50 %

==========================================
PAME: Plasmonic Assay Modeling Environment
==========================================

Graphical Python application for simulating plasmonic biosensors, particularly fiberoptic biosensors with nanoparticles.

Check out the `PAME preprint`_.

    .. _PAME preprint : https://linktonowhere

Tutorials
=========

IPython Notebooks
-----------------
Some of these are traditional tutorials, others are examples of analyzed data from our lab.

    - `Simultation Parsing Tutorial <https://github.com/hugadams/PAME/blob/master/Simulations/simtutorial.ipynb>`_
    - `Gold Nanoparticle Self-Assembly Compared to Experimental Data <https://github.com/hugadams/PAME/blob/master/Notebooks/SAM_pametest.ipynb>`_
        - Experimental datasets are preloaded in `scikit-spectra library <http://hugadams.github.io/scikit-spectra/>`_
    - `Simulating a Refractometer <https://github.com/hugadams/PAME/blob/master/Notebooks/glycerin_simulation.ipynb>`_
    - `Protein binding to gold nanoparticle film <https://github.com/hugadams/PAME/blob/master/Notebooks/bsa_shell_sim.ipynb>`_
    - `Gold and Silver Nanoparticle Combined Layer 1 <https://github.com/hugadams/PAME/blob/master/Notebooks/AuAg_protein.ipynb>`_
    - `Gold and Silver Nanoparticle Combined Layer 2 <https://github.com/hugadams/PAME/blob/master/Notebooks/AuAg_sameheight_protein.ipynb>`_

Screencasts
-----------
Tutorials are cumulative (eg screencast 2 picks up where 1 ends).

PAME's tutorials are a series of screencasts.  
    - Screencast 1: `Introduction to PAME- Anti-reflective coatings <https://youtube.com/watch?v=Na3vK8WsBHI>`_
    - Screencast 2: `Introduction to Nanoparticles <https://www.youtube.com/watch?v=ykF67bfCSlc>`_
    - Screencast 3: `Nanoparticle film with silica shell <https://www.youtube.com/watch?v=58y53AiB1GQ>`_
    - Screencast 4: `Nanoparticle film with protein shell <https://www.youtube.com/watch?v=EZzoOMxI3ss>`_
    - Screencast 5: `Intro to Fiberoptic Dip Sesnosr <https://www.youtube.com/watch?v=1xOxBkiCICs>`_
    - Screencast 6: `Multiplexed Dip Sensor with Gold and Silver Nanoparticles <https://www.youtube.com/watch?v=r0k9215ctfw>`_
    - Screencast 7: `Gold Nanoparticle Fiber Dip Sensor Simulation <https://www.youtube.com/watch?v=Q6H_f46dZZc>`_ 
    - Screencast 8: `Dip Sensor with Organosilane Layer <https://www.youtube.com/watch?v=FzMon52iHQo>`_  

Installation
============

Binaries (ie .exe one-click use files) are `under development <https://bitbucket.org/anthony_tuininga/cx_freeze/issue/127/collectionssys-error#comment-15016355>`_, but for now, PAME must be installed as a python library and launched through the command line.  Anyone interested in helping to develop binaries, please contact.  

PAME makes heavy use of the `SciPy Stack (numpy, ipython etc...) <http://www.scipy.org/install.html>`_, and so it has a lot of dependencies.  If you are new to Python, or want to install PAME into a clean environment (this is suggested), see the `Conda` installation directions.  Otherwise, you can use `pip install` as usual.


PyPI
----

To install from pip

    pip install PAME

Since PAME requires many dependencies, this may upgrade numpy, scipy, ipython and other core scipy libraries.


Conda
-----
I use `anaconda` because it has an excellent virtual environment manager.  The advantage is here you can installed a clean working environment only for PAME without altering any of your other packages.  For a tutorial on conda virtual environments, `check this out <http://www.continuum.io/blog/conda>`_.  To configure a PAME environment in anaconda, first install anaconda and then do the following:


1. Create a clean virtual environment (mine is named PAMEvenv)

     conda create -n PAMEvenv anaconda

This installs several required scientific packages including `numpy`, `pandas` and `ipython`.

2. Activate the environment

     source activate PAMEvenv

3. Install pame (download pame source code and unzip, then navigate into directory)

     cd /path/to/PAMEdirectory
     python setup.py install

4. Conda install/upgrade dependencies

     conda install traits traitsui mayavi chaco mpmath PIL

To deactivate the virtual environment

     source deactivate

Dependencies
------------

The full list of PAME's dependencies is in the `requirements.txt <https://github.com/hugadams/PAME/blob/master/requirements.txt>`_ file.  





Support
=======

Questions?  Interested in developing?  Message: pame_env@googlegroups.com, or contact me directly (hughesadam87@gmail.com, @hughesadam87)



Web Utilitiles
==============

PAME doesn't run in the browser.  Check out these related tools that do!

 - `Mie-coefficients <http://nordlander.rice.edu/miewidget>`_

 - `Film Metrics (Thin Film Solver) <https://www.filmetrics.com/reflectance-calculator>`_

 - `Mie with shells and other tools <http://nanocomposix.com/pages/tools>`_

License
=======

3-Clause Revised BSD_

   .. _BSD : https://github.com/hugadams/PAME/blob/master/LICENSE.txt

