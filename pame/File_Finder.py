"""This program is modified from livesearch example in traits4.0.  The main change is that the table 
selection can be multiple rows, meaning 'selected' returns a list.  This would throw off many of the
functions which were used to open a file.  For example, the search function to find a line in a file 
would need modified.  Most of these file-related methods like "selected_contents, selected_line" 
were deleted.  Most search features like the directory structure, recursive search, type_ranges
(etc...) were retained."""

from os import walk, getcwd, listdir

from os.path \
     import basename, dirname, splitext, join

from traits.api \
     import HasTraits, File, Directory, Str, Bool, List, Int, Enum, DictStrList, Button, Instance, \
     Property, Any, property_depends_on

from traitsui.api \
     import View, VGroup, VSplit, HGroup, Item, TableEditor, CodeEditor, \
     TitleEditor, HistoryEditor, DNDEditor, OKCancelButtons

from traitsui.table_column import ObjectColumn

#-- The Live Search table editor definition ------------------------------------

class FileColumn ( ObjectColumn ):

    def get_drag_value ( self, object ):
        return object.full_name

###Used for managing selected files###
source_editor = TableEditor(
    columns = [
        FileColumn(     name        = 'base_name',
                        label       = 'Source Files',
                        width       = 0.30,
                        editable    = False ),
        ],
    filter_name        = 'filter',
    auto_size          = False,
    show_toolbar       = False,
    selection_mode     = 'rows',          #Multiple selection
    selected           = 'selected',
    selection_color    = 0x000000,
    selection_bg_color = 0xFBD391
)

file_editor = TableEditor(
    columns = [
        FileColumn(     name        = 'base_name',
                        label       = 'Selected Files',
                        width       = 0.30,
                        editable    = False ),
        ],
    filter_name        = 'filter',
    auto_size          = False,
    show_toolbar       = False,
    selection_mode     = 'rows',          #Multiple selection
    selected           = 'selected_file',
    selection_color    = 0x000000,
    selection_bg_color = 0xFBD391
)

#-- LiveSearch class -----------------------------------------------------------

class LiveSearch ( HasTraits ):
    """ Searches for files in operating system.  Adapted heavily from traits examples."""
    #THIS DICTSTRINGLIST CAN BE OVERWRITTEN AT ANY TIME AND THE PROGRAM WILL NOT FAULTER, MEANING CUSTOM FILE SEARCHES ARE POSSIBLE

    ValidTypes =DictStrList({
#	    'Python': [ '.py' ],
            'Sopra':      [ '.nk'],
            'XNK':    [ '.txt', '.dat' ],   #CAN EDIT MODULE WHICH CONTROLS THIS TO ADD "ANY" OPTION, OR MAYBE FILTER = NONE OPTION
            'XNK_csv': ['.csv']
#	    'Java':   [ '.java' ],
#	    'Ruby':   [ '.rb' ]
    })

    #A list of the keys in ValidTypes, basically a list of searchable types 'Python' vs. 'Java'
    types_list=Property(List, depends_on='ValidTypes')

    # Enumerated list of the above list (Allows user to select based on types_name)
    type_range = Enum(values='types_list')

    # The currenty root directory being searched:
    root = Directory( getcwd(), entries = 10 )

    # Should sub directories be included in the search:
    recursive = Bool( False )

    # The current search string:
    search = Str()

    # Is the search case sensitive?
    case_sensitive = Bool( False )

    # The live search table filter:
    filter = Property # Instance( TableFilter )

    # The current list of source files being searched:
    source_files = Property # List( SourceFile )

    # The current list of items which are deposited for return by the user
    my_files = List

    # The currently selected source file:
    selected = Any # Instance( SourceFile )

    # The currently selected stored file:
    selected_file=Any# Instance( SourceFile)

    # The currently selected match:
    selected_match = Int

    # source_summary of current number of files and matches:
    source_summary = Property # Str

    # selected_summary of current number of selected files and matches:
    selected_summary = Property # Str

    # Button to add files from source list to return list
    Add=Button 
    AddAll=Button 
    RemoveAll=Button 
    Remove=Button

    #-- Traits UI Views --------------------------------------------------------

    view = View(
        VGroup(
            HGroup(
                Item( 'root',            #Directory
                      id    = 'root',
                      label = 'Path',
                      width = 0.5
                      ),
                Item( 'recursive' ),
                Item( 'type_range', label = 'Type' ),  #HERE IS FILE TYPE

                # COMMENTED OUT STRING SEARCH, DONT DELETE THIS LETS ME SEARCH FILES 
                # MUST ALSO UNCOMMENT 2 METHODS AT END OF FILE
#                Item( 'search',
#                      id     = 'search',
#                      width  = 0.5,
#                      label = 'Search for infile string',
#                      editor = HistoryEditor( auto_set = True )
#                      ),
#                Item( 'case_sensitive' )
                ),
            VSplit(
                VGroup(
                    HGroup(    
                        VGroup(
                            Item( 'source_summary', editor = TitleEditor(), show_label=False ),
                            Item( 'source_files',
                                  id     = 'source_files',
                                  editor = source_editor, show_label=False),
                            HGroup(  Item('Add', label='Deposit Selected', show_label=False), 
                                     Item('AddAll', label='Deposit All', show_label=False) 
                                     )	
                            ),


                        VGroup(
                            Item( 'selected_summary', editor = TitleEditor(), show_label=False ),
                            Item( 'my_files',
                                  editor=file_editor, show_label=False),
                            HGroup( Item('Remove', 
                                         label='Remove Selected',
                                         show_label=False, 
                                         enabled_when='len(my_files) > 0'),
                                    Item('RemoveAll', 
                                         label='Remove All Stored',
                                         show_label=False,
                                         enabled_when='len(my_files) > 0') )
                            ),
                        ),
                    ),
                dock        = 'horizontal',
                show_labels = False
                ),
            ),
        title     = 'Live File Search',
        id        = 'File Search Mod',
        width     = 0.75,
        height    = 0.67,
        resizable = True,
        buttons=OKCancelButtons  #Why don't these work on small button operations
    )

    # Button Events
    # -------------
    def _Add_fired(self):
        for afile in self.selected:
            if afile not in self.my_files:
                self.my_files.append(afile)

    def _AddAll_fired(self):
        """ Add all files in a directory possibly.  Can add a lot of files, so
        instead of appending one by one, add them all at once to avoid over-triggering
        event handlers in modeltree_v2.py, which will update a dictionary every single
        time something in here changes.
        """
        new = []
        for afile in self.source_files:
            if afile not in self.my_files:
                new.append(afile)                
        self.my_files.extend(new)

    def _Remove_fired(self):
        for afile in self.selected_file:  #Since multi rows, this is a list, even when selected on object
            self.my_files.remove(afile)   #Selected_file is the variable for all selections on file table

    def _RemoveAll_fired(self): 
        self.my_files=[]

    #-- Property Implementations -----------------------------------------------

    def _get_types_list(self): 
        return self.ValidTypes.keys()

    @property_depends_on( 'search, case_sensitive' )
    def _get_filter ( self ):
        if len( self.search ) == 0:
            return lambda x: True

        return lambda x: len( x.matches ) > 0

    @property_depends_on( 'root, recursive, type_range' )
    def _get_source_files ( self ):
        """FIND THE SOURCE FILES populates with a list of source_files"""
        root = self.root
        if root == '':
            root = getcwd()

        valid_extensions = self.ValidTypes[ self.type_range ]      #TYPE_RANGES=EXTENSIONS. type_range=filenames
        if self.recursive:
            result = []
            for dir_path, dir_names, file_names in walk( root ):
                for file_name in file_names:	
                    extension=splitext(file_name)[1]
                    if extension in valid_extensions:
                        result.append( SourceFile(
                            live_search = self,
                            full_name   = join( dir_path, file_name ),
                            file_ext = extension) #File class set automatically
                                       )
            return result

        return [ SourceFile( live_search = self,
                             full_name   = join( root, file_name ) )
                 for file_name in listdir( root )
                 if splitext( file_name )[1] in valid_extensions ]


    @property_depends_on( 'source_files, search, case_sensitive' )
    def _get_source_summary ( self ):
        source_files = self.source_files
        search       = self.search
        if search == '':
            return 'A total of %d files found.' % len( source_files )


    @property_depends_on('my_files')
    def _get_selected_summary ( self ):
        return 'A total of %d files have been selected.' %(len(self.my_files) )


    #-- Traits Event Handlers --------------------------------------------------

    def _selected_changed ( self ): 
        self.selected_match = 1

    def _source_files_changed ( self ):
        if len( self.source_files ) > 0:
            self.selected = self.source_files[0]
        else:
            self.selected = None

