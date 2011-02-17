/* Author: Dave Hayes

*/
"use strict";
var contentLayouts = {}, layouts = {}, loadingSongs = '<div class="scrolling-container"><table id="songs"><thead class="ui-widget-header ui-corner-all"><tr class="song"><th class="status ui-corner-left"></th><th class="track-number">#</th><th class="title">Title</th><th class="artist">Artist</th><th class="album">Album</th><th class="genre">Genre</th><th class="year">Year</th><th class="time ui-corner-right">Time</th></tr></thead><tbody><tr class="song" id="Loading"><td class="status ui-corner-left" colspan="8"><div class="loading">Loading...</div></td></tr></tbody></table></div>',
    loadingArtists = '<div class="scrolling-container"><table id="artists"><tbody><tr class="artist ui-state-default" id="all-artists"><td class="ui-corner-all">All Artists (<span id="artist-count">Loading</span>)</td></tr></tbody></div>',
    loadingAlbums = '<div class="scrolling-container"><table id="albums"><tbody><tr class="album ui-state-default" id="all-albums"><td class="ui-corner-all">All Albums (<span id="album-count">Loading</span>)</td></tr></tbody></div>',
    playlist = [],
    seekPercent = 0,
    playingCurrently = null,
    bitrates = [48, 64, 96, 128, 160, 192, 256, 320],
    bitrate = 320,
    randomTrack = null,
    playerState = 'stopped',
    playerFormats = [],
    playerType = null,
    ajaxQueue = {
        'artists': null,
        'albums': null,
        'songs': null,
        'tags': null
    },
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
                    layouts['sources-pane'].sizePane('south', layouts['body'].state.west.size);
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
                    if (layouts['sources-pane'].state.south.size !== layouts['body'].state.west.size) {
                        layouts['sources-pane'].sizePane('south', layouts['body'].state.west.size);
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
    };

    
var showCover = function (song) {
    var offset = $('#cover-art').offset(),
        size = Math.floor($(document).height() * 0.85);
    $('.cover-img').toggleClass('active inactive');
    $('img.active').attr({
        //'src': 'get_cover?size=32&songid=' + song,
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
};

var playSong = function (songIndex) {
    var song = playlist[songIndex],
        songUrl, songUrlMp3, songUrlOga;
    $("#progress-bar").slider("disable");
    showInfo(song)
    songUrl = 'get_song?format=' + playerFormats.join(',') + '&songid=' + song + '&bitrate=' + parseInt(bitrate, 10);
    songUrlMp3 = 'get_song?format=mp3&songid=' + song + '&bitrate=' + parseInt(bitrate, 10);
    songUrlOga = 'get_song?format=oga&songid=' + song + '&bitrate=' + parseInt(bitrate, 10);
    playingCurrently = songIndex;
    $("#jplayer").jPlayer("setMedia", {
        mp3: songUrlMp3,
        oga: songUrlOga
    }).jPlayer("play");
    
    $.address.parameter('song', song);
    playerState = 'playing';
};

var showInfo = function(song) {
    showCover(song);
    $('#now-playing-title').html($('#' + song + ' .title').html());
    $('#now-playing-artist').html($('#' + song + ' .artist').html());
    $('#now-playing-album').html($('#' + song + ' .album').html());
    $('.now-playing > .status > .status-icon, .status > .ui-icon').removeClass('ui-icon ui-icon-volume-on ui-icon-volume-off');
    $('.now-playing').removeClass('now-playing');
    $('#' + song).addClass('now-playing');
    $('.now-playing > .status > .status-icon, .status > .ui-icon').addClass('ui-icon ui-icon-volume-on');
    $("#now-playing, #progress-bar, #play-time").show();
    $.address.title($('#now-playing-artist').html() + " - " + $('#now-playing-title').html());
    if (ajaxQueue.tags) {
        ajaxQueue.tags.abort();
    }
    ajaxQueue.tags = $.ajax({
        url: 'get_tags',
        data: {songid: song},
        success: function (response) {
            var tags = response.song
            ajaxQueue.tags = null;
            $('#now-playing-artist').click(function () {
                $.address.parameter('query', null).parameter('albums', null).parameter('artists', tags.artist_hash);
            });
            $('#now-playing-album').click(function () {
                $.address.parameter('artists', null).parameter('query', null).parameter('albums', tags.album_hash);
            });
        }
    });

    
};

var listArtists = function (query, highlight) {
    var offset, options = {
        'output': 'html'
    };
    if (ajaxQueue.artists) {
        ajaxQueue.artists.abort();
    }
    if (query) {
        options.query = query;
    }
    //    $("#artists-container").html(loadingArtists);
    $("#artists-container").addClass('ui-state-disabled');
    ajaxQueue.artists = $.ajax({
        url: 'list_artists',
        data: options,
        success: function (response) {
            $("#artists-container").html(response);
            $("#artist-count").html($("#artists .artist").not("#all-artists").size());
            ajaxQueue.artists = null;
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
            var selectedArtists = [];
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
        }
    });
};

var listAlbums = function (artists, query) {
    var options = {
        'output': 'html'
    };
    if (ajaxQueue.albums) {
        ajaxQueue.albums.abort();
    }
    if (query) {
        options.query = query;
    }
    if (artists) {
        options.artists = artists.join(',');
    }
    //    $("#albums-container").html(loadingAlbums);
    $('#albums-container').addClass("ui-state-disabled");
    ajaxQueue.albums = $.ajax({
        url: 'list_albums',
        data: options,
        success: function (response) {
            var selectedAlbums = [],
                selectedArtists = [],
                position, offset;
            $("#albums-container").html(response);
            $("#album-count").html($("#albums .album").not("#all-albums").size());
            ajaxQueue.albums = null;
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
        }
    });
};

var listSongs = function (artists, albums, query, play) {
    var options = {
        'output': 'html'
    };
    if (ajaxQueue.songs) {
        ajaxQueue.songs.abort();
    }
    if (query) {
        options.query = query;
    }
    if (artists) {
        options.artists = artists.join(',');
    }
    if (albums) {
        options.albums = albums.join(',');
    }
    //    $("#songs-container").html(loadingSongs);
    $("#songs-container").addClass('ui-state-disabled');
    ajaxQueue.songs = $.ajax({
        url: 'list_songs',
        data: options,
        success: function (response) {
            $("#songs-container").html(response);
            ajaxQueue.songs = null;
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
                helper: function (e,ui) {
                    return $('<div class="ui-icon ui-icon-document"></div>').appendTo('body').css('zIndex',5).show();
                } 
            });
            $("#songs").tablesorter({
                headers: { 0: { sorter: false}}
            }).bind("sortEnd",function() { 
                playlist = [];
                $('tbody tr.song').each(function (index) {
                    playlist.push($(this).attr('id'));
                });
                if (playingCurrently !== null) {
                    playingCurrently = $.inArray(state.activeSong, playlist);
                }
            });
            $("#songs-container").removeClass('ui-state-disabled');
        }
    });
};

