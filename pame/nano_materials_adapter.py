from simple_materials_adapter import BasicAdapter

class NanoSphereAdapter(BasicAdapter):
	name='BareNanoSphere'
	source='Absorption and Scattering of Light by Small Particles.  Huffman Bohren.  1983'
	notes='Makes a nanosphere with full mie scattering from an input material'
	apikey='nanosphere'

class NanoSphereShellAdapter(BasicAdapter):
	name='Nanosphere with Shell'
	source='Absorption and Scattering of Light by Small Particles.  Huffman Bohren.  1983'
	notes='Makes a nanosphere with full mie scattering from an input material and shell material'
	apikey='nanospherehshell'



