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
    var ajaxQueue = {};
    ajaxQueue.tags = null;
    
    var playlist = [];
    var currentSong = null;
    var playlist_info = {};
    
    
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
    
    var playSong = function (songid) {
	
	if ($.inArray(songid, playlist) === -1) {
	    playlist = [];
	    $(".li-song").each(function (index) {
		playlist.push($(this).data().songid);
		playlist_info[$(this).data().songid] = $(this).data()
	    });
	}
	var song = playlist_info[songid];
	var player = $("#player").clone(true).attr('id', "player-" + songid).data('id', "player-" + songid);
	$('body').append(player);
	var iwidth = $("#player").width();
	$("#" + player.attr('id') + " h1").text(song.tracknumber + ". " + song.title);
	$("#" + player.attr('id') + " .title").text(song.title);
	$("#" + player.attr('id') + " .artist").text(song.artist);
	$("#" + player.attr('id') + " .album").text(song.album);
	$("#" + player.attr('id') + " .duration").text(song.length);
	$("#" + player.attr('id') + " .big-cover").html('<img src="get_cover?albumid=' + song.albumid + '&size=' + iwidth + '" width="' + iwidth + '"/>');
	var songUrl = $.fn.blofeld("getSongURL", {
                songid: songid,
                format: ['mp3'],
                bitrate: 320
        });
	$("#jplayer").jPlayer( "option", "cssSelectorAncestor", "#" + player.attr('id'))
	.jPlayer("setMedia", {
	    mp3: songUrl,
	    oga: songUrl
	}).jPlayer("play");
	currentSong = $.inArray(songid, playlist);
	
	$.mobile.changePage(player, {'data-url': "#player?songid=" + song});

    };
    
    var nextSong = function() {
	if (currentSong < playlist.length - 1) {
	    $.mobile.changePage("#player?songid=" + (playlist[currentSong + 1]));
	}
    }
    
    var prevSong = function() {
	if (currentSong > 0) {
	    $.mobile.changePage("#player?songid=" + (playlist[currentSong - 1]));
	} else {
	    $.mobile.changePage("#player?songid=" + (playlist[currentSong]));
	}
    }
    
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
			playSong(data.options.pageData.songid);
			break;
		    default:
			loadPage(type, data.options.dataUrl, options, info);
		}
		
            }
        }
    });
    
    $(document).bind("pagechange", function ( e, data ) {
	if ($.mobile.activePage.hasClass("player-page")) {
	    $(".player-page:not(#player)").not($.mobile.activePage).remove();
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
	    cssSelectorAncestor: ".player-page",
	    cssSelector: {
		"play": ".jp-play",
		"pause": ".jp-pause",
		"stop" : ".jp-stop",
		"videoPlay" : ".jp-video-play",
		"seekBar" : ".jp-seek-bar",
		"playBar" : ".jp-play-bar",
		"mute" : ".jp-mute",
		"unmute" : ".jp-unmute",
		"volumeBar" : ".jp-volume-bar",
		"volumeBarValue" : ".jp-volume-bar-value",
		"currentTime" : ".jp-current-time",
		"duration" : ".jp-duration" //"#play-time-total"
	    },
	    ended: nextSong
	});
	$(".big-cover").height($("body").width());
	$(".jp-next").click(function () {
	    nextSong();
	})
	$(".jp-prev").click(function () {
	    prevSong();
	})
    });
}());
