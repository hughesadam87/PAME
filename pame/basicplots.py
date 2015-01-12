''' A set of plotting components for Fiber Reflectance, Dielectric material, scattering cross section.
They each have special get/set methods for communicating with simulations in gensim and other
getters and setter model components.'''

from enable.api import Component, ComponentEditor
from traits.api import HasTraits, Instance, Array, Property, CArray, Str, Float, Tuple, Any, Dict, List, \
     Enum, Bool, cached_property, implements, DelegatesTo, on_trait_change
from traitsui.api import Item, Group, View, Tabbed, Action, HGroup, InstanceEditor, VGroup, ListStrEditor

# Chaco imports
from chaco.api import ArrayPlotData, Plot, AbstractPlotData, PlotAxis, HPlotContainer, ToolbarPlot, Legend
from chaco.tools.api import *
from numpy import where
from interfaces import IView
from chaco.tools.api import RangeSelection, RangeSelectionOverlay
from scipy.integrate import simps  #Simpson integration

from pandas import DataFrame
import numpy as np

# Use matplotlib color maps because chaco's confuse me on lineplot
# http://stackoverflow.com/questions/15140072/how-to-map-number-to-color-using-matplotlibs-colormap
import matplotlib as mpl
import matplotlib.cm as cm

# pame imports
import config
import globalparms

class PlotError(Exception):
    """ """

def plot_line_points(*args, **kwargs):
    """ plots a line and/or markers.  Colors/styles default to config.  
    First positional arg must be a Plot object, remaining args,kwargs passing
    into Plot.plot().  
    
    kwargs
    ------
    
    style: both, line or scatter
        Plot lines, markers or both
    """
    args = list(args)
    plotobj = args[0]
    if not isinstance(plotobj, Plot):
        raise PlotError('Expected Plot type as first arg, got %s' % plotobj)
    del args[0]

    style = kwargs.pop('style', 'both').lower()
    
    if style in ['both', 'line']:
        kwargs['type'] ='line'        
        kwargs.setdefault('color' ,config.LINECOLOR)
        kwargs.setdefault('line_width', config.LINEWIDTH) #Note undersocre in line_width kwarg
        plotobj.plot( *args, **kwargs)
        kwargs.pop('line_width')

    if style in ['both', 'scatter']:
        kwargs['type'] ='scatter'
        kwargs.setdefault('marker_size', config.MARKERSIZE)    
        plotobj.plot( *args, **kwargs)


