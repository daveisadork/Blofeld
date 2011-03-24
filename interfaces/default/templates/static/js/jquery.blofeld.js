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
    
    var ajaxQueue = {
            artists: null,
            albums: null,
            songs: null,
            tags: null
    },
    settings = {},
    methods = {
        init: function (options) {
            return this.each(function() {
                if (options) { 
                    $.extend(settings, options);
                }          
            });
        },
        listArtists: function (query, callback) {
            return this.each(function() {
                var $this = $(this),
                    options = {output: 'html'};
                if (ajaxQueue.artists) {
                    ajaxQueue.artists.abort();
                }
                if (query) {
                    options.query = query;
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
        }
    };
    
    $.fn.blofeld = function (method, args) {
        
        // Method calling logic
        if (methods[method]) {
            return methods[method].apply(this, Array.prototype.slice.call(arguments, 1));
        } else if (typeof method === 'object' || !method) {
            return methods.init.apply(this, arguments);
        } else {
            $.error('Method ' +  method + ' does not exist on jQuery.blofeld');
            return 0
        }    
    };
})(jQuery);