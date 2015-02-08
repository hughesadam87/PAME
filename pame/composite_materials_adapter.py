from simple_materials_adapter import BasicAdapter

class CompositeAdapter(BasicAdapter):
	from composite_materials_v2 import CompositeMaterial
	name='Composite Material for Bulk Materials'
	source='N/A'
	notes='Takes in two basic materials and mixes them according to effective medium approximations'

	def populate_object(self):
		self.matobject=self.CompositeMaterial()

class CompositeMaterial_EquivAdapter(BasicAdapter):
	from composite_materials_v2 import CompositeMaterial_Equiv
	name='General composite equivalent object for mixing spheres and shells'
	source='NEED TO UPDATE'
	notes='This is the basis for several other objects such as nanoparticles'

	def populate_object(self): 
		self.matobject=self.CompositeMaterial_Equiv()

class SphericalInclusions_DiskAdapter(BasicAdapter):
	from composite_materials_v2 import SphericalInclusions_Disk
	name='Class for mixing spherical objects on a flat disk surface'
	source='None: Uses basic counting'
	notes='This is the base class for NanoSpheres on a disk or other surface'

	def populate_object(self): 
		self.matobject=self.SphericalInclusions_Disk()

