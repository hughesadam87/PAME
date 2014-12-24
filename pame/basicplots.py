''' A set of plotting components for Fiber Reflectance, Dielectric material, scattering cross section.
They each have special get/set methods for communicating with simulations in gensim and other
getters and setter model components.'''

from enable.api import Component, ComponentEditor
from traits.api import HasTraits, Instance, Array, Property, CArray, Str, Float, Tuple, Any, Dict, List, Enum, Bool, cached_property, implements
from traitsui.api import Item, Group, View, Tabbed, Action, HGroup, InstanceEditor, VGroup, ListStrEditor

# Chaco imports
from chaco.api import ArrayPlotData, Plot, AbstractPlotData, PlotAxis, HPlotContainer, ToolbarPlot
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

# pame config
import config

class OpticalView(HasTraits):
    """ Multiple lineplots for optics in Stack for attributes like Reflectance, Tramission etc...
    
    Reflectance data is already stored as a panel, but to be consistent with simulation and legacy
    design, uses numpy arrays.  (IView)
    
    Uses update methods rather than delegating to StackData so it can be used independtly, although
    such an interface is probably never going to be used.  If it ends up simplifying things to just
    let the data in here have access to the opticstack panel from sim_traits, just do that.
    """
    implements(IView)

    name=Str('Test') #??

    Refplot = Instance(Plot)
    Transplot = Instance(Plot)             #Traits are populated on update usually
    Avgplot= Instance(Plot)

    chooseplot=Enum('Reflectance', 'Transmittance', 'Averaged Reflectance')   #For second view
    selected=Property(depends_on='chooseplot')

    data = Instance(ArrayPlotData)

    xarray=Array() #Wavelengths
    angles=Array()
        
    RefArray=Array()
    TransArray=Array()
    Reflectance_AVG=Array()

    # Radio button View
    traits_view = View( Item('chooseplot', 
                             label='Choose selected plot', 
                             show_label=False, 
                             style='custom'),
                  Item('selected', show_label=False, editor=ComponentEditor()),
                  width=800, height=600, resizable=True   )

    # Tabs
    #tabbed_view = View(
        #Tabbed(
            #Item('Refplot', editor=ComponentEditor(), dock='tab', label='Reflectance'),
            #Item('Transplot', editor=ComponentEditor(), dock='tab', label='Transmittance'), 
            #Item('Avgplot', editor=ComponentEditor(), dock='tab', label='Theta averaged'),		
            #show_labels=False         #Side label not tab label
            #),
        #width=800, height=600,
        #resizable=True
    #)


    def _get_selected(self): 
        if self.chooseplot == 'Reflectance': 
            return self.Refplot
        elif self.chooseplot == 'Transmittance': 
            return self.Transplot
        elif self.chooseplot == 'Averaged Reflectance': 
            return self.Avgplot

    def create_plots(self):
        """ Creates several toolbar plots"""
        self.Refplot = ToolbarPlot(self.data) #Requires access to arrayplotdata
        self.Transplot= ToolbarPlot(self.data)
        self.Avgplot= ToolbarPlot(self.data)

        print self.RefArray.shape, 'in create plot', self.Refplot

        # http://stackoverflow.com/questions/15140072/how-to-map-number-to-color-using-matplotlibs-colormap
        norm = mpl.colors.Normalize(vmin=self.angles[0], vmax=self.angles[-1])
        cmapper = cm.ScalarMappable(norm=norm, cmap=config.LINECMAP ).to_rgba #THIS IS A FUNCTION

        for i, angle in enumerate(self.angles):
            
            linecolor = cmapper(angle)

#            print self.RefArray[i,:], self.RefArray[i,:].shape, type(self.RefArray[i,:]), np.isnan(np.sum(self.RefArray[i,:]))
            self.data.set_data(('RTheta' + str(i)), self.RefArray[i,:])
            
