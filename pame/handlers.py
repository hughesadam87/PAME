""" Custom popup menus for prompting user on selection/saving eg 
Messages like 'Are you sure you want to overwrite file?'
"""

import os
from traits.api import HasTraits, File, Str, Property
from traitsui.api import View, Item, OKCancelButtons

### Envoke as follows
#popup=BasicDialog(message='Simulation complete.  Would you like to save now?')
#ui=popup.edit_traits(kind='modal')
#if ui.result == True:
     #self.output_simulation()

class BasicDialog(HasTraits):
     ''' Basic yes/no popup.'''
     message=Str

     traits_view = View(
          Item('message', style='readonly', show_label=False),
          buttons=OKCancelButtons, kind='popup', title='Notification',
     )     

class WarningDialog(BasicDialog):
     ''' Basic yes/no popup.'''

     traits_view = View(
          Item('message', style='readonly', show_label=False),
          buttons=OKCancelButtons, kind='popup', title='Warning',
     )  

class FileOverwriteDialog(BasicDialog):
     filename = File
     _shortname=Property(depends_on='filename')

     traits_view = View(
          Item('message', style='readonly', label='Warning', show_label=True),
          buttons=OKCancelButtons,
          kind='popup',
          title='File already exists.',
     )
     
     def _get__shortname(self):
          return os.path.split(self.filename)[1]

     def _message_default(self):
          return '"%s" will be overwritten, are you sure you want to continue?' % self._shortname




