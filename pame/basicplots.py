""" A set of plotting components for Fiber Reflectance, Dielectric material, scattering cross section.
They each have special get/set methods for communicating with simulations in gensim and other
getters and setter model components."""
from __future__ import division

from enable.api import Component, ComponentEditor
from traits.api import HasTraits, Instance, Array, Property, CArray, Str, Float, Tuple, Any, Dict, List, \
     Enum, Bool, cached_property, implements, DelegatesTo, on_trait_change, Button
from pame.utils import DynamicRange
from traitsui.api import Item, Group, View, Tabbed, Action, HGroup, InstanceEditor, \
     VGroup, ListStrEditor

# Chaco imports
from chaco.api import ArrayPlotData, Plot, PlotAxis, HPlotContainer, ToolbarPlot, Legend
from chaco.tools.api import *
from numpy import where
from interfaces import IView
from chaco.tools.api import RangeSelection, RangeSelectionOverlay
from scipy.integrate import simps  #Simpson integration

from pandas import DataFrame
import numpy as np

# Use matplotlib color maps because chaco's confuse me on lineplot
# http://stackoverflow.com/questions/15140072/how-to-map-number-to-color-using-matplotlibs-
import matplotlib as mpl
import matplotlib.cm as cm

# pame imports
import config
import globalparms
from main_parms import SHARED_SPECPARMS

def r3(x): return round(x, 3)

class PlotError(Exception):
    """ """

def empty_image():
    """ Returns empty image plot """
    from chaco.api import ImageData, GridDataSource, GridMapper, DataRange2D, ImagePlot
    image_source = ImageData.fromfile(config.IMG_NOCOMPLEX_PATH)
    
    w, h = image_source.get_width(), image_source.get_height()
    index = GridDataSource(np.arange(w), np.arange(h))
    index_mapper = GridMapper(range=DataRange2D(low=(0, 0),
    high=(w-1, h-1)))

    image_plot = ImagePlot(
    index=index,
    value=image_source,
    index_mapper=index_mapper,
    origin='top left'
    )
    
    return image_plot

