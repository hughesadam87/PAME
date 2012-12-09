from material_traits_v4 import Sellmeir, DispWater, basic_material

class CompositeMaterial(basic_material):
	'''Still inherits basic traits like earray, narray and how they are interrelated'''
	from material_mixer import MG_Mod, Bruggeman, QCACP, MG
	from interfaces import IMixer, IStorage
	from material_editor_v2 import MaterialStorage
	from modeltree_v2 import Main



#	modeltree=Instance(Main,())
	Material1=Instance(IMaterial)
	Material2=Instance(IMaterial)   #Make these classes later
	MixingStyle=Enum('MGMOD', 'Bruggeman', 'QCACP', 'MG')
	Mix=Instance(IMixer)
	Vfrac=DelegatesTo('Mix')	#Coordinates with parameter in mixer
	earray=DelegatesTo('Mix', prefix='mixedarray')
#	materials_trees=DelegatesTo('modeltree')

	selectmat1=Button ; selectmat2=Button

	matstorage=Instance(IStorage)

	mixgroup=Group(   VGroup(
				HGroup(
					Item('MixingStyle', label='Mixing Method', show_label=False),
		 			Item('Mix', editor=InstanceEditor(), style='custom', label='Mixing Parameters', show_label=False ),
					),	
				Item('mviewbutton', label='Show Full Material', show_label=False),
							),    #Group Label here
			label='Mixing Parameters')            #View Label 

	compmatgroup=Group(Item('mat_name', label='Material Name'),
		Tabbed( 
	         Item('Material1', editor=InstanceEditor(), style='custom', label='Solute', show_label=False),
		 Item('Material2', editor=InstanceEditor(), style='custom', label='Solvent', show_label=False),
		      ),
		Item('selectmat1'), Item('selectmat2'),
		label='Materials')

	traits_view=View(Include('compmatgroup' ), Include('mixgroup'), resizable=True, buttons=OKCancelButtons)


	def _Material1_default(self): return Sellmeir(specparms=self.specparms) 
	def _Material2_default(self): return Dispwater(specparms=self.specparms) #MIXED MATERIAL WITH DEFAULTS DETERMINED BY THIS INSTANCE
	def _Mix_default(self): return self.MG_Mod(specparms=self.specparms, solventmaterial=self.Material2, solutematerial=self.Material1)
	def _MixingStyle_changed(self): 
		self.update_mix()
		self.update_mview()

	def _Material1_changed(self): 
		self.Material1.specparms=self.specparms #Autosyncs materials
		self.update_mix()

	def _Material2_changed(self): 
		print 'mat 2 changing'
		self.Material2.specparms=self.specparms  
		self.update_mix()

	def _specparms_changed(self):
		if self.Material1.specparms != self.specparms:
			self.Material1.specparm = self.specparms
		if self.Material2.specparms != self.specparms:
			self.Material2.specparm = self.specparms

	def update_mix(self):
		vfrac=self.Vfrac
		if self.MixingStyle=='MG':
			self.Mix=self.MG(specparms=self.specparms, solventmaterial=self.Material2, solutematerial=self.Material1, Vfrac=vfrac)
		elif self.MixingStyle=='Bruggeman':
			self.Mix=self.Bruggeman(specparms=self.specparms, solventmaterial=self.Material2, solutematerial=self.Material1,Vfrac=vfrac)
		elif self.MixingStyle=='QCACP':
			self.Mix=self.QCACP(specparms=self.specparms, solventmaterial=self.Material2, solutematerial=self.Material1,Vfrac=vfrac)
		elif self.MixingStyle=='MGMOD':
			self.Mix=self.MG_Mod(specparms=self.specparms, solventmaterial=self.Material2, solutematerial=self.Material1,Vfrac=vfrac)

	def _mat_name_default(self): return  (self.Material1.mat_name + '  IN   ' + self.Material2.mat_name)
		
	def _selectmat1_fired(self): 
		self.matstorage=self.MaterialStorage(specparms=self.specparms)
		f=self.matstorage.configure_traits(kind='nonmodal')
		if f.current_selection != None:
			self.material1=f.current_selection 
	
	def _Vfrac_changed(self): 
		self.update_data() ; self.update_mview()

if __name__ == '__main__':

	f=CompositeMaterial()
	f.configure_traits()