var stopPlayback = function () {
    state.activeSong = null;
    playingCurrently = null;
    $("#jplayer").jPlayer("stop");
    $("#now-playing, #progress-bar, #play-time").hide();
    $('.now-playing > .status > .status-icon, .status > .ui-icon').removeClass('ui-icon ui-icon-volume-on ui-icon-volume-off');
    $('.now-playing').removeClass('now-playing');
    playerState = 'stopped';
    $.address.parameter('song', null);
    $.address.title("Blofeld");
};

var playNextSong = function () {
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
};

var setupPlayer = function () {
    $("#jplayer").bind($.jPlayer.event.error, function (event) {
        $("#jplayer-inspector").append('<li class="jp-error">' + event.jPlayer.error.message + '</li>');
    }).bind($.jPlayer.event.warning, function (event) {
        $("#jplayer-inspector").append('<li class="jp-warning">' + event.jPlayer.warning.message + '</li>');
    }).jPlayer({
        swfPath: "static/images",
        //errorAlerts: true,
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
            "duration" : "#play-time-total"
        },
        ready: function (event) {
            $("#jplayer-inspector").append('<li class="jp-info">Flash: ' + JSON.stringify(event.jPlayer.flash) + '</li>');
            $("#jplayer-inspector").append('<li class="jp-info">HTML: ' + JSON.stringify(event.jPlayer.html) + '</li>');
            $(this).bind($.jPlayer.event.timeupdate, function (event) {
                seekPercent = parseInt(event.jPlayer.status.seekPercent, 10);
                if (seekPercent > 0) {
                    if ($('#progress-bar').slider("option", "disabled")) {
                        $('#progress-bar').slider("enable");
                    }
                } else if (!$('#progress-bar').slider("option", "disabled")) {
                    $('#progress-bar').slider("disable");
                }
                $('#progress-bar').progressbar('option', 'value', seekPercent).slider('option', 'value', parseInt(event.jPlayer.status.currentPercentAbsolute, 10));
            });
            $.jPlayer.timeFormat.padMin = false;
        },
        ended:  playNextSong
    });
    playerFormats.push('mp3');
    
};

var disableSelection = function (target) {
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
};

var find = function () {
    $('#search-box').autocomplete("close");
    $.address.parameter('query', $('#search-box').val());
};

