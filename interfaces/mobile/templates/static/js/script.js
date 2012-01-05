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
    
    var breadcrumb = []
    
    var loadPage = function (type, url, options) {
	var args = $.extend({output: 'html', extra_info: true}, options);
	$.mobile.changePage("list_" + type, {
	    data: args,
	    'data-url': url
	});
	
	/*
        $("#" + type + "-list").blofeld("list" + type, options, function () {
            $.mobile.changePage($("#" + type));
            $("#" + type + "-list").listview("refresh");

        });
	*/
    };
    
    var playSong = function (data) {
	
	var songUrl = $.fn.blofeld("getSongURL", {
                songid: data.options.pageData.songid,
                format: ['mp3', 'oga'],
                bitrate: 160
        });
	$("#jplayer").jPlayer("setMedia", {
	    mp3: songUrl,
	    oga: songUrl
	}).jPlayer("play");
	$.mobile.changePage($("#player"));
    };
    
    $(document).bind( "pagebeforechange", function( e, data ) {

        // We only want to handle changePage() calls where the caller is
        // asking us to load a page by URL.
        if ( typeof data.toPage === "string" ) {

            // We are being asked to load a page by URL, but we only
            // want to handle URLs that request the data for a specific
            // category.
            var u = $.mobile.path.parseUrl( data.toPage ),
                re = /^#(artists|albums|songs|player)/;

            if ( u.hash.search(re) !== -1 ) {

                // We're being asked to display the items for a specific category.
                // Call our internal method that builds the content for the category
                // on the fly based on our in-memory category data structure.
                //showalbums( u, data.options );
                //alert(data.options.pageData.id);
		e.preventDefault();
		var type = re.exec(u.hash)[1];
		var options = $.extend(data.options.pageData, {});
		var info = {}
		switch (type) {
		    case "player":
			playSong(data);
			break;
		    default:
			loadPage(type, data.options.dataUrl, options, info);
		}
		
            }
        }
    });

    $(document).ready(function () {
        $.mobile.changePage("#artists");
	$("#jplayer").jPlayer({
	    swfPath: "static/images/Jplayer.swf",
	    volume: 1,
	    solution: "flash,html",
	    supplied: "mp3,oga",
	    preload: "auto",

	    cssSelectorAncestor: "body",
	    cssSelector: {
		"play": "#play-button",
		"pause": "#pause-button",
		"stop" : ".jp-stop",
		"videoPlay" : ".jp-video-play",
		"seekBar" : ".jp-seek-bar",
		"playBar" : ".jp-play-bar",
		"mute" : ".jp-mute",
		"unmute" : ".jp-unmute",
		"volumeBar" : ".jp-volume-bar",
		"volumeBarValue" : ".jp-volume-bar-value",
		"currentTime" : "#play-time-current",
		"duration" : ".jp-duration" //"#play-time-total"
	    }
	});
	$("#inspector").jPlayerInspector({jPlayer:$("#jplayer")});

    });
}());