def _plotdata_empty(data):
    """ Checks plotdata.arrays to see if 'x' is the only key where values are populated."""
    is_empty = True
    for k, v in data.arrays.items():
        if k != 'x':
            if len(v) > 0:
                is_empty = False
                break
    return is_empty

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
    """ Plot reflectance, transmission etc... from dielectric slab."""
    optic_model = Instance(HasTraits) # DielectricSlab object, must be initialized by calling fcn            
    optical_stack = Property()
    x_unit = Property()

    # Extended behavior to pivot wavelength and angles.  Fairly hacked in
    primary_axis = Enum('Angles', 'Wavelengths')    
    lam_samples = Instance(DynamicRange)
    ang_samples = Instance(DynamicRange)
    refresh = Button  
    
    # Plot category (R, kz, A etc...)
    choose = Enum(globalparms.header.keys())  # SHOULD DELEGATE OR HAVE ADAPTER     
    chosen_name = Property(Str, depends_on='choose')

    # Metatraits to change plot selection depending on data type (eg R vs. kz's)
    real_or_imag = Enum('real', 'imaginary')
    
    layer_list = List() #<-- layer0, layer1, layer 2, depends on optic_stack.ns or .ds
    chosen_layer = Enum(values='layer_list')
    _model_attr = Str  #<-- Retains actual model attribute corresponding to self.choose and chosen_layer
    _is_ndlayer = Bool(False) #Current attribute has a value in each layer of material...

    show_legend=Bool(False)
    average = Bool(False)  #Averaging style
    plot = Any #Plot, ToolbarPlot, ImagePlot
    data = Instance(ArrayPlotData,())

    traits_view = View( HGroup(
                             Item('refresh', label='REFRESH', show_label=False),                                                                   
                             Item('average'),
                             Item('show_legend', label='Legend'),                             
                             Item('choose', 
                                  label='Choose selected plot', 
                                  show_label=False, 
                                  style='simple'
                                  ),     
                             Item('chosen_layer',
                                  visible_when='_is_ndlayer==True',
                                  label='Layer'
                                  ),
                             Item('real_or_imag', 
                              #    visible_when='_nonzero_complex==True', 
                                  label='Component'
                                  ),                   
                             #Item('chosen_name', 
                                  #style='readonly',
                                  #label='Displaying'
                                  #)
                                ),
                        HGroup(Item('primary_axis', label='Axis'),
                               Item('lam_samples',
                                    label='Wavelength Sampling:',
                                    editor=InstanceEditor(),
                                    style='custom',
                                    visible_when='primary_axis=="Wavelengths"'),
                               Item('ang_samples',
                                    label='Angle Sampling:',
                                    editor=InstanceEditor(),
                                    style='custom',
                                    visible_when='primary_axis=="Angles"')                               
                             ),
                  Item('plot', 
                       show_label=False, 
                       editor=ComponentEditor()),

                  width=800, 
                  height=600,
                  resizable=True
                  )

    # Default sampling sliders.  Note that if lambdas actually changed,
    # there's no event listner to update the range on this.  Would need
    # something like "lambdas_changed"/"angles_changed"
    def _lam_samples_default(self):
        lammax = self.optic_model.lambdas.shape[0]/2
        return DynamicRange(low=1, high=int(lammax), value=1)
    
    def _ang_samples_default(self):
        angmax = self.optic_model.angles.shape[0]/2
        return DynamicRange(low=1, high=int(angmax), value=1)

    def _refresh_fired(self):
        self.optic_model.update_opticview()
        
    def _model_changed(self):
        """ Don't want users chnging Model: 1 View to a Model.  If Model
        changes, make a new view is the pattern enforced.
        """ 
        raise PlotError("PAME Model-View design patter prevents changing"
                        " the Model instace on a given IView.  Please make"
                        " a separate view.")

    def __model_attr_default(self):
        return self.choose

    def _get_chosen_name(self):
        """ Long name corresponding to selected plot attribute"""
        return globalparms.header[self.choose]
    
    def _get_optical_stack(self):
        """ If primary axis is wavelegnths, pivot"""
        out = self.optic_model.optical_stack
        if self.primary_axis == 'Wavelengths':
            out = out.swapaxes('items', 'major')
        return out
            
    def _get_x_unit(self):
        """ Return either Angles (rads) or current spectral unit """
        if self.primary_axis == 'Wavelengths':
            return 'Angles'
        return self.optic_model.specparms.working_x_unit   
    
    @on_trait_change('average, show_legend, real_or_imag, primary_axis,\
                      lam_samples.value, ang_samples.value')
    def _update_plot(self):
        """ Change which data (R, T, A...) to view.  These all trigger
        full redraw."""
        self.update()
                    
    @on_trait_change('choose, chosen_layer')
    def _update_modelattr_plot(self):
        """ User selects choose and layer, and this will update self._model_attr"""
        self._model_attr = self.infer_ndlayer(self.choose)              
        self.update()        
        
    def update(self):
        """Deviates from other plots in that these plots aren't meant to update in realtime
        via set-data, so it's easier to just wipe plotdata and redraws lines, basically as a
        static plot would work.  Therefore, I don't separate update_data() and create_plots()
        and so forth.  This method literally creates the plot from scratch.
        """
        # At this point, assumes that arrays have been redraw so overwrite data or just
    
        self.plot = ToolbarPlot(self.data) #Requires access to arrayplotdata
        ostack = self.optical_stack #So don't have to recall property over and over
        
        # Depending on primary_axis, set X to lambdas Y to Angles or vice/ver
        # For x, resample wavelengths and choose current unit system via request()
        primary_x = self.optic_model.specparms.working_lambdas[::self.lam_samples.value]
        primary_y = self.optic_model.angles[::self.ang_samples.value]
        colormap = config.LINECMAP
        
        if self.primary_axis == 'Wavelengths':
            colormap = config.LINECMAP_LAMBDA
            primary_x, primary_y = primary_y, primary_x

        self.data.arrays={} #Clear DATA!!!
        self.data.set_data('x', primary_x)
        linenames = [] #<-- To put into legend in sorted order     
                            
        # If angle averaging, can be many styles.  If wavelength, just call mean
        if self.average:
            if self.primary_axis == 'Angles':
                # Why can't I just use panel.minor_xs().slice()?
                avg_array = self.optic_model.compute_average(self._model_attr).astype(complex)
            else:
                avg_array = ostack.minor_xs(self._model_attr).mean(axis=1).values.astype(complex)
            yout = self.infer_complex(avg_array)
          
            self.data.set_data('y', yout) 
            plot_line_points(self.plot, ("x", "y"), 
                             name='%s Avg.' % (self._model_attr),
                             style='both',
                             line_width=4)  #<--- Thick line

        # Plot angle dependence, bruteforce colromap
        else:
            # http://stackoverflow.com/questions/15140072/how-to-map-number-to-color-using-matplotlibs-colormap
            # http://stackoverflow.com/questions/27908032/custom-labels-in-chaco-legend/27950555#27950555            
            amin = primary_y[0]
            amax = primary_y[-1]
            if amin > amax:  #If counting backwards angles like in transmission
                amax, amin = amin, amax

            norm = mpl.colors.Normalize(vmin=amin, vmax=amax)
            cmapper = cm.ScalarMappable(norm=norm, cmap=colormap ).to_rgba  #THIS IS A FUNCTION
    
            # yval is angle or wavelength
            for idx, yval in enumerate(primary_y):
                linecolor = cmapper(yval)    
                linename = '%.2f' % yval
                linenames.append(linename)

                array = ostack[yval][self._model_attr].astype(complex)
                yout = self.infer_complex(array)
                                
                self.data.set_data(linename, yout)                    
                plot_line_points(self.plot, 
                                 ("x", linename), 
                                 name = linename, 
                                 color = linecolor,
                                 style = 'line'   #<-- Don't plot marker
                                 )
  
        # XXX --- At this point intercept self.data.arrays, and if 'x' is
        # only one with any data, then all lines are missing and could break out and set
        # to an image plot that says NO DATA or soemthing
        # https://media.readthedocs.org/pdf/chaco/latest/chaco.pdf
        if _plotdata_empty(self.data):
            self.plot = empty_image()
            return

        # Update plot title, legend, tools, labels
        # ----------------------------------------
        #self.plot.title = '%s' % self.chosen_name
        self.plot.padding = 50
                
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
                        
            self.plot.legend.labels = linenames
            self.plot.legend.visible = True
            self.plot.legend.bgcolor = (.8,.8,.8) #lightgray
            self.plot.legend.border_visible = True
            self.plot.legend.resizable = 'hv' #<--- doesn't work
        
        # Attach some tools to the plot
        #http://docs.enthought.com/chaco/api/tools.html
        self.plot.tools.append(PanTool(self.plot))
        self.plot.tools.append(LineInspector(self.plot))
        zoom = BetterSelectingZoom(component=self.plot,
                                   tool_mode="box", 
                                   always_on=False)
        self.plot.overlays.append(zoom)
        
    def infer_ndlayer(self, attr_name):
        """ Given selected attribute like kz, looks at opticalstack and
        if it finds kz_L1, kz_L2, kz_L3 etc.., it means that kz has a value
        in every layer of the dielectric so plot must display as such.  An
        attribute like "R" denotes the reflectance at the first interface, so
        this would be disabled.  
        
        If ndlayer, returns kz_L1 (ie first layer) modified attribute name.
        If not, returns attr_name unchanged!
        """
        
        # If attribute is flat/does not have value in each layer of slab
        if attr_name in self.optical_stack.minor_axis:
            self._is_ndlayer = False
            return attr_name

        #http://stackoverflow.com/questions/28031354/match-the-pattern-at-the-end-of-a-string#28031451
        # Split on _globalparms._flat_suffix        
        delim = '_%s' % globalparms._flat_suffix
        layered_keys = set(i.split(delim)[0] for i in self.optical_stack.minor_axis if delim in i)
        # layered keys are keys in minor axis that correspond to quantites
        # that exists for each layer.  So like kv_L1, vn_L1, ... this returns
        # [kv, vn].  Then I can see if selected attr in this list

        if attr_name in layered_keys:              
            self._is_ndlayer = True
            self.layer_list = ['Layer %s' % i for i in range(len(self.optic_model.ns))] #Use layer names instead?
            return attr_name + delim + str(self.layer_list.index(self.chosen_layer)) #kz_L1 etc...

        else:
            raise PlotError('Selected plot attribute "%s" is not in optical_stack,'
                ' nor can it be inferred as a multi-layer attribute based on splitting'
                ' of delimiter "%s", which results in %s.' %
                (attr_name, globalparms._flat_suffix, layered_keys))              

    
    def infer_complex(self, carray):
        """ From an array to be plotted, inspects if it has a real AND imaginary component.
        Set _nonzero_complex variable and handles logic of self.real_or_imag.  If imaginary
        component is 0, we don't want the plot to let users select the imaginary channel.
        """            
        #http://docs.scipy.org/doc/numpy/reference/generated/numpy.iscomplex.html        
        if np.sum(carray.imag > config.ABOUTZERO):  #<--- if all imaginary components are 0
            _nonzero_complex = True
            
        else:
            _nonzero_complex = False                
        # Return real or imaginary component of array
        if self.real_or_imag == 'real':
            return carray.real
        else:
            # User selects imaginary, but its equal to 0, don't return lines
            if _nonzero_complex == False:
                return []
            else:
                return carray.imag
        