Array.prototype.compare = function (testArr) {
    if (this.length !== testArr.length) {
        return false;
    }
    for (var i = 0; i < testArr.length; i = i + 1) {
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
    if (!! $('#switcher').themeswitcher) {
        $('#switcher').themeswitcher();
    }

    // Create our paned layout
    layouts["body"] = $('body').layout(layoutOptions.body);
    layouts["sources-pane"] = $('#sources-pane').layout(layoutOptions["sources-pane"]);
    layouts['sources-pane'].sizePane('south', layouts['body'].state.west.size);
    $("tr.source").each(function () {
        name = $(this).attr("name");
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
    $("#content > div:not(#music-library)").hide()
    
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
        if (!! event.parameters.song) {
            song = event.parameters.song;
        }
        if (!! event.parameters.query) {
            query = event.parameters.query;
        }
        if (!! event.parameters.artists) {
            artists = event.parameters.artists.split(',');
        }
        if (!! event.parameters.albums) {
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
        var name = $(this).attr('name')
        $("#content > div").hide();
        $(".source.ui-state-default").removeClass('ui-state-default');
        $(this).addClass('ui-state-default');
        $("#" + name).show();
        contentLayouts[name].resizeAll();
    });
    $('tr.source[name="play-queue"]').droppable({
        drop: function( event, ui ) {
            $("#play-queue").append("<p>" + ui.draggable.attr('id') + "</p>");
        },
        accept: '.song',
        hoverClass: "ui-state-hover",
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
            $.address.title($('#now-playing-artist').html() + " - " + $('#now-playing-title').html());
        }
    });
    $("#pause-button").button({
        icons: {
            primary: 'ui-icon-pause'
        },
        text: false
    }).click(function () {
        $(".now-playing .ui-icon-volume-on").toggleClass("ui-icon-volume-on ui-icon-volume-off");
        $.address.title($('#now-playing-artist').html() + " - " + $('#now-playing-title').html() + " (Paused)");
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
    $('#shutdown-button').button({
        icons: {
            primary: 'ui-icon-power'
        }
    }).click(function () {
        $("#shutdown-dialog").dialog("open");
        if (ajaxQueue.artists) {
            ajaxQueue.artists.abort();
        }
        if (ajaxQueue.albums) {
            ajaxQueue.albums.abort();
        }
        if (ajaxQueue.artists) {
            ajaxQueue.songs.abort();
        }
        $.ajax({
            url: 'shutdown',
            success: function (response) {
                if (response.shutdown === true) {
                    $("#shutdown-dialog span").html("done.");
                }
            }
        });
    });
    $(".ui-layout-toggler").button();
    $("#shutdown-dialog").dialog({
        autoOpen: false,
        resizable: false,
        draggable: false,
        modal: true,
        
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
    $('#add-user-button').button({
        icons: {
            primary: 'ui-icon-plus'
        }
    }).click(function () {
        $("#add-user-dialog").dialog('open');
    });
    $("#add-user-dialog").dialog({
        autoOpen: false,
        resizable: false,
        title: 'Add User',
        buttons: {
            Cancel: function() {
                $( this ).dialog( "close" );
            },
            "Add User": function() {
                var bValid = true;
                allFields.removeClass( "ui-state-error" );

                bValid = bValid && checkLength( name, "username", 3, 16 );
                bValid = bValid && checkLength( email, "email", 6, 80 );
                bValid = bValid && checkLength( password, "password", 5, 16 );

                bValid = bValid && checkRegexp( name, /^[a-z]([0-9a-z_])+$/i, "Username may consist of a-z, 0-9, underscores, begin with a letter." );
                // From jquery.validate.js (by joern), contributed by Scott Gonzalez: http://projects.scottsplayground.com/email_address_validation/
                bValid = bValid && checkRegexp( email, /^((([a-z]|\d|[!#\$%&'\*\+\-\/=\?\^_`{\|}~]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])+(\.([a-z]|\d|[!#\$%&'\*\+\-\/=\?\^_`{\|}~]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])+)*)|((\x22)((((\x20|\x09)*(\x0d\x0a))?(\x20|\x09)+)?(([\x01-\x08\x0b\x0c\x0e-\x1f\x7f]|\x21|[\x23-\x5b]|[\x5d-\x7e]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(\\([\x01-\x09\x0b\x0c\x0d-\x7f]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]))))*(((\x20|\x09)*(\x0d\x0a))?(\x20|\x09)+)?(\x22)))@((([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))\.)+(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))\.?$/i, "eg. ui@jquery.com" );
                bValid = bValid && checkRegexp( password, /^([0-9a-zA-Z])+$/, "Password field only allow : a-z 0-9" );
            }            
        },
        close: function() {
            allFields.val( "" ).removeClass( "ui-state-error" );
        },
        open: function (event, ui) {
            $('#add-user-dialog').dialog({
                width: '300',
                position: 'center'
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
            artistsChanged, albumsChanged, queryChanged, songChanged;
        if (!! event.parameters.song) {
            song = event.parameters.song;
        }
        if (!! event.parameters.query) {
            query = event.parameters.query;
        }
        if (!! event.parameters.artists) {
            artists = event.parameters.artists.split(',');
        }
        if (!! event.parameters.albums) {
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
        if (!! event.parameters.song) {
            song = event.parameters.song;
        }
        if (!! event.parameters.query) {
            query = event.parameters.query;
        }
        if (!! event.parameters.artists) {
            artists = event.parameters.artists.split(',');
        }
        if (!! event.parameters.albums) {
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
