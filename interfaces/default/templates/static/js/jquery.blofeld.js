/*
 * Blofeld plugin for jQuery JavaScript Library
 * https://github.com/daveisadork/Blofeld
 * 
 * Copyright (c) 2010 - 2011 Dave Hayes <dwhayes@gmail.com>
 * 
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301, USA.
 */

(function ($) {
    "use strict";
    
    var bitrates = [48, 64, 96, 128, 160, 192, 256, 320],
        ajaxQueue = {
            artists: null,
            albums: null,
            songs: null,
            tags: null
        },
        formats = ['mp3', 'ogg', 'oga', 'vorbis'],
        settings = {},
        methods = {};

    methods.init = function (options) {
        return this.each(function () {
            if (options) { 
                $.extend(settings, options);
            }          
        });
    };

    methods.listArtists = function (args, callback) {
        var options = {
            query: '',
            output: 'html'
        };
        return this.each(function () {
            var $this = $(this);
            if (args) {
                $.extend(options, args);
            }
            if (ajaxQueue.artists) {
                ajaxQueue.artists.abort();
            }
            ajaxQueue.artists = $.ajax({
                url: 'list_artists',
                data: options,
                success: function (response) {
                    $this.html(response);
                    ajaxQueue.artists = null;
                    if (callback) {
                        callback();
                    }
                }
            });
        });
    };

    methods.listAlbums = function (args, callback) {
        var options = {
            artists: [],
            query: '',
            output: 'html'
        };
        return this.each(function () {
            if (args) {
                $.extend(options, args);
            }
            var $this = $(this);
            if (ajaxQueue.albums) {
                ajaxQueue.albums.abort();
            }
            if (options.artists) {
                options.artists = options.artists.join(',');
            } else {
                options.artists = '';
            }
            ajaxQueue.artists = $.ajax({
                url: 'list_albums',
                data: options,
                success: function (response) {
                    $this.html(response);
                    ajaxQueue.albums = null;
                    if (callback) {
                        callback();
                    }
                }
            });
        });
    };

    methods.listSongs = function (args, callback) {
        var options = {
            artists: [],
            albums: [],
            query: '',
            output: 'html'
        };
        return this.each(function () {
            if (args) {
                $.extend(options, args);
            }
            var $this = $(this);
            if (ajaxQueue.songs) {
                ajaxQueue.songs.abort();
            }
            if (options.artists) {
                options.artists = options.artists.join(',');
            } else {
                options.artists = '';
            }
            if (options.albums) {
                options.albums = options.albums.join(',');
            } else {
                options.albums = '';
            }
            
            ajaxQueue.songs = $.ajax({
                url: 'list_songs',
                data: options,
                success: function (response) {
                    $this.html(response);
                    ajaxQueue.songs = null;
                    if (callback) {
                        callback();
                    }
                }
            });
        });
    };

    methods.getSongURL = function (args) {
        var songUrl, options = {
            songid: '',
            format: [],
            bitrate: 320
        };
        if (args) {
            $.extend(options, args);
        }
        if (!options.songid) {
            options.songid = $(this).attr('id');
        }
        songUrl = 'get_song?songid=' + options.songid;
        if (options.format) {
            if ($.inArray(options.format, formats)) {
                songUrl = songUrl + '&format=' + options.format.join(',');
            } else {
                $.error('Format must be null or an array containing one or more of ' + formats.join(', '));
            }
            
        }
        if (options.bitrate) {
            if ($.inArray(options.bitrate, bitrates)) {
                songUrl = songUrl + '&bitrate=' + parseInt(options.bitrate, 10);
            } else {
                $.error('Bitrate must be one of ' + bitrates.join(', ') + ' or null.');
            }
        }
        return songUrl;
    };

    methods.getTags = function (args, callback) {
        var options = {
            songid: ''
        };
        return this.each(function () {
            if (args) {
                $.extend(options, args);
            }
            if (ajaxQueue.tags) {
                ajaxQueue.tags.abort();
            }
            ajaxQueue.tags = $.ajax({
                url: 'get_tags',
                data: options,
                success: function (response) {
                    var tags = response.song;
                    ajaxQueue.tags = null;
                    if (callback) {
                        callback(tags);
                    }
                }
            });
        });
    };
    
    $.fn.blofeld = function (method) {
        if (methods[method]) {
            return methods[method].apply(this, Array.prototype.slice.call(arguments, 1));
        } else if (typeof method === 'object' || !method) {
            return methods.init.apply(this, arguments);
        } else {
            $.error('Method ' +  method + ' does not exist on jQuery.blofeld');
            return this.each();
        }    
    };
}(jQuery));