#            plt.plot(self.xarray, self.RefArray[i,:])

            self.Refplot.plot( ("x", ('RTheta' + str(i))), 
                               name=('%.2f'% angle ),
                               color=linecolor)

            self.data.set_data(('TTheta' + str(i)), self.TransArray[i,:])
            self.Transplot.plot( ("x", ('TTheta' + str(i))), 
                                 name=('%.2f' % angle),
                                 color=linecolor)

        self.Avgplot.plot( ("x", 'Avg'), name='Averaged Angles', color='red' )

        self.add_tools_title(self.Refplot, 'Reflectance')
        self.add_tools_title(self.Transplot, 'Transmittance')
        self.add_tools_title(self.Avgplot, 'Averaged Reflectance')
    

    def add_tools_title(self, plot, title):
        '''Used to add same tools to multiple plots'''
        plot.title = title
        plot.padding = 50
        
        # Legend settings
        # http://code.enthought.com/projects/files/ETS3_API/enthought.chaco.legend.Legend.html
        plot.legend.labels = list([i for i in self.angles]) #Sort numerically, not alphabetically
        plot.legend.visible = True
        plot.legend.bgcolor = (.5,.5,.5) #gray
        plot.legend.border_visible = True
        plot.legend.resizable = 'hv'

        
        # Attach some tools to the plot
        plot.tools.append(PanTool(plot))
        zoom = BetterSelectingZoom(component=plot, tool_mode="box", always_on=False)
