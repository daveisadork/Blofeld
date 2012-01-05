/*
 * Blofeld - All-in-one music server
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

(function () {
    "use strict";
    
    var loadPage = function (type, options) {
        $("#" + type + "-list").blofeld("list" + type, options, function () {
            $.mobile.changePage($("#" + type));
            $("#" + type + "-list").listview("refresh");

        });
        
    };
    
    $(document).bind( "pagebeforechange", function( e, data ) {

        // We only want to handle changePage() calls where the caller is
        // asking us to load a page by URL.
        if ( typeof data.toPage === "string" ) {

            // We are being asked to load a page by URL, but we only
            // want to handle URLs that request the data for a specific
            // category.
            var u = $.mobile.path.parseUrl( data.toPage ),
                re = /^#Albums/;

            if ( u.hash.search(re) !== -1 ) {

                // We're being asked to display the items for a specific category.
                // Call our internal method that builds the content for the category
                // on the fly based on our in-memory category data structure.
                //showAlbums( u, data.options );
                //alert(data.options.pageData.id);
                $("#Albums h1").text(data.options.pageData.name);
                
                    
                // Make sure to tell changePage() we've handled this call so it doesn't
                // have to do anything.
                e.preventDefault();
                loadPage("Albums", {artists: [data.options.pageData.id]});
            }
        }
    });

    $(document).bind( "pageinit", function (e, data) {
        loadPage("Artists");
    });
}());