class OpticalView(HasTraits):
    optic_model = Any # DielectricSlab object, must be initialized with this by calling fcn    
    optic_stack = DelegatesTo('optic_model')
    lambdas = DelegatesTo('optic_model')  #Xarray everywhere will need replaced
    angles = DelegatesTo('optic_model')
    x_unit = DelegatesTo('optic_model')

    real_or_imag = Enum('real', 'imaginary')
    _is_complex = Bool(False)
    show_legend=Bool(False)
    average = Bool(False)  #Averaging style
    plot = Instance(Plot)
    
    # CHANGE TO HEADER
    choose = Enum(globalparms.header.keys())  # SHOULD DELEGATE OR HAVE ADAPTER     
    chosen_name = Property(Str, depends_on='choose')
    
    data = Instance(ArrayPlotData,())

    traits_view = View( HGroup(
                             Item('average'),
                             Item('choose', 
                                  label='Choose selected plot', 
                                  show_label=False, 
                                  style='simple'
                                  ),
                             Item('real_or_imag', 
                                  visible_when='_is_complex==True', 
                                  label='Component'
                                  ),          
                             Item('show_legend', label='Legend'),
                             #Item('chosen_name', 
                                  #style='readonly',
                                  #label='Displaying'
                                  #)
                             ),
                  Item('plot', 
                       show_label=False, 
                       editor=ComponentEditor()),

                  width=800, 
                  height=600,
                  resizable=True
                  )

    def _get_chosen_name(self):
        """ Long name corresponding to selected plot attribute"""
        return globalparms.header[self.choose]
    
    @on_trait_change('choose, average, real_or_imag, show_legend')
    def _update_shiz(self):
        """ Change which data (R, T, A...) to view.  These all trigger
        full redraw."""
        self.update()
        
    def update(self):
        """Deviates from other plots in that these plots aren't meant to update in realtime
        via set-data, so it's easier to just wipe plotdata and redraws lines, basically as a
        static plot would work.  Therefore, I don't separate update_data() and create_plots()
        and so forth.  This method literally creates the plot from scratch.
        """
        # At this point, assumes that arrays have been redraw so overwrite data or just
    
        self.plot = ToolbarPlot(self.data) #Requires access to arrayplotdata

        self.data.arrays={} #Clear DATA!!!
        self.data.set_data('x', self.lambdas)
        
        # FROM HERE DOWN, ASSUMES SINGLE LAYER LIKE R
        if self.average:
            avg_array = self.optic_model.compute_average(self.choose).astype(complex)
            yout = self.infer_complex(avg_array)
          
            self.data.set_data('y', yout) 
            plot_line_points(self.plot, ("x", "y"), 
                             name='%s Avg.' % (self.choose),
                             style='both',
                             line_width=4)  #<--- Thick line

        # Plot angle dependence, bruteforce colromap
        else:
            # http://stackoverflow.com/questions/15140072/how-to-map-number-to-color-using-matplotlibs-colormap
            norm = mpl.colors.Normalize(vmin=self.angles[0], vmax=self.angles[-1])
            cmapper = cm.ScalarMappable(norm=norm, cmap=config.LINECMAP ).to_rgba  #THIS IS A FUNCTION
    
            for idx, angle in enumerate(self.angles):
                linecolor = cmapper(angle)    
                linename = str(round(angle,2))

                array = self.optic_model.optical_stack[angle][self.choose].astype(complex)
                yout = self.infer_complex(array)
                                
                self.data.set_data(linename, yout)                    
                plot_line_points(self.plot, 
                                 ("x", linename), 
                                 name = linename, 
                                 color = linecolor,
                                 style = 'line'   #<-- Don't plot marker
                                 )
  
        # Update plot title, legend, tools, labels
        # ----------------------------------------
        #self.plot.title = '%s' % self.chosen_name
        #self.plot.padding = 50
        
        x_axis = PlotAxis(orientation='bottom', #top, bottom, left, righ
                  title=self.x_unit,
                  mapper=self.plot.x_mapper,
                  component=self.plot)       
        
        
        ylabel = '%s' % self.chosen_name
        if self.real_or_imag == 'imaginary':
            ylabel = ylabel + ' (imaginary)'
            
        y_axis = PlotAxis(orientation='left',
                  title=ylabel,
                  mapper=self.plot.y_mapper,
                  component=self.plot)   
        
        self.plot.underlays.append(y_axis)                
        self.plot.underlays.append(x_axis)        
        
        
        # Legend settings
        # http://code.enthought.com/projects/files/ETS3_API/enthought.chaco.legend.Legend.html
        # LEGEND EXAMPLES MISSING FOR CUSTOM OVERLAY
        # http://docs.enthought.com/chaco/user_manual/basic_elements/overlays.html
        if self.show_legend:
                        
#            self.plot.legend.labels = list([i for i in self.angles]) #Sort numerically, not alphabetically
            self.plot.legend.visible = True
            self.plot.legend.bgcolor = (.8,.8,.8) #lightgray
            self.plot.legend.border_visible = True
            self.plot.legend.resizable = 'hv' #<--- doesn't work
        
        ## Attach some tools to the plot
        self.plot.tools.append(PanTool(self.plot))
        zoom = BetterSelectingZoom(component=self.plot, tool_mode="box", always_on=False)
        self.plot.overlays.append(zoom)
    
    
    def infer_complex(self, carray):
        """ From an array to be plotted, inspects if it has a real AND imaginary component.
        Set _is_complex variable and handles logic of self.real_or_imag.  If imaginary
        component is 0, we don't want the plot to let users select the imaginary channel.
        """
        #http://docs.scipy.org/doc/numpy/reference/generated/numpy.iscomplex.html        
        if np.sum(np.iscomplex(carray)):  #<--- if all imaginary components are 0
            self._is_complex = True
            
        else:
            self._is_complex = False
            self.real_or_imag = 'real'  #Necessary for view logic completion
            
        # Choose real or complex channel
        if self.real_or_imag == 'real':
            return carray.real
        else:
            return carray.imag
        