#		plot.overlays.append(RangeSelectionOverlay(component=plot))
        plot.overlays.append(zoom)

    def update(self, xarray, anglearray, RefArray, TransArray, Reflectance_AVG):   
        print 'UPDATING OPTIC VIEW'
        self.xarray=xarray
        self.angles=anglearray
        self.RefArray=RefArray
        self.TransArray=TransArray
        self.Reflectance_AVG=Reflectance_AVG

        # Totally makes new dat and redraws plots instead of updating data.  Otherwise, need 5 array
        # plot data objects and speed increase is minimal
        self.data = ArrayPlotData(x=self.xarray, 
                                  angs=self.angles, 
                                  Ref=self.RefArray, 
                                  Trans=self.TransArray, 
                                  Avg=self.Reflectance_AVG)
        self.create_plots()

    def get_sexy_data(self):
        '''Returns the data in a list that can be immediately read back in another instance of opticview.  
        Note this is not the same as the arrayplotdata getdata() function'''
        return [self.xarray, self.angles, self.RefArray, self.TransArray, self.Reflectance_AVG]

    def set_sexy_data(self, data_list):
        '''Takes in data formatted deliberately from "get_sexy_data" and forces an update'''
        self.update(data_list[0], data_list[1], data_list[2], data_list[3], data_list[4])

    # Legacy: gets average T and R values 
    def get_dataframe(self):
        ''' Returns dataframe of data for easier concatenation into a runpanel dataframe used by
        simulations'''

        delim='_' #Separate R,T modes (R1, R2 for each mode)
        d={}
        for theta, i in enumerate(self.angles):
            d['R'+delim+str(theta)+delim+str(i)]=self.RefArray[i]
            d['T'+delim+str(theta)+delim+str(i)]=self.TransArray[i]

        #rowwise mean of reflectance at various angles (Note, avgarray is the angles used
        tavg=np.mean(self.TransArray, axis=0)    
        ravg=np.mean(self.RefArray, axis=0)
        d.update({'Ravg':ravg, 'Tavg':tavg})
        return DataFrame(d, index=self.xarray)


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


    def _get_ereal(self): return self.earray.real
    def _get_eimag(self): return self.earray.imag
    def _get_nreal(self): return self.narray.real
    def _get_nimag(self): return self.narray.imag

    def create_plots(self):
        self.eplot = ToolbarPlot(self.data)
        self.nplot= ToolbarPlot(self.data)
        self.eplot.plot(("x", "er"), name="ereal", color="red", linewidth=4)
        self.eplot.plot(("x", "er"), name="ereal data", color="orange", type='scatter', marker_size=2)
        self.eplot.plot(("x", "ei"), name="eimag", color="green", linewidth=4)
        self.eplot.plot(("x", "ei"), name="eimag data", color="orange", type='scatter', marker_size=2)

        self.nplot.plot(("x", "nr"), name="nreal", color="red", linewidth=4)
        self.nplot.plot(("x", "nr"), name="nreal data", color="orange", type='scatter', marker_size=2)
        self.nplot.plot(("x", "ni"), name="nimag", color="green", linewidth=4)
        self.nplot.plot(("x", "ni"), name="nimag data", color="orange", type='scatter', marker_size=2)	

        self.add_tools_title(self.eplot, 'Dielectric ')
        self.add_tools_title(self.nplot, 'Index of Refraction ')

    def add_tools_title(self, plot, title_keyword):
        '''Used to add same tools to multiple plots'''
        plot.title = title_keyword + 'vs. Wavelength'
        plot.legend.visible = True

        bottom_axis = PlotAxis(plot, orientation='bottom', title=self.xunit, label_color='red', label_font='Arial', tick_color='green', tick_weight=1)
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
        self.xunit=xunit ;  self.xarray=xarray
        self.earray=earray; self.narray=narray
        if self.data == None:
            self.data = ArrayPlotData(x=self.xarray, er=self.ereal, nr=self.nreal, ei=self.eimag, ni=self.nimag)
            self.create_plots()
        else:
            self.update_data()

    def update_data(self):
        self.data.set_data('x',self.xarray) ; self.data.set_data('er', self.ereal)
        self.data.set_data('nr', self.nreal) ; self.data.set_data('ei', self.eimag)
        self.data.set_data('ni', self.nimag)
        self.eplot.request_redraw() ; self.nplot.request_redraw()

    ####### USED FOR SIMULATION STORAGE MOSTLY #####

    def get_sexy_data(self):
        '''Returns the data in a list that can be immediately read back in another instance of opticview.  Note this is not the same as the arrayplotdata getdata() function'''
        return [self.xarray, self.ereal, self.nreal, self.eimag, self.nimag]

    def set_sexy_data(self, data_list):
        '''Takes in data formatted deliberately from "get_sexy_data" and forces an update'''
        self.update(data_list[0], data_list[1], data_list[2], data_list[3])

    def get_dataframe(self):
        ''' Returns dataframe of data for easier concatenation into a runpanel dataframe used by
        simulations'''
        d = {'er' : self.ereal, 'nr':self.nreal, 'ei':self.eimag, 'ni':self.nimag}   
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

    exmax=Tuple(0,0)     #Technically properties but don't update with view for some reason
    absmax=Tuple(0,0)    #Pukes if 0,0 default not provided, but this is probably due to my program not tuple trait
    scatmax=Tuple(0,0)
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
        rounding=3  #Change for rounding of these 
        value=max(array)
        index=int(where(array==value)[0])  #'where' returns tuple since is can be used on n-dim arrays
        x=self.xarray[index]
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

        bottom_axis = PlotAxis(plot, orientation='bottom', title=self.xunit, label_color='red', label_font='Arial', tick_color='green', tick_weight=1)
        vertical_axis = PlotAxis(plot, orientation='left',
                                 title=str(title_keyword))

        plot.underlays.append(vertical_axis)
        plot.underlays.append(bottom_axis)

        # Attach some tools to the plot
        plot.tools.append(PanTool(plot))
        zoom = ZoomTool(component=plot, tool_mode="box", always_on=False)
        plot.overlays.append(zoom)

    def update(self, xarray, extarray, scatarray, absarray, xunit):         
        self.xunit=xunit ;self.xarray=xarray
        self.extarray=extarray ; self.absarray=absarray ; self.scatarray=scatarray

        if self.data == None:
            self.data = ArrayPlotData(x=self.xarray, Scattering=self.scatarray, Absorbance=self.absarray , Extinction=self.extarray)
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