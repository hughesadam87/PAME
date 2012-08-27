from numpy import linspace, meshgrid, pi, sin, arange

from chaco.api import *
from enable.api import *
from traits.api import *
from traitsui.api import *

from chaco.tools.api import PanTool, ZoomTool


def _create_img_plot_component():# Create a scalar field to colormap

    xbounds = (-2*pi, 2*pi, 600)
    ybounds = (-1.5*pi, 1.5*pi, 300)
    xs = linspace(*xbounds)
    ys = linspace(*ybounds)
    x, y = meshgrid(xs,ys)
    z = sin(x)*y

    # Create a plot data obect and give it this data
    pd = ArrayPlotData()
    pd.set_data("imagedata", z)

    plot = Plot(pd)
    plot.tools.append(PanTool(plot))


    img_plot = plot.img_plot("imagedata", xbounds=(xs[0],xs[-1]),
colormap=jet)[0]

    return plot

def _create_line_plot_component():# Create a scalar field to colormap

    xbounds = (-2*pi, 2*pi, 600)
    xs = linspace(*xbounds)
    ys = pi * sin(xs)

    # Create a plot data obect and give it this data
    pd = ArrayPlotData()
    pd.set_data("x", xs)
    pd.set_data("y", ys)

    plot = Plot(pd)
    plot.tools.append(PanTool(plot))

    line_plot = plot.plot(("x", "y"), xbounds=(xs[0],xs[-1]))

    return plot

size = (400, 300)
title="Colormapped Image Plot"

class Demo(HasTraits):

    img = Instance(Component)
    line = Instance(Component)

    traits_view = View(
                    Group(
                        Item('img', editor=ComponentEditor(size=size),
                             show_label=False),
                        Item('line', editor=ComponentEditor(size=size),
                             show_label=False),
                        orientation = "vertical"),
                    resizable=True, title=title
                    )

    def synch(self):
        self.line.index_range = self.img.index_range

    def _img_default(self):
        return _create_img_plot_component()

    def _line_default(self):
        return _create_line_plot_component()

demo = Demo()
demo.synch()

if __name__ == "__main__":
    demo.configure_traits()

