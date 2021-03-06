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
    var contentLayouts = {},
        layouts = {},
        playlist = [],
        seekPercent = 0,
        playingCurrently = null,
        bitrates = [48, 64, 96, 128, 160, 192, 256, 320],
        bitrate = 320,
        randomTrack = null,
        playerState = 'stopped',
        formats = {html: [], flash: []},
        solutions = ["flash", "html"],
        activeSolution = null,
        state = {
            selectedAlbums: [],
            selectedArtists: [],
            activeSong: null,
            currentSearch: null,
            previousSong: null
        },
        layoutOptions = {
            body: {
                north: {
                    paneSelector: "#header",
                    resizable: false,
                    size: 'auto',
                    closable: false
                },
                east: {
                    paneSelector: '#actions',
                    slidable: false,
                    initClosed: true
                },
                south: {
                    paneSelector: "#footer",
                    closable: true,
                    resizable: false,
                    initClosed: true,
                    size: 'auto'
                },
                west: {
                    paneSelector: "#sources-pane",
                    closable: false,
                    size: '200',
                    slidable: false,
                    onresize: function (event) {
                        layouts['sources-pane'].resizeAll();
                        layouts['sources-pane'].sizePane('south', layouts.body.state.west.size);
                    }
                },
                center: {
                    onresize: function (event) {
                        contentLayouts[$(".content-pane:visible").attr("id")].resizeAll();
                    }
                }
            },
            'sources-pane': {
                minSize: 100,
                center: {
                    paneSelector: "#source-list"
                },
                south: {
                    paneSelector: "#cover-art-pane",
                    closable: false,
                    // size: layouts['body'].state.west.size,
                    spacing_closed: 0,
                    onresize: function (event) {
                        if (layouts['sources-pane'].state.south.size !== layouts.body.state.west.size) {
                            layouts['sources-pane'].sizePane('south', layouts.body.state.west.size);
                        }
                    }
                }
            },
            'music-library': {
                center: {
                    paneSelector: "#songs-container"
                },
                west: {
                    paneSelector: "#artist-album-lists",
                    closable: false,
                    onresize: function (event) {
                        layouts['artist-album-lists'].resizeAll();
                    }
                }
            },
            'artist-album-lists': {
                minSize: 100,
                center: {
                    paneSelector: "#albums-container"
                },
                north: {
                    paneSelector: "#artists-container",
                    size: 250,
                    resizable: true,
                    closable: false
                }
            }
        },

        showCover = function (song) {
            var offset = $('#cover-art').offset(),
                size = Math.floor($(document).height() * 0.85);
            $('.cover-img').toggleClass('active inactive');
            $('img.active').attr({
                'src': 'get_cover?size=' + size + '&songid=' + song,
                'top': offset.top,
                'left': offset.left
            }).load(function () {
                $('img.active').fadeIn(1000, function () {
                    $('img.inactive').hide();
                }).error(function () {
                    $('img.inactive').fadeOut(1000);
                });
            });
            $('#cover-art-dialog img').attr({
                src: 'get_cover?songid=' + song + '&size=' + size
            });
        },

        showInfo = function (song) {
            showCover(song);
            $("#play-time-total").html($("#" + song + " .time").html());
            $('#now-playing-title').html($('#' + song + ' .title').html());
            $('#now-playing-artist').html($('#' + song + ' .artist').html());
            $('#now-playing-album').html($('#' + song + ' .album').html());
            $('.now-playing > .status > .status-icon, .status > .ui-icon').removeClass('ui-icon ui-icon-volume-on ui-icon-volume-off');
            $('.now-playing').removeClass('now-playing');
            $('#' + song).addClass('now-playing');
            $('.now-playing > .status > .status-icon, .status > .ui-icon').addClass('ui-icon ui-icon-volume-on');
            $("#now-playing, #progress-bar, #play-time").show();
            $.address.title($('#now-playing-artist').text() + " - " + $('#now-playing-title').text());
            $.fn.blofeld("getTags", {songid: song}, function (tags) {
                $('#now-playing-artist').click(function () {
                    $.address.parameter('query', null).parameter('albums', null).parameter('artists', tags.artist_hash);
                });
                $('#now-playing-album').click(function () {
                    $.address.parameter('artists', null).parameter('query', null).parameter('albums', tags.album_hash);
                });
            });
        },

        playSong = function (songIndex) {
            var song = playlist[songIndex],
                songUrl, db, gain, gainType, gainClass;
            $("#progress-bar").slider("disable");
            showInfo(song);
            songUrl = $.fn.blofeld("getSongURL", {
                songid: song,
                format: formats[activeSolution],
                bitrate: bitrate
            });
            if ($('#enable-replaygain').is(':checked')) {
                gainType = $('input[name="replaygain"]:checked').val();
                gainClass = ' .replaygain_' + gainType + '_gain';
                db = parseFloat($('#' + song + gainClass).text());
                gain = Math.pow(10,db/20);
                console.log('Gain type: ' + gainType + ', value: ' + gain);
            } else {
                console.log('Ignoring ReplayGain, gain: 1');
                gain = 1;
            }
            playingCurrently = songIndex;
            $("#jplayer").jPlayer("setMedia", {
                mp3: songUrl,
                oga: songUrl
            })
            .jPlayer("volume", gain)
            .jPlayer("play");
            
            $.address.parameter('song', song);
            playerState = 'playing';
        },

        listArtists = function (query, highlight) {
            $("#artists-container").addClass('ui-state-disabled')
                .blofeld("listArtists", {
                    query: query
                }, function () {
                    $("#artist-count").html($("#artists .artist").not("#all-artists").size());
                    var offset, selectedArtists = [];
                    if (highlight) {
                        state.selectedArtists = highlight;
                    }
                    if (state.selectedArtists.length > 0) {
                        $(".artist").removeClass('ui-state-default');
                        state.selectedArtists.forEach(function (artistHash) {
                            $('#' + artistHash).addClass('ui-state-default');
                        });
                    } else {
                        $('#all-artists').addClass('ui-state-default');
                    }
                    $('.artist.ui-state-default').not("#all-artists").each(function () {
                        selectedArtists.push($(this).attr('id'));
                    });
                    if (selectedArtists.length === 0) {
                        $('#all-artists').addClass('ui-state-default');
                    }
                    state.selectedArtists = selectedArtists;
                    if (state.selectedArtists.length > 0) {
                        $.address.parameter('artists', state.selectedArtists);
                    } else {
                        $.address.parameter('artists', null);
                    }
                    offset = $('.artist.ui-state-default').first().position().top - $('#artists-container').height() / 2;
                    $('#artists-container div').scrollTop(offset);
                    $("#artists-container").removeClass('ui-state-disabled');
                });
        },

        listAlbums = function (artists, query) {
            $('#albums-container').addClass("ui-state-disabled")
                .blofeld("listAlbums", {
                    artists: artists,
                    query: query
                }, function () {
                    var selectedAlbums = [],
                        selectedArtists = [],
                        position,
                        offset;
                    $("#album-count").html($("#albums .album").not("#all-albums").size());
                    if (state.selectedAlbums.length > 0) {
                        $("#all-albums").removeClass('ui-state-default');
                        state.selectedAlbums.forEach(function (albumHash) {
                            $('#' + albumHash).addClass('ui-state-default');
                        });
                    }
                    $('.album.ui-state-default').not("#all-albums").each(function () {
                        selectedAlbums.push($(this).attr('id'));
                    });
                    if (selectedAlbums.length > 0) {
                        $.address.parameter('albums', selectedAlbums);
                    } else {
                        $("#all-albums").addClass('ui-state-default');
                        $.address.parameter('albums', null);
                    }
                    $('.artist.ui-state-default').not("#all-artists").each(function () {
                        selectedArtists.push($(this).attr('id'));
                    });
                    state.selectedArtists = selectedArtists;
                    position = $('.album.ui-state-default').first().position();
                    if (position) {
                        offset = position.top - $('#albums-container').height() / 2;
                        $('#albums-container div').scrollTop(offset);
                        $('#albums-container').removeClass("ui-state-disabled");
                    }
                });
        },

        listSongs = function (artists, albums, query, play) {
            $("#songs-container").addClass('ui-state-disabled')
                .blofeld("listSongs", {
                    artists: artists,
                    albums: albums,
                    query: query
                }, function () {
                    playlist = [];
                    $('tbody tr.song').each(function (index) {
                        playlist.push($(this).attr('id'));
                    });
                    if (playingCurrently !== null) {
                        playingCurrently = $.inArray(state.activeSong, playlist);
                    }
                    $('#' + state.activeSong).addClass('now-playing');
                    if ($('#jplayer').jPlayer("getData", "diag.isPlaying")) {
                        $('.now-playing > .status > .status-icon').addClass('ui-icon ui-icon-volume-on');
                    } else {
                        $('.now-playing > .status > .status-icon').addClass('ui-icon ui-icon-volume-off');
                        $.address.parameter('song', null);
                    }
                    if (play) {
                        setTimeout(function () {
                            playSong($.inArray(play, playlist));
                        }, 3000);
                    }
                    $(".song").draggable({
                        helper: function (e, ui) {
                            return $('<div class="ui-icon ui-icon-document"></div>').appendTo('body').css('zIndex', 5).show();
                        } 
                    });
                    $("#songs").tablesorter({
                        headers: { 0: { sorter: false}}
                    }).bind("sortEnd", function () { 
                        playlist = [];
                        $('tbody tr.song').each(function (index) {
                            playlist.push($(this).attr('id'));
                        });
                        if (playingCurrently !== null) {
                            playingCurrently = $.inArray(state.activeSong, playlist);
                        }
                    });
                    $('#songs-container').removeClass("ui-state-disabled");
                });
        },
        
        monitorLibraryUpdate = function (ticket) {
            if ($("#library-update-dialog").is(":visible")) {
                $.ajax({
                    url: 'update_library',
                    data: {'ticket': ticket},
                    timeout: 1000,
                    success: function (response) {
                        var progress = parseInt((response.processed_items / response.queued_items) * 100)
                        $("#library-update-status").text(response.status);
                        $("#library-update-current-item").text(response.current_item);
                        $("#library-update-removed-items").text(response.removed_items);
                        $("#library-update-new-items").text(response.new_items);
                        $("#library-update-changed-items").text(response.changed_items);
                        $("#library-update-unchanged-items").text(response.unchanged_items);
                        $("#library-update-elapsed-time").text(response.total_time);
                        $("#library-update-progress").progressbar({
                            value: progress 
                        });
                        if (response.status != 'Finished') {
                            setTimeout(function () {
                                monitorLibraryUpdate(ticket);
                                }, 250);
                        } else {
                            $("#library-update-progress").progressbar({
                                value: 100
                            });
                        }
                    },
                    error: function () {
                        setTimeount(function () {
                            monitorLibraryUpdate(ticket);
                        }, 1000);       
                    }
                });
            }
        },

        stopPlayback = function () {
            state.activeSong = null;
            playingCurrently = null;
            $("#jplayer").jPlayer("stop");
            $("#now-playing, #progress-bar, #play-time").hide();
            $('.now-playing > .status > .status-icon, .status > .ui-icon').removeClass('ui-icon ui-icon-volume-on ui-icon-volume-off');
            $('.now-playing').removeClass('now-playing');
            playerState = 'stopped';
            $.address.parameter('song', null);
            $.address.title("Blofeld");
        },

        playNextSong = function () {
            if (playingCurrently !== null) {
                if ($('#repeat-button').is(':checked')) {
                    if ($('#shuffle-button').is(':checked')) {
                        if (playlist.length === 0) {
                            $('.song').each(function (index) {
                                playlist.push($(this).attr('id'));
                            });
                            playingCurrently = $.inArray(state.activeSong, playlist);
                        }
                        randomTrack = Math.floor(Math.random() * playlist.length);
                        playSong(randomTrack);
                        playlist.splice(randomTrack, 1);
                    } else if (playingCurrently < playlist.length - 1) {
                        playSong(playingCurrently + 1);
                    } else {
                        playSong(0);
                    }
                } else if (playlist.length === 0) {
                    stopPlayback();
                } else if ($('#shuffle-button').is(':checked')) {
                    randomTrack = Math.floor(Math.random() * playlist.length);
                    playSong(randomTrack);
                    playlist.splice(randomTrack, 1);
                } else if (playingCurrently < playlist.length - 1) {
                    playSong(playingCurrently + 1);
                } else {
                    stopPlayback();
                }
            } else {
                playSong(0);
            }
        },

        setupPlayer = function () {
            var solution = "flash,html";
            if ($('#html5-audio').is(':checked')) {
                solution = "html,flash";
            }
            $("#jplayer").bind($.jPlayer.event.error, function (event) {
                $("#jplayer-inspector").append('<li class="jp-error">' + event.jPlayer.error.message + '</li>');
            }).bind($.jPlayer.event.warning, function (event) {
                $("#jplayer-inspector").append('<li class="jp-warning">' + event.jPlayer.warning.message + '</li>');
            }).jPlayer({
                swfPath: "static/images",
                //errorAlerts: true,
                volume: 1,
                solution: solution,
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
                },
                ready: function (event) {
                    var index;
                    $.jPlayer.timeFormat.padMin = false;
                    $("#jplayer-inspector").append('<li class="jp-info">Flash: ' + JSON.stringify(event.jPlayer.flash) + '</li>');
                    $("#jplayer-inspector").append('<li class="jp-info">HTML5: ' + JSON.stringify(event.jPlayer.html) + '</li>');
                    for (index = 0; index < solutions.length; index = index + 1) {
                        if (event.jPlayer[solutions[index]].canPlay.mp3) {
                            formats[solutions[index]].push('mp3');
                        }
                        if (event.jPlayer[solutions[index]].canPlay.oga) {
                            formats[solutions[index]].push('oga');
                        }
                        if (event.jPlayer[solutions[index]].used) {
                            activeSolution = solutions[index];
                        }
                        if (!!event.jPlayer[solutions[index]].audio) {
                            $("#jplayer-solutions ." + solutions[index] + " .available").html(JSON.stringify(event.jPlayer[solutions[index]].audio.available));
                        } else {
                            $("#jplayer-solutions ." + solutions[index] + " .available").html(JSON.stringify(event.jPlayer[solutions[index]].available));
                        }
                        $("#jplayer-solutions ." + solutions[index] + " .preferred").html(JSON.stringify(event.jPlayer[solutions[index]].desired));
                        $("#jplayer-solutions ." + solutions[index] + " .used").html(JSON.stringify(event.jPlayer[solutions[index]].used));
                        $("#jplayer-solutions ." + solutions[index] + " .formats").html(formats[solutions[index]].join(', '));
                    }
                },
                timeupdate: function (event) {
                    seekPercent = parseInt(event.jPlayer.status.seekPercent, 10);
                    if (seekPercent > 0) {
                        if ($('#progress-bar').slider("option", "disabled")) {
                            $('#progress-bar').slider("enable");
                        }
                    } else if (!$('#progress-bar').slider("option", "disabled")) {
                        $('#progress-bar').slider("disable");
                    }
                    $('#progress-bar').progressbar('option', 'value', seekPercent).slider('option', 'value', parseInt(event.jPlayer.status.currentPercentAbsolute, 10));
                },
                ended:  playNextSong
            });
        },

        rebuildPlayer = function () {
            $("#jplayer").jPlayer("destroy");
            formats = {html: [], flash: []};
            activeSolution = null;
            setupPlayer();
        },

        disableSelection = function (target) {
            if (typeof target.onselectstart !== "undefined") {
                target.onselectstart = function () {
                    return false;
                };
            } else if (typeof target.style.MozUserSelect !== "undefined") {
                target.style.MozUserSelect = "none";
            } else {
                target.onmousedown = function () {
                    return false;
                };
            }
            target.style.cursor = "default";
        },

        find = function () {
            $('#search-box').autocomplete("close");
            $.address.parameter('query', $('#search-box').val());
        };

    Array.prototype.compare = function (testArr) {
        var i;
        if (this.length !== testArr.length) {
            return false;
        }
        for (i = 0; i < testArr.length; i = i + 1) {
            if (this[i].compare) {
                if (!this[i].compare(testArr[i])) {
                    return false;
                }
            }
            if (this[i] !== testArr[i]) {
                return false;
            }
        }
        return true;
    };
    
    $(document).ready(function () {
        // Create the jQueryUI Theme Switcher widget
        if (!!$('#switcher').themeswitcher) {
            $('#switcher').themeswitcher();
        }
    
        // Create our paned layout
        layouts.body = $('body').layout(layoutOptions.body);
        layouts["sources-pane"] = $('#sources-pane').layout(layoutOptions["sources-pane"]);
        layouts['sources-pane'].sizePane('south', layouts.body.state.west.size);
        $("tr.source").each(function () {
            var name = $(this).attr("name");
            if (!layoutOptions[name]) {
                layoutOptions[name] = {
                    center: {
                        paneSelector: "#" + name + "-widget"
                    } 
                };
            }
            contentLayouts[name] = $('#' + name).layout(layoutOptions[name]);
        });
        layouts["artist-album-lists"] = $('#artist-album-lists').layout(layoutOptions["artist-album-lists"]);
        
        // Show only the default content pane
        $("#content > div:not(#music-library)").hide();
        
        // Set up jPlayer
        setupPlayer();
        
        // Disable text selection on elements where it would be annoying
        disableSelection(document.getElementById("sources-pane"));
        disableSelection(document.getElementById("content"));
        disableSelection(document.getElementById("controls"));
        disableSelection(document.getElementById("progress"));
        disableSelection(document.getElementById("actions"));
        $.address.init(function (event) {
            var song = null,
                query = '',
                artists = [],
                albums = [];
            if (!!event.parameters.song) {
                song = event.parameters.song;
            }
            if (!!event.parameters.query) {
                query = event.parameters.query;
            }
            if (!!event.parameters.artists) {
                artists = event.parameters.artists.split(',');
            }
            if (!!event.parameters.albums) {
                albums = event.parameters.albums.split(',');
            }
            //        state.selectedArtists = artists;
            //        state.selectedAlbums = albums;
            //        state.currentSearch = query;
            $('#search-box').val(query);
        });
        $('#clear-search').button({
            icons: {
                primary: 'ui-icon-circle-close'
            },
            text: false
        }).click(function () {
            $('#search-box').val('');
            $.address.parameter('query', null);
        });
        $("#now-playing, #progress-bar, #play-time, .cover-img").hide();
        $('tr.song').live("dblclick", function () {
            if ($('#shuffle-button').is(':checked')) {
                playlist = [];
                $('.song').each(function (index) {
                    playlist.push($(this).attr('id'));
                });
            }
            playSong($.inArray($(this).attr('id'), playlist));
        });
        $('tbody > tr.song').live("mousedown", function (event) {
            if (event.ctrlKey) {
                $(this).toggleClass('ui-state-default');
            } else if (event.shiftKey) {
                $(this).addClass('ui-state-default');
                $('.song.ui-state-default').first().nextUntil('#' + $('.song.ui-state-default').last().attr('id')).addClass('ui-state-default');
            } else {
                $('.song.ui-state-default').removeClass('ui-state-default');
                $(this).addClass('ui-state-default');
            }
        });
        $('tr.album').live("mousedown", function (event) {
            var selectedAlbums = [];
            if ($(this).attr('id') === "all-albums") {
                $('.album.ui-state-default').removeClass('ui-state-default');
                $(this).addClass('ui-state-default');
            } else if (event.ctrlKey) {
                $(this).toggleClass('ui-state-default');
            } else if (event.shiftKey) {
                $(this).addClass('ui-state-default');
                $('.album.ui-state-default').first().nextUntil('#' + $('.album.ui-state-default').last().attr('id')).addClass('ui-state-default');
            } else {
                $('.album.ui-state-default').removeClass('ui-state-default');
                $(this).addClass('ui-state-default');
            }
            $('.album.ui-state-default').not("#all-albums").each(function () {
                selectedAlbums.push($(this).attr('id'));
            });
            if (selectedAlbums.length > 0) {
                $.address.parameter('albums', selectedAlbums);
            } else {
                $.address.parameter('albums', null);
            }
        });
        $('tr.artist').live("mousedown", function (event) {
            var selectedArtists = [];
            if ($(this).attr('id') === "all-artists") {
                $('.artist.ui-state-default').removeClass('ui-state-default');
                $(this).addClass('ui-state-default');
            } else if (event.ctrlKey) {
                $(this).toggleClass('ui-state-default');
            } else if (event.shiftKey) {
                $(this).addClass('ui-state-default');
                $('.artist.ui-state-default').first().nextUntil('#' + $('.artist.ui-state-default').last().attr('id')).addClass('ui-state-default');
            } else {
                $('.artist.ui-state-default').removeClass('ui-state-default');
                $(this).addClass('ui-state-default');
            }
            $('.artist.ui-state-default').not("#all-artists").each(function () {
                selectedArtists.push($(this).attr('id'));
            });
            if (selectedArtists.length > 0) {
                $.address.parameter('artists', selectedArtists);
            } else {
                $.address.parameter('artists', null);
            }
        });
        $('tr.source').click(function (event) {
            var name = $(this).attr('name');
            $("#content > div").hide();
            $(".source.ui-state-default").removeClass('ui-state-default');
            $(this).addClass('ui-state-default');
            $("#" + name).show();
            contentLayouts[name].resizeAll();
        });
        $('tr.source[name="play-queue"]').droppable({
            drop: function (event, ui) {
                $("#play-queue").append("<p>" + ui.draggable.attr('id') + "</p>");
            },
            accept: '.song',
            hoverClass: "ui-state-hover"
        });
        $("#previous-button").button({
            icons: {
                primary: 'ui-icon-seek-first'
            },
            text: false
        }).click(function () {
            if (playingCurrently) {
                if (playingCurrently > 0) {
                    playSong(playingCurrently - 1);
                } else {
                    stopPlayback();
                }
            } else {
                stopPlayback();
            }
        });
        $("#progress-bar").progressbar().slider({
            max: 100,
            animate: true,
            disabled: true,
            slide: function (event, ui) {
                if (seekPercent > 0) {
                    $("#jplayer").jPlayer("playHead", ui.value * (100.0 / seekPercent));
                }
            }
        });
        $('#repeat-button').button({
            icons: {
                primary: 'ui-icon-refresh'
            },
            text: false
        });
        $('#shuffle-button').button({
            icons: {
                primary: 'ui-icon-shuffle'
            },
            text: false
        }).click(function () {
            if (!$('#shuffle-button').is(':checked')) {
                playlist = [];
                $('.song').each(function (index) {
                    playlist.push($(this).attr('id'));
                });
                playingCurrently = $.inArray(state.activeSong, playlist);
            }
        });
        $("#play-button").button({
            icons: {
                primary: 'ui-icon-play'
            },
            text: false
        }).click(function () {
            if (playerState === 'stopped') {
                if (playlist.length > 0) {
                    playSong($.inArray($('tr.song.ui-state-default').attr('id'), playlist));
                }
            } else {
                $(".now-playing .ui-icon-volume-off").toggleClass("ui-icon-volume-on ui-icon-volume-off");
                $.address.title($('#now-playing-artist').text() + " - " + $('#now-playing-title').text());
            }
        });
        $("#pause-button").button({
            icons: {
                primary: 'ui-icon-pause'
            },
            text: false
        }).click(function () {
            $(".now-playing .ui-icon-volume-on").toggleClass("ui-icon-volume-on ui-icon-volume-off");
            $.address.title($('#now-playing-artist').text() + " - " + $('#now-playing-title').text() + " (Paused)");
        });
        $("#next-button").button({
            icons: {
                primary: 'ui-icon-seek-end'
            },
            text: false
        }).click(playNextSong);
        $('#bitrate-slider').slider({
            value: 7,
            min: 0,
            max: 7,
            step: 1,
            slide: function (event, ui) {
                bitrate = bitrates[ui.value];
                $("#amount").html(bitrate);
            }
        });
        $('#download-button').button({
            icons: {
                primary: 'ui-icon-link'
            }
        }).click(function () {
            var downloadList = [];
            $("tbody .song").each(function () {
                downloadList.push($(this).attr('id'));
            });
            window.location = 'download?songs=' + downloadList.join(',');
        });
        $('#apply-player-prefs-button').button({
            icons: {
                primary: 'ui-icon-circle-check'
            }
        }).click(rebuildPlayer);
        $('#shutdown-button').button({
            icons: {
                primary: 'ui-icon-power'
            }
        }).click(function () {
            $("#shutdown-dialog").dialog("open");
            $.ajax({
                url: 'shutdown',
                success: function (response) {
                    if (response.shutdown === true) {
                        $("#shutdown-dialog span").html("done.");
                    }
                }
            });
        });
        $('#update-library-button').button({
            icons: {
                primary: 'ui-icon-arrowrefresh-1-e'
            }
        }).click(function () {
            $("#library-update-progress").progressbar({
                value: 0
            });
            $("#library-update-dialog").dialog("open");
            $.ajax({
                url: 'update_library',
                success: function (response) {
                    monitorLibraryUpdate(response.ticket);
                }
            });
        });
        $(".ui-layout-toggler").button();
        $("#shutdown-dialog").dialog({
            autoOpen: false,
            resizable: false,
            draggable: false,
            modal: true
        });
        $("#library-update-dialog").dialog({
            autoOpen: false,
            resizable: true,
            draggable: true,
            width: 500,
            modal: false
        });
        $("#library-update-progress").progressbar({
            value: 0
        });
        $("#cover-art-dialog").dialog({
            autoOpen: false,
            resizable: false,
            open: function (event, ui) {
                $('#cover-art-dialog').dialog({
                    width: 'auto',
                    position: 'center',
                    title: $('#now-playing-artist').html() + ' - ' + $('#now-playing-album').html()
                });
            }
        });
        $("#cover-art > img, #cover-art-pane > img").click(function () {
            $("#cover-art-dialog").dialog('open');
        });
        $("#search-box").autocomplete({
            source: 'suggest',
            select: function (event, ui) {
                $("#search-box").val(ui.item.value);
                find();
                return false;
            },
            open: function (event, ui) {
                $("ul.ui-autocomplete").removeClass('ui-corner-all').addClass('ui-corner-bottom');
                $("#search-box").removeClass('ui-corner-bottom');
            },
            close: function (event, ui) {
                $("#search-box").addClass('ui-corner-bottom');
            }
        }).keydown(function (event) {
            if (event.which === 13) {
                find();
            }
        });
        $.address.change(function (event) {
            var song = null,
                query = '',
                artists = [],
                albums = [],
                artistsChanged,
                albumsChanged,
                queryChanged,
                songChanged;
            if (!!event.parameters.song) {
                song = event.parameters.song;
            }
            if (!!event.parameters.query) {
                query = event.parameters.query;
            }
            if (!!event.parameters.artists) {
                artists = event.parameters.artists.split(',');
            }
            if (!!event.parameters.albums) {
                albums = event.parameters.albums.split(',');
            }
            artistsChanged = !artists.compare(state.selectedArtists);
            albumsChanged = !albums.compare(state.selectedAlbums);
            queryChanged = (query !== state.currentSearch);
            songChanged = (song !== state.activeSong);
            if (songChanged) {
                state.activeSong = song;
                if (!artistsChanged && !albumsChanged && !queryChanged) {
                    return;
                }
            }
            if (queryChanged) {
                state.currentSearch = query;
                listArtists(query, artists);
            }
            if ((artistsChanged && artists.length > 0 && !queryChanged) || (queryChanged && !query)) {
                state.selectedArtists = artists;
                listAlbums(artists, query);
            } else if ((artistsChanged && artists.length === 0 && !queryChanged) || (queryChanged && query)) {
                state.selectedArtists = artists;
                listAlbums(null, query);
            }
            if (((albumsChanged || artistsChanged) && albums.length > 0) || query !== state.previousSearch) {
                state.selectedArtists = artists;
                state.selectedAlbums = albums;
                listSongs(artists, albums, query);
            } else if (((albumsChanged || artistsChanged) && albums.length === 0) || queryChanged) {
                state.selectedArtists = artists;
                state.selectedAlbums = albums;
                listSongs(artists, null, query);
            }
            $(".artist").removeClass('ui-state-default');
            if (artists.length > 0) {
                artists.forEach(function (artistHash) {
                    $('#' + artistHash).addClass('ui-state-default');
                });
            } else {
                $('#all-artists').addClass('ui-state-default');
            }
            $(".album").removeClass('ui-state-default');
            if (albums.length > 0) {
                albums.forEach(function (albumHash) {
                    $('#' + albumHash).addClass('ui-state-default');
                });
            } else {
                $('#all-albums').addClass('ui-state-default');
            }
        });
        $.address.externalChange(function (event) {
            var song = null,
                query = '',
                artists = [],
                albums = [];
            if (!!event.parameters.song) {
                song = event.parameters.song;
            }
            if (!!event.parameters.query) {
                query = event.parameters.query;
            }
            if (!!event.parameters.artists) {
                artists = event.parameters.artists.split(',');
            }
            if (!!event.parameters.albums) {
                albums = event.parameters.albums.split(',');
            }
            $(".artist").removeClass('ui-state-default');
            if (artists.length > 0) {
                artists.forEach(function (artistHash) {
                    $('#' + artistHash).addClass('ui-state-default');
                });
            } else {
                $('#all-artists').addClass('ui-state-default');
            }
            $(".album").removeClass('ui-state-default');
            if (albums.length > 0) {
                albums.forEach(function (albumHash) {
                    $('#' + albumHash).addClass('ui-state-default');
                });
            } else {
                $('#all-albums').addClass('ui-state-default');
            }
        });
        setTimeout(function () {
            $('#splash-background').fadeOut(1250);
            setTimeout(function () {
                $('#splash-text').fadeOut(2000);
            }, 1000);
        }, 2000);
    });
}());