#-- SourceFile class -----------------------------------------------------------

class SourceFile ( HasTraits ):
    """ Stores file in table."""
    
    # The search object this source file is associated with:
    live_search = Instance( LiveSearch )

    # The full path and file name of the source file:
    full_name = File

    # File extension (set by the live search _get_source_files mechanism)
    file_ext = Str

    #This is the specifier from type_ranges which corresponds to an extension e.g.( 'Python' to '.py')	
    fileclass = Property # Str

    # The base file name of the source file:
    base_name = Property # Str

    # The portion of the file path beyond the root search path:
    ext_path = Property # Str

    # NOT NECESSARY TO STORE CONTENTS, THEY ARE READ BY MATERIAL ADAPTERS
    # The contents of the source file:
    #contents = Property # List( Str )

    # The list of matches for the current search criteria:
    matches = Property # List( Str )

    # File ext


    @property_depends_on('file_ext')
    def _get_fileclass(self):
        """ For each file, looks at its extension (ie .nk, .txt) and returns
        category defined in LiveSeach.  For .nk, this would be Sopra.  For .txt
        this would be Other.
        """
        for key in self.live_search.ValidTypes.keys():
            for value in self.live_search.ValidTypes[key]:
                if self.file_ext in value:
                    return key

    @property_depends_on( 'full_name' )
    def _get_base_name ( self ):
        return basename( self.full_name )

    @property_depends_on( 'full_name' )
    def _get_ext_path ( self ):
        return dirname( self.full_name )[ len( self.live_search.root ): ]

    # DONT DELETE BELOW: USED FOR SEARCHING FILES FOR INFORMATION

    # CONTENTS ARE ONLY NECESSARY WHEN DOING SEARCHES IN THE FILE CONTENTS THEMSELVES (IE STRING SEARCH)
    #@property_depends_on( 'full_name' )
    #def _get_contents ( self ):
        #try:
            #with open( self.full_name, 'rb' ) as f:
                #contents = f.readlines()
            #return contents
        #except:
            #return ''

    # Used by search, but doesn't seem to be too time consuming
    #@property_depends_on( 'full_name, live_search.[search, case_sensitive]' )
    #def _get_matches ( self ):
        #search = self.live_search.search
        #if search == '':
            #return []

        #case_sensitive = self.live_search.case_sensitive
        #if case_sensitive:
            #return [ '%5d: %s' % ( (i + 1), line.strip() )
                     #for i, line in enumerate( self.contents )
                     #if line.find( search ) >= 0 ]

        #search = search.lower()
        #return [ '%5d: %s' % ( (i + 1), line.strip() )
                 #for i, line in enumerate( self.contents )
                 #if line.lower().find( search ) >= 0 ]


if __name__ == '__main__':
    demo = LiveSearch()
    demo.configure_traits()