# MVIEW SHOULD HAVE A SECOND TYPE OF DIFFERENT Y-AXIS IE
# https://github.com/enthought/chaco/blob/master/examples/demo/multiaxis.py
class ABCView(HasTraits):
    """ Interface for plots that are associated with a PameObject, either a
    Material or Mie insance,  (stored in attr "model"), that updates in
    real time when arrays on that object change (eg index of refraction array).  
    
    Notes
    -----
    Older implementaions kept view and model separate, and it was up to
    model when to trigger view updates, but this implementation has less
    boilerplate, and it's useful for plots to inspect their model objects
    because metadata makes plots more flexible.  
    """
 
    implements(IView) #Superfulous at this point, but PlotSelectors looks for
    
    model = Instance(HasTraits) #<-- Material object, must be initialized with

    # Can't delegate specparms to model, or lambdas would be delegate of delegate, fails
    specparms = Instance(HasTraits, SHARED_SPECPARMS) 
    working_lambdas = DelegatesTo('specparms')
    data = Instance(ArrayPlotData)
    
    def __init__(self, *args, **kwargs):
        """Create plots (requires _data_default), then all listeners
        should just hook up.
        """
        super(ABCView, self).__init__(*args, **kwargs)
        self.update_data()
        self.create_plots()
               
    def _data_default(self):
        """ Default plotdata with "x" and then never have to recreate."""
        data = ArrayPlotData()#dict(x=self.lambdas, er=[], ei=[], nr=[], ni=[]))    
        data.set_data('x', self.working_lambdas )
        return data        
        
    def _working_lambdas_changed(self):
        self.data.set_data('x', self.working_lambdas)
        self.create_plots() #Redraw to change xaxis label
    
    def add_tools_title(self, plot, title_keyword):
        """Used to add same tools to multiple plots"""
        plot.title = title_keyword
        plot.legend.visible = True

        bottom_axis = PlotAxis(plot, orientation='bottom',
                               title=self.specparms.working_x_unit, 
                         #      label_color='red', 
                         #      label_font='Arial', 
                         #      tick_color='green',
                               tick_weight=1)

        # CUSTOM YLABEL, why bother?
