from simple_materials_adapter import BasicAdapter

class ABCCompAdapter(BasicAdapter):
        mat_class = 'mixed'  #<--- don't change, needed by layer editor

class CompositeAdapter(ABCCompAdapter):
        name='Composite Material for Bulk Materials'
        source='N/A'
        notes='Takes in two basic materials and mixes them according to effective medium approximations'
        apikey = 'composite'
        
class CompositeMaterial_EquivAdapter(ABCCompAdapter):
        name='General composite equivalent object for mixing spheres and shells'
        source='NEED TO UPDATE'
        notes='This is the basis for several other objects such as nanoparticles'
        apikey = 'composite_equiv'

class SphericalInclusions_DiskAdapter(ABCCompAdapter):
        name='Class for mixing spherical objects on a flat disk surface'
        source='None: Uses basic counting'
        notes='This is the base class for NanoSpheres on a disk or other surface'
        apikey = 'sphere_inc_disk'