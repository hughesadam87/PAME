from simple_materials_adapter import BasicAdapter

class NanoSphereAdapter(BasicAdapter):
	from advanced_objects_v2 import NanoSphere
	name='BareNanoSphere'
	source='Hoffman Stegawitz'
	notes='Makes a nanosphere with full mie scattering from an input material'

	def populate_object(self): self.matobject=self.NanoSphere()

class NanoSphereShellAdapter(BasicAdapter):
	from advanced_objects_v2 import NanoSphereShell
	name='Nanosphere with Shell'
	source='NEED TO UPDATE'
	notes='Makes a nanosphere with full mie scattering from an input material and shell material'

	def populate_object(self): self.matobject=self.NanoSphereShell()



