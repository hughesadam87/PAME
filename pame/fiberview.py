from traits.api import Instance, HasTraits
from traitsui.api import View, Item
from mayavi.core.api import Engine
from mayavi.core.ui.api import MayaviScene, MlabSceneModel, SceneEditor
from mayavi.mlab import points3d

class FiberView(HasTraits):
    """This view is inherently connected to fiber model"""
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

	self.FiberEngine.start() ; self.FiberScene=MlabSceneModel(engine=self.FiberEngine)

	outter_tube=self.FiberScene.mlab.points3d(0, 0, 0, 
	                                          color=(.84, .84, .84),
	                                          opacity=.5, 
	                                          mode='cylinder',
	                                          extent=[-1, 1,-.1, .1, -.1, .1] )  #controls xmax,xmin,ymax etc.. all relative.  Must be -a to a for centered 
	inner_tube=self.FiberScene.mlab.points3d(0, 0, 0, 
	                                         color=(.77, .77, .77),
	                                         mode='cylinder',
	                                         extent=[-1.01, 1.01,-.05, .05, -.05, .05] ) 

if __name__ == '__main__':
	FiberView().configure_traits()

