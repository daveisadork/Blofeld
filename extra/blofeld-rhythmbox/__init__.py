import rhythmdb, rb
import gobject, gtk
import urllib2
import cjson as json
import datetime

class Blofeld(rb.Plugin):

    def __init__(self):
        rb.Plugin.__init__(self)

    def activate(self, shell):
        print "activating sample python plugin"
        self.db = shell.get_property("db")
        self.entry_type = self.db.entry_register_type("BlofeldEntryType")
        model = self.db.query_model_new_empty()
        group = rb.rb_source_group_get_by_name ("library")
        if not group:
            group = rb.rb_source_group_register ("library",
                _("Library"),
                rb.SOURCE_GROUP_CATEGORY_FIXED)
        theme = gtk.icon_theme_get_default()
        rb.append_plugin_source_path(theme, "/icons")

        width, height = gtk.icon_size_lookup(gtk.ICON_SIZE_LARGE_TOOLBAR)
        icon = rb.try_load_icon(theme, "network-server", width, 0)
        self.source = gobject.new (BlofeldSource,
                        shell=shell,
                        entry_type=self.entry_type,
                        source_group=group,
                        icon=icon,
                        plugin=self)
        shell.register_entry_type_for_source(self.source, self.entry_type)
        shell.append_source(self.source, None) # Add the source to the lis
        self.pec_id = shell.get_player().connect('playing-song-changed', self.playing_entry_changed)

    def deactivate(self, shell):
        print "deactivating sample python plugin"
        self.source.delete_thyself()
        self.source = None

    def playing_entry_changed (self, sp, entry):
        self.source.playing_entry_changed (entry)


class BlofeldSource(rb.BrowserSource):
    __gproperties__ = {
        'plugin': (rb.Plugin, 'plugin', 'plugin', gobject.PARAM_WRITABLE|gobject.PARAM_CONSTRUCT_ONLY),
    }

    def __init__(self):
        rb.BrowserSource.__init__(self, name=_("Blofeld"))
        self.__activated = False

    def do_impl_activate(self):
        if not self.__activated:
            shell = self.get_property('shell')
            self.__db = shell.get_property('db')
            self.__entry_type = self.get_property('entry-type')
            self.__activated = True
        rb.BrowserSource.do_impl_activate (self)
        song_list = urllib2.urlopen('http://127.0.0.1:8080/list_songs?list_all=true')
        songs = json.decode(song_list.read())
        trackurl = 'http://127.0.0.1:8080/get_song?songid='
        for song in songs:
            entry = self.__db.entry_lookup_by_location (trackurl + song['id'])
            if entry == None:
                entry = self.__db.entry_new(self.__entry_type, trackurl + song['id'])
            self.__db.set(entry, rhythmdb.PROP_ARTIST, song['artist'])
            self.__db.set(entry, rhythmdb.PROP_ALBUM, song['album'])
            self.__db.set(entry, rhythmdb.PROP_TITLE, song['title'])
            self.__db.set(entry, rhythmdb.PROP_TRACK_NUMBER, song['tracknumber'])
            try:
                self.__db.set(entry, rhythmdb.PROP_BITRATE, song['bitrate'] / 1000)
            except:
                pass
            try:
                year = int(song['date'][0:4])
                date = datetime.date(year, 1, 1).toordinal()
                self.__db.set(entry, rhythmdb.PROP_DATE, date)
            except:
                pass
            try:
                self.__db.set(entry, rhythmdb.PROP_GENRE, ", ".join(song['genre']))
            except:
                self.__db.set(entry, rhythmdb.PROP_GENRE, "Unknown")
            try:
                self.__db.set(entry, rhythmdb.PROP_DURATION, int(round(song['length'])))
            except:
                pass
            self.__db.commit()

    def playing_entry_changed (self, entry):
        if not self.__db or not entry:
            return
        if entry.get_entry_type() != self.__db.entry_type_get_by_name("BlofeldEntryType"):
            return
        gobject.idle_add (self.emit_cover_art_uri, entry)

    def emit_cover_art_uri (self, entry):
        url = self.__db.entry_get(entry, rhythmdb.PROP_LOCATION).replace('song?', 'cover?size=500&')
        self.__db.emit_entry_extra_metadata_notify (entry, 'rb:coverArt-uri', url)
        return False


gobject.type_register(BlofeldSource)