class MaterialView(HasTraits):

    implements(IView)

    eplot = Instance(Plot)
    nplot = Instance(Plot)             #Traits are populated on update usually

    data = Instance(AbstractPlotData)

    xarray=Array()
    earray=CArray()
    narray=CArray()
    xunit=Str()
    ereal=Property(Array,depends_on=["earray"])     #Storing as traits just in case I want to have the array view     
    eimag=Property(Array,depends_on=["earray"])
    nreal=Property(Array,depends_on=["narray"])
    nimag=Property(Array,depends_on=["narray"])

    ToggleReal=Action(name="Toggle Real", action="togimag")
    ToggleImag=Action(name="Toggle Imaginary", action="togreal")

    view = View(
        Tabbed(
            Item('eplot', editor=ComponentEditor(), dock='tab', label='Dielectric'),
            Item('nplot', editor=ComponentEditor(), dock='tab', label='Index'), 
            show_labels=False         #Side label not tab label
            ),
        width=800, height=600,  buttons=['Undo'],             #Buttons work but only respond to trait changes not plot changes like zoom and stuff
        resizable=True
    )


    def _get_ereal(self):
        return self.earray.real
    
    def _get_eimag(self): 
        return self.earray.imag

    def _get_nreal(self): 
        return self.narray.real

    def _get_nimag(self): 
        return self.narray.imag

    def create_plots(self):
        self.eplot = ToolbarPlot(self.data)
        self.nplot= ToolbarPlot(self.data)

        plot_line_points(self.eplot, ('x','er'), color='orange', name='ereal')
        plot_line_points(self.eplot, ('x','ei'), color='green', name='eimag')
        plot_line_points(self.nplot, ('x','nr'), color='orange', name='nreal')
        plot_line_points(self.nplot, ('x','ni'), color='green', name='nimag')

        self.add_tools_title(self.eplot, 'Dielectric ')
        self.add_tools_title(self.nplot, 'Index of Refraction ')

    def add_tools_title(self, plot, title_keyword):
        '''Used to add same tools to multiple plots'''
        plot.title = title_keyword + 'vs. Wavelength'
        plot.legend.visible = True

        bottom_axis = PlotAxis(plot, orientation='bottom',
                               title=self.xunit, 
                               label_color='red', 
                               label_font='Arial', 
                               tick_color='green',
                               tick_weight=1)
        vertical_axis = PlotAxis(plot, orientation='left',
                                 title='Relative'+str(title_keyword))

        plot.underlays.append(vertical_axis)
        plot.underlays.append(bottom_axis)

        # Attach some tools to the plot
        plot.tools.append(PanTool(plot))
        zoom = ZoomTool(component=plot, tool_mode="box", always_on=False)
        plot.overlays.append(zoom)


    def togimag(self):      #NOT SURE HOW TO QUITE DO THIS
        print 'togimag not supported!!'

    def togreal(self):
        print 'togimag not supported!!'

    def update(self, xarray, earray, narray, xunit):    
        '''Method to update plots; draws them if they don't exist; otherwise it simply updates the data'''     
        self.xunit=xunit 
        self.xarray=xarray
        self.earray=earray
        self.narray=narray
        
        if self.data == None:
            self.data = ArrayPlotData(x=self.xarray, er=self.ereal, nr=self.nreal, ei=self.eimag, ni=self.nimag)
            self.create_plots()
        else:
            self.update_data()

    def update_data(self):
        self.data.set_data('x',self.xarray) 
        self.data.set_data('er', self.ereal)
        self.data.set_data('nr', self.nreal) 
        self.data.set_data('ei', self.eimag)
        self.data.set_data('ni', self.nimag)
        self.eplot.request_redraw() ; self.nplot.request_redraw()

    ####### USED FOR SIMULATION STORAGE MOSTLY #####

    def get_sexy_data(self):
        '''Returns the data in a list that can be immediately read back in another instance of opticview.  
        Note this is not the same as the arrayplotdata getdata() function'''
        return [self.xarray, self.ereal, self.nreal, self.eimag, self.nimag]

    def set_sexy_data(self, data_list):
        '''Takes in data formatted deliberately from "get_sexy_data" and forces an update'''
        self.update(data_list[0], data_list[1], data_list[2], data_list[3])

    # Migrate to model!!
    def get_dataframe(self):
        ''' Returns dataframe of data for easier concatenation into a runpanel dataframe used by
        simulations'''
        d = {'er' : self.ereal, 
             'nr':self.nreal,
             'ei':self.eimag,
             'ni':self.nimag}   
        return DataFrame(d, index=self.xarray)

