# Blofeld - All-in-one music server
# Copyright 2010 Dave Hayes <dwhayes@gmail.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301, USA.

# This file isn't used at the moment.

songs = {
    '_id': '_design/songs',
    'views': {
        'all': {
            'map': '''
                function(doc) {
                    if (doc.type == 'song') {
                        emit(null, {
                            artist: doc.artist,
                            album: doc.album,
                            tracknumber: doc.tracknumber,
                            genre: doc.genre,
                            title: doc.title,
                            location: doc.location,
                            artist_hash: doc.artist_hash,
                            album_hash: doc.album_hash,
                            mtime: doc.mtime
                        });
                    }
                }'''
            }
        }
    }

artists = {
    '_id': '_design/artists',
    'views': {
        'all': {
            'map': '''
                function(doc) {
                    if (doc.type == 'song') {
                        emit(doc.artist_hash, doc.artist);
                    }
                }'''
            },
        'search': {
            'map': '''
                function(doc) {
                    if (doc.type == 'song') {
                        emit(doc.artist_hash, [doc.artist, doc.album, doc.title]);
                    }
                }'''
            }
        }
    }

albums = {
    '_id': '_design/albums',
    'views': {
        'all': {
            'map': '''
                function(doc) {
                    if (doc.type == 'song') {
                        emit(doc.album_hash, doc.album);
                    }
                }'''
            },
        'search': {
            'map': '''
                function(doc) {
                    if (doc.type == 'song') {
                        emit(doc.album_hash, {
                            search_string: [doc.artist, doc.album, doc.title].join(';'),
                            title: doc.album,
                            artist_hash: doc.artist_hash
                        });
                    }
                }'''
            },
        'by_artist': {
            'map': '''
                function(doc) {
                    if (doc.type == 'song') {
                        emit(doc.album_hash, 
                            {title: doc.album, artist: doc.artist_hash}
                            );
                    }
                }'''
            }
        }
    }