#        vertical_axis = PlotAxis(plot, orientation='left',
#                                 title='Relative'+str(title_keyword))

#        plot.underlays.append(vertical_axis)
        plot.underlays.append(bottom_axis)

        # Attach some tools to the plot
        plot.tools.append(PanTool(plot))
        zoom = ZoomTool(component=plot, tool_mode="box", always_on=False)
        plot.overlays.append(zoom)    

    def create_plots(self):
        """ Creates toolbar plot(s); draws lines initially. """
        
    def update_data(self):
        """ Update plot data only."""


class MaterialView(ABCView):
    """ Plots index of refraction and dielectric function of a material in real
    time, by listening to delegated traits.

    Important: Chose not to have direct update listeners from model.earray.
    Materials still need to physically do "update()" (called mview()),
    but now plots have access to Material for metdata attributes.
    
    """

    eplot = Instance(Plot)
    nplot = Instance(Plot)  
    
    earray = DelegatesTo('model')
    narray = DelegatesTo('model')

    ToggleReal=Action(name="Toggle Real", action="togimag")
    ToggleImag=Action(name="Toggle Imaginary", action="togreal")
    
    interpolation = DelegatesTo('model')
    extrapolation = DelegatesTo('model')

    # Custom plot_title disallowed

    view = View(
        VGroup(
            HGroup(
                Item('interpolation', label='Interpolation', 
                    visible_when='interpolation is not None'),
                Item('extrapolation', label='Extrapolate',
                    visible_when='interpolation is not None')
                ),        
        Tabbed(
            Item('eplot', editor=ComponentEditor(), dock='tab', label='Permittivity'),
            Item('nplot', editor=ComponentEditor(), dock='tab', label='Index'), 
            show_labels=False         #Side label not tab label
            ),
         ),
        width=800, height=600,  buttons=['Undo'],             
        resizable=True
        )
        
    def _earray_changed(self):
        self.update_data()
        
    def create_plots(self):
        self.eplot = ToolbarPlot(self.data)
        self.nplot = ToolbarPlot(self.data)
        
        # Name required or will appear twice in legend!
        plot_line_points(self.eplot, ('x','er'), color='orange', name='e1')
        plot_line_points(self.eplot, ('x','ei'), color='green', name='ie2')
        plot_line_points(self.nplot, ('x','nr'), color='orange', name='n')
        plot_line_points(self.nplot, ('x','ni'), color='green', name='ik')         

        self.add_tools_title(self.eplot, 'Dielectric Function vs. Wavelength')
        self.add_tools_title(self.nplot, 'Index of Refraction vs. Wavelength ')

    def update_data(self):    
        """Method to update plots; draws them if they don't exist; otherwise 
        simply updates the data
        """     
        self.data.set_data('er', self.earray.real)
        self.data.set_data('nr', self.narray.real) 
        self.data.set_data('ei', self.earray.imag)
        self.data.set_data('ni', self.narray.imag)


