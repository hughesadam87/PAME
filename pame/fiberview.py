from traits.api import Instance, HasTraits
from traitsui.api import View, Item
from mayavi.core.api import Engine
from mayavi.core.ui.api import MayaviScene, MlabSceneModel, SceneEditor
from mayavi.mlab import points3d
import numpy as np
    

LIGHTGRAY = (.77, .77, .77)
DARKGRAY = (.84, .84, .84)

class ViewMlab(HasTraits):
    """ ABC Mayavi Class for 3d glyphs and surfaces.  At proof of pinciple
        stage.
    """
    FiberEngine = Instance(Engine, args=())
    FiberScene = Instance(MlabSceneModel)
    
    traits_view = View( Item('FiberScene',
                            editor=SceneEditor(scene_class=MayaviScene), 
                            style='custom',
                            show_label=False
                            ),		                      		
                        width=480, 
                        height=480) 
 					 
    def __init__(self, *args, **kwargs):
	super(HasTraits, self).__init__(*args, **kwargs)
	self.FiberEngine.start() 
	self.FiberScene=MlabSceneModel(engine=self.FiberEngine)	
	self.draw()
	
	
    def draw(self):
	raise NotImplementedError('ABC METHOD')
	

class EllispometryView(ViewMlab):
    #http://docs.enthought.com/mayavi/mayavi/auto/mlab_helper_functions.html
    #http://docs.enthought.com/mayavi/mayavi/auto/mlab_helper_functions.html#surf
    def draw(self):
	""" Square is a surface with a constant surface function IE f(x,y) = 1
	for constant color.  2dSquare glyph didn't have any fill
	"""
	square = np.empty((50,50))
	square.fill(1)
	self.FiberScene.mlab.surf(square, 
	                          color=LIGHTGRAY)


class FiberView(ViewMlab):
    
    def draw(self):
	outter_tube=self.FiberScene.mlab.points3d(0, 0, 0, 
	                                          color = LIGHTGRAY,
	                                          opacity=0, 
	                                          mode='cylinder',	                                          
	                                          extent=[-1, 1,-.1, .1, -.1, .1] )  #controls xmax,xmin,ymax etc.. all relative.  Must be -a to a for centered 

	inner_tube=self.FiberScene.mlab.points3d(0, 0, 0, 
	                                         color = DARKGRAY,
	                                         mode='cylinder',
	                                         extent=[-1.01, 1.01,-.05, .05, -.05, .05] )     

if __name__ == '__main__':
	FiberView().configure_traits()