class ScatterView(HasTraits):
    '''Used to view scattering cross sections and other relevant parameters from mie scattering program'''

    implements(IView)

    sigplot = Instance(Plot)        #Scattering cross section
    data = Instance(AbstractPlotData)

    xarray=Array()
    xunit=Str()

    extarray=Array()    #Scattering, extinction, absorption
    scatarray=Array()
    absarray=Array()

    exmax=Tuple(Float,Float)     #Technically properties but don't update with view for some reason
    absmax=Tuple(Float,Float)    #Pukes if 0,0 default not provided, but this is probably due to my program not tuple trait
    scatmax=Tuple(Float,Float)
    exarea=Float         #Store the area under the curve for now, although this should be gotten in curve analysis data
    absarea=Float
    scatarea=Float 

    view = View(
        Item('sigplot', editor=ComponentEditor(), dock='tab', label='Cross Section', show_label=False),
        HGroup(
            Item('exmax', style='readonly', label='Extinction Max'),
            Item('absmax', style='readonly', label='Absorbance Max'),
            Item('scatmax', style='readonly', label='Scattering Max'),
            ),
        HGroup(
            Item('exarea', style='readonly', label='Extinction Area'),
            Item('absarea', style='readonly', label='Absorbance Area'),
            Item('scatarea', style='readonly', label='Scattering Area'),
            ),
        width=800, height=600,
        resizable=True
    )

    def compute_max_xy(self, array):
        rounding = 3  #Change for rounding of these 
        value = max(array)
        index = int(where(array==value)[0])  #'where' returns tuple since is can be used on n-dim arrays
        x = self.xarray[index]
        return (round(x,rounding), round(value,rounding))

    def compute_area(self, array):
        ''' Get the area under a curve.  If I want to change integration style, should just make the integration 
            style an Enum variable and redo this on a trait change'''
        rounding=0
        return round(simps(array, self.xarray, even='last'), rounding)

    def create_plots(self):
        self.sigplot = ToolbarPlot(self.data)
        self.sigplot.plot(("x", "Scattering"), name="Scattering", color="green", linewidth=4)
        self.sigplot.plot(("x", "Scattering"), name="Scattering", color="green", type='scatter', marker_size=2)

        self.sigplot.plot(("x", "Absorbance"), name="Absorbance", color="blue", linewidth=4)
        self.sigplot.plot(("x", "Absorbance"), name="Absorbance", color="blue", type='scatter', marker_size=2)

        self.sigplot.plot(("x", "Extinction"), name="Extinction", color="red", linewidth=4)
        self.sigplot.plot(("x", "Extinction"), name="Extinction", color="red", type='scatter', marker_size=2)

        self.add_tools_title(self.sigplot, 'Scattering Spectrum')

    def add_tools_title(self, plot, title_keyword):
        '''Used to add same tools to multiple plots'''
        plot.title = title_keyword + 'vs. Wavelength'
        plot.legend.visible = True

        bottom_axis = PlotAxis(plot, orientation='bottom', 
                               title=self.xunit, 
                               label_color='red',
                               label_font='Arial', 
                               tick_color='green', tick_weight=1)

        vertical_axis = PlotAxis(plot, orientation='left',
                                 title=str(title_keyword))

        plot.underlays.append(vertical_axis)
        plot.underlays.append(bottom_axis)

        # Attach some tools to the plot
        plot.tools.append(PanTool(plot))
        zoom = ZoomTool(component=plot, tool_mode="box", always_on=False)
        plot.overlays.append(zoom)

    def update(self, xarray, extarray, scatarray, absarray, xunit):         
        self.xunit=xunit 
        self.xarray=xarray
        self.extarray=extarray 
        self.absarray=absarray 
        self.scatarray=scatarray

        if self.data == None:
            self.data = ArrayPlotData(x=self.xarray, 
                                      Scattering=self.scatarray, 
                                      Absorbance=self.absarray , 
                                      Extinction=self.extarray)
            self.create_plots()
        else:
            self.update_data()
            self.exarea=self.compute_area(self.extarray)
            self.absarea=self.compute_area(self.absarray)
            self.scatarea=self.compute_area(self.scatarray)
            try:
                self.exmax=self.compute_max_xy(self.extarray)
                self.absmax=self.compute_max_xy(self.absarray)
                self.scatmax=self.compute_max_xy(self.scatarray)

            except TypeError:  #Sometimes these inexplicably mess up, especially when loading in strange materials
                print 'Had to pass in finding max_xy values'
                pass


    def update_data(self):
        ### Don't alter these keys 'x', 'sig' etc... as they are called in the composit_plot Double Sview object
        self.data.set_data('x', self.xarray) ; self.data.set_data('Scattering', self.scatarray)
        self.data.set_data('Absorbance', self.absarray) ; self.data.set_data('Extinction', self.extarray)
        self.sigplot.request_redraw()

    def get_sexy_data(self):
        '''Returns the data in a list that can be immediately read back in another instance of opticview.  Note this is not the same as the arrayplotdata getdata() function'''
        return [self.xarray, self.scatarray, self.absarray, self.extarray]

    def set_sexy_data(self, data_list):
        '''Takes in data formatted deliberately from "get_sexy_data" and forces an update'''
        self.update(data_list[0], data_list[1], data_list[2], data_list[3])

    def get_dataframe(self):
        ''' Returns dataframe of data for easier concatenation into a runpanel dataframe used by
        simulations'''
        d = {'ext' : self.extarray, 'scatt':self.scatarray, 'abs':self.absarray}   
        return DataFrame(d, index=self.xarray)