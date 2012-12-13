from traits.api import HasTraits, File, Str
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


class FileOverwriteDialog(BasicDialog):
     filename = File

     traits_view = View(
          Item('message', style='readonly', label='Warning', show_label=True),
          buttons=OKCancelButtons, kind='popup', title='File already exists',
     )

     def _message_default(self):
          return '"%s" file will be overwritten, are you sure you want to continue?'%self.filename