class ScatterView(ABCView):
    """Used to view scattering cross sections and other relevant parameters from mie scattering program"""

    implements(IView)

    sigplot = Instance(Plot)        

    #Scattering, extinction, absorption
    Cext = DelegatesTo('model')    
    Cscatt = DelegatesTo('model')   
    Cabs = DelegatesTo('model')   
    
    # Useful to have callers change, for example FullMie vs. Composite
    plot_title = Str('Scattering Spectrum')

    # No listeners to Cext, Cscatt, Cabs, as it's easier to implement 
    # sview.update_data() from Mie, just have to remember that update_cross()
    # must call it after every update.

    # Plot area, max, min showed on view
    exmax = Tuple(Float,Float)     #Technically properties but don't update with view for some reason
    absmax = Tuple(Float,Float)    #Pukes if 0,0 default not provided, but this is probably due to my program not tuple trait
    scatmax = Tuple(Float,Float)
    exarea = Float         #Store the area under the curve for now, although this should be gotten in curve analysis data
    absarea = Float
    scatarea = Float 

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
        x = self.working_lambdas[index]
        return r3(x), r3(value)

    def compute_area(self, array):
        """ Get the area under a curve.  If I want to change integration style, 
        should just make the integration style an Enum variable and redo this 
        on a trait change"""
        return r3(simps(array, self.working_lambdas, even='last'))

    def create_plots(self):
        self.sigplot = ToolbarPlot(self.data)
        
        # Don't change names, used by DoubleSView!
        plot_line_points(self.sigplot, ('x','Scattering'), color='green', name='Scattering')
        plot_line_points(self.sigplot, ('x','Absorbance'), color='blue', name='Absorbance')
        plot_line_points(self.sigplot, ('x','Extinction'), color='red', name='Extinction')

        self.add_tools_title(self.sigplot, self.plot_title)

    def _plot_title_changed(self):
        self.sigplot.title = self.plot_title

    def update_data(self):
        #Don't alter these keys 'x', 'sig' etc... as they are called in the composit_plot Double Sview object
        self.data.set_data('Scattering', self.Cscatt)
        self.data.set_data('Absorbance', self.Cabs) 
        self.data.set_data('Extinction', self.Cext)
        
        self.exarea = self.compute_area(self.Cext)
        self.absarea = self.compute_area(self.Cabs)
        self.scatarea = self.compute_area(self.Cscatt)
        
        try:
            self.exmax=self.compute_max_xy(self.Cext)
            self.absmax=self.compute_max_xy(self.Cabs)
            self.scatmax=self.compute_max_xy(self.Cscatt)

        except TypeError:  #Sometimes these inexplicably mess up, especially when loading in strange materials
            print 'Cannot find max xy values in ext,abs,scattering cross sections'
            pass        


        
if __name__ == '__main__':
    from pame.material_models import Sellmeir
    Sellmeir().configure_traits()