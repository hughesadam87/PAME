from simple_materials_adapter import BasicAdapter

class ABCNanoAdapter(BasicAdapter):
        mat_class = 'nano'

class NanoSphereAdapter(ABCNanoAdapter):
	name = 'BareNanoSphere'
	source = 'Absorption and Scattering of Light by Small Particles.  Huffman Bohren.  1983'
	notes = 'Makes a nanosphere with full mie scattering from an input material'
	apikey = 'nanosphere'

class NanoSphereShellAdapter(ABCNanoAdapter):
	name = 'Nanosphere with Shell'
	source = 'Absorption and Scattering of Light by Small Particles.  Huffman Bohren.  1983'
	notes = 'Makes a nanosphere with full mie scattering from an input material and shell material'
	apikey = 'nanospherehshell'


class DoubleNanoAdapter(ABCNanoAdapter):
	name = 'Double Nanosphere'
	source = 'Absorption and Scattering of Light by Small Particles.  Huffman Bohren.  1983'
	notes = 'Mixed layer of two nanoparticles with shells'
	apikey = 'doublenanoshell'	

