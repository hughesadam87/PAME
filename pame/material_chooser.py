from traits.api import HasTraits, Property, Enum, Instance, Any, Dict, List

from pame.modeltree_v2 import Model
#from pame.composite_tree import CompositeMain
#from pame.nanotree import NanoMain


# DONT CHANGE, DONT BOTHER MAKING A TRAIT ITS JUST HASSLE
_matdict ={'Bulk Material': Model(),
 #               'Mixed Bulk Materials':CompositeMain(),
 #               'Nanoparticle Objects':NanoMain()
               }

class MaterialChooser(HasTraits):
    """ """
    selectedtree=Instance(HasTraits) #Can't be a property

    mat_class=Enum('Bulk Material', 'Mixed Bulk Materials', 'Nanoparticle Objects')   
    
    def _mat_class_default(self):
        return 'Bulk Material'
    
    # Yes, is necessary to default and _changed in separate listners
    def _selectedtree_default(self):
        return _matdict[self.mat_class]

    def _mat_class_changed(self):
        self.selectedtree = _matdict[self.mat_class]

    
