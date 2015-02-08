

from pame.modeltree_v2 import Model
from pame.composite_tree import CompositeMain
from pame.nanotree import NanoMain

class MaterialChooser(HasTraits):
    """ """
    modeltree=Instance(Model,())
    compositetree=Instance(CompositeMain,())
    nanotree=Instance(NanoMain,())    
    
    selectedtree=Property(depends_on='mat_class')  #Determines which tree to use to select materials
    mat_class=Enum('Bulk Material', 'Mixed Bulk Materials', 'Nanoparticle Objects')   
    
    def _get_selectedtree(self): 
        if self.mat_class=='Bulk Material': 
            return self.modeltree 
        if self.mat_class=='Mixed Bulk Materials':
            return self.compositetree
        if self.mat_class=='Nanoparticle Objects': 
            return self.nanotree    
