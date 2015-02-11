''' Containers to store multiple instances of plots from basicplots.py'''

from traits.api import Str, Dict, Property, cached_property, Enum, Bool, \
     HasTraits, List, Instance, implements, on_trait_change
from traitsui.api import View, HGroup, Item, VGroup, ListStrEditor, InstanceEditor, CheckListEditor
from interfaces import IMaterial, ICompositeView
from enable.api import ComponentEditor, Component
from chaco.api import GridContainer, HPlotContainer, OverlayPlotContainer, Plot, ArrayPlotData

###
from basicplots import ScatterView

class MultiView(HasTraits):
    '''Used to store arbitrary plots and selection based on key/plot input'''
    host=Str('Host Unkown')   #Object which calls this, only needed for naming
    nameplot=Dict  #Dictionary with plot designator/name as key, plot itself as value
    plotname=Property(List, depends_on='nameplot, alphabetize')
    chooseplot=Enum(values='plotname')
    selectedplot=Property(depends_on='chooseplot')
    alphabetize=Bool(True)

    implements(ICompositeView)

    @cached_property
    def _get_plotname(self): 
        print 'nameplot passed'
        keys=self.nameplot.keys()
        if self.alphabetize == True:
            keys.sort()  #Consider using same techinque in gensim to sort string+int
        return keys          #If the need ever arises.

    @cached_property
    def _get_selectedplot(self): 
        self.nameplot[self.chooseplot].request_redraw()
        return self.nameplot[self.chooseplot]

    view = View( 
        HGroup(
            Item('host', show_label=False, style='readonly'),
            Item('chooseplot', label='Choose selected plot', show_label=False, style='simple'),
            Item('alphabetize', label='Order objects alphabetically'),
            ),
        Item('selectedplot', show_label=False, editor=ComponentEditor()),
        width=800, height=600, resizable=True   )


class DoubleSview(HasTraits):
    ''' Container for two instances of scatter view.  Takes in full Sview objects, so that composite
        plots can be built up using these '''

    scatt1=Instance(ScatterView) 
    scatt2=Instance(ScatterView)
    
    implements(ICompositeView)    

    datanames=['Scattering', 'Absorbance', 'Extinction']
    hideplots=List( editor = CheckListEditor(
        values = [ 'Scattering', 'Absorbance', 'Extinction' ],
        cols   = 3 ) )  #THESE ARE KEYS USED TO SETDATA IN SVIEW OBJECT (DON'T ALTER IN EITHER CODE)

    #Following is used to keep keys in plot objects separate (e.g. Absorbance is a plot key for scatt1 and scatt2#
    #These will turn it into Absorbance%s1 and Absorbance%s2#
    delimiter=Str('%')  
    s1_id=Str('s1')
    s2_id=Str('s2')	
    s1_color=Str('blue')
    s2_color=Str('red')

    alldata=Instance(ArrayPlotData)
    doubleplot=Instance(Plot)

    def _alldata_default(self): 
        """ Default ArrayPlotData with reserved names which will be updated when individual plot data
        objects are changed.
        names for the ArrayPlotData objects based on datanames (sig, absorb) plus the id and delimiter.  I reserve
        only one instance of 'x' """
        alldata=ArrayPlotData()

        for name in self.datanames: 
            alldata.set_data(name+self.delimiter+self.s1_id, [] )  
            alldata.set_data(name+self.delimiter+self.s2_id, [] )  
        alldata.set_data('x', [])
        return alldata

    def _doubleplot_default(self):
        ''' I add all the plots in one go, then use hide/show functions to change them'''
        plot=Plot(self.alldata)	
        for name in self.alldata.list_data():
            if name != 'x':
                if name.split(self.delimiter)[1] == self.s1_id:
                    color=self.s1_color
                elif name.split(self.delimiter)[1] == self.s2_id:
                    color=self.s2_color
                plot.plot(('x', name), name=name, linewidth=5, color=color)
        return plot


    @on_trait_change('scatt1.data.arrays, scatt2.data.arrays')
    def update_alldata(self):
        ''' This is how the plots update in real time, by listening to data.arrays.  I extract 'x' from
            the first plot, assuming it is the same between plots '''
        if self.scatt1 is not None:
            for name in self.scatt1.data.arrays:
                if name == 'x':
                    self.alldata.set_data((str(name)), self.scatt1.data.arrays[name] )
                else:
                    self.alldata.set_data((str(name)+self.delimiter+self.s1_id), 
                                      self.scatt1.data.arrays[name] )
        if self.scatt2 is not None:
            for name in self.scatt2.data.arrays:
                if name != 'x':
                    self.alldata.set_data((str(name)+self.delimiter+self.s2_id), 
                                          self.scatt2.data.arrays[name] )


    @on_trait_change('hideplots')
    def update_lines(self):	
        ''' Allows users to hide or show plots by first plotting all the lines.  Note that since there 
            are two plots, there are actually two matches to name.  EG if name is "abs" then its going
            to hide or show abs%1 and abs%2, that is why I only need to put one call below '''
        for name in self.doubleplot.plots:
            if name.split(self.delimiter)[0] in self.hideplots:
                self.doubleplot.hideplot(name)
            else:
                self.doubleplot.showplot(name)				
        self.doubleplot.request_redraw()  #Necessary


    traits_view=View(
        VGroup(
            HGroup(
                Item('scatt1', style='custom', show_label=False),
                Item('scatt2', style='custom', show_label=False),
                label="Separate"),
            VGroup(				
                Item('hideplots',style='custom', label='Hide Plot'),
                Item('doubleplot', editor=ComponentEditor(size=(200,100)), show_label=False ),
                label="Combined"),
            layout='tabbed'),
        resizable=True)



if __name__ == '__main__':
    NanoSphereShell().configure_traits()