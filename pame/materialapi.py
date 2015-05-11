from basic_material import BasicMaterial
from material_models import Constant, Sellmeir, Cauchy, DrudeBulk, Dispwater, Air
from material_files import SopraFile, XNKFile, XNKFileCSV

from composite_materials_v2 import \
     CompositeMaterial, CompositeMaterial_Equiv,SphericalInclusions_Disk, \
     SphericalInclusions_Shell

from advanced_objects_v2 import NanoSphere, NanoSphereShell


# DOES NOT INCLUDE FILE ADAPTERS/MATERIALS.  EACH OF THOSE HAS SPECIAL KEYWORD
# FOR INSTANTIATION DEFINED ON THE ADAPTER.

# DONT CHANGE KEY NAMES WITHOUT UPDATING 'apikey' trait in ADAPTERS
SIMPLEMATERIALS = dict(air=Air,
                       basic= BasicMaterial,
                       constant = Constant,
                       sellmeir = Sellmeir,
                       cauchy = Cauchy,
                       dispwater = Dispwater,
                       drudebulk = DrudeBulk,
                       sopra = SopraFile, 
                       xnk = XNKFile,
                       xnk_csv = XNKFileCSV
                       )

COMPOSITEMATERIALS = dict(composite = CompositeMaterial,
                          composite_equiv = CompositeMaterial_Equiv, #<-- General, not sphere in shell
                          sphere_inc_shell = SphericalInclusions_Shell,
                          sphere_inc_disk = SphericalInclusions_Disk
                          )

NANOMATERIALS = dict(nanosphere = NanoSphere,
                     nanospherehshell = NanoSphereShell)

# This is proper way to merge dictionares 
ALLMATERIALS = dict(SIMPLEMATERIALS.items() +
                    COMPOSITEMATERIALS.items() +
                    NANOMATERIALS.items())