var mainLayout, browserLayout;
var global_loadPercent = 0;
var loadingSongs = '<div class="scrolling-container"><table id="songs"><thead class="ui-widget-header"><th class="ui-corner-all"><center>Loading...</center></th></tr></thead></table></div>';
var loadingArtists = '<div class="scrolling-container"><table id="artists"><tbody><tr class="artist ui-state-default" id="all-artists"><td class="ui-corner-all">All Artists (<span id="artist-count">Loading</span>)</td></tr></tbody></div>';
var loadingAlbums = '<div class="scrolling-container"><table id="albums"><tbody><tr class="album ui-state-default" id="all-albums"><td class="ui-corner-all">All Albums (<span id="album-count">Loading</span>)</td></tr></tbody></div>';
var playlist = [];
var selectedAlbums = [];
var selectedArtists = [];
var playingCurrently = null;
var activeSong = null;
var ajaxQueue = {'artists': null, 'albums': null, 'songs': null};
var bitrates = [48, 64, 96, 128, 160, 192, 256, 320];
var bitrate = 320;
var randomTrack = null;
var playerState = 'stopped';

var showCover = function (song) {
    var offset = $('#cover-art').offset();
    $('.cover-img').toggleClass('active inactive');
    $('img.active').attr({
        'src': 'get_cover?size=32&songid=' + song,
        'top': offset.top,
        'left': offset.left
    })
    .load(function () {
        $('img.active').fadeIn(1000, function () {
            $('img.inactive').hide();
        })
        .error(function () {
            $('img.inactive').fadeOut(1000);
        });
    });
    
};

var playSong = function (songIndex) {
    $("#progress-bar").slider("disable");
    var song = playlist[songIndex];
    playingCurrently = songIndex;
    $("#jplayer").jPlayer('setFile', 'get_song?format=mp3&songid=' + song + '&bitrate=' + parseInt(bitrate, 10), 'get_song?format=ogg&songid=' + song + '&bitrate=' + parseInt(bitrate, 10)).jPlayer("play");
    $('#now-playing-title').html($('#' + song + ' .title').html());
    $('#now-playing-artist').html($('#' + song + ' .artist').html());
    $('#now-playing-album').html($('#' + song + ' .album').html());
    $('.now-playing > .status > .status-icon, .status > .ui-icon').removeClass('ui-icon ui-icon-volume-on ui-icon-volume-off');
    $('.now-playing').removeClass('now-playing');
    $('#' + song).addClass('now-playing');
    $('.now-playing > .status > .status-icon, .status > .ui-icon').addClass('ui-icon ui-icon-volume-on');
    $("#now-playing, #progress-bar, #play-time").show();
    activeSong = song;
    playerState = 'playing';
    showCover(song);
};

var listArtists = function (query) {
    if (ajaxQueue.artists) {
        ajaxQueue.artists.abort();
    }
    var options = {'output': 'html'};
    if (query) {
        options.query = query;
    }
    $("#artists-container").html(loadingArtists);
    ajaxQueue.artists = $.ajax({
        url: 'list_artists',
        data: options, 
        success: function (response) {
            $("#artists-container").html(response);
            $("#artist-count").html($("#artists .artist").not("#all-artists").size());
            ajaxQueue.artists = null;
        }
    });
};

var listAlbums = function (artists, query) {
    if (ajaxQueue.albums) {
        ajaxQueue.albums.abort();
    }
    var options = {'output': 'html'};
    if (query) {
        options.query = query;
    }
    if (artists) {
        options.artists = artists.join(',');
    }
    $("#albums-container").html(loadingAlbums);
    ajaxQueue.albums = $.ajax({
        url: 'list_albums', 
        data: options,
        success: function (response) {
            $("#albums-container").html(response);
            $("#album-count").html($("#albums .album").not("#all-albums").size());
            ajaxQueue.albums = null;
        }
    });
};

var listSongs = function (artists, albums, query, play) {
    if (ajaxQueue.songs) {
        ajaxQueue.songs.abort();
    }
    var options = {'output': 'html'};
    if (!query && !artists && !albums) {
        
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
    $("#songs-container").html(loadingSongs);
    ajaxQueue.songs = $.ajax({
        url: 'list_songs',
        data: options, 
        success: function (response) {
            $("#songs-container").html(response);
            ajaxQueue.songs = null;
            playlist = [];
            $('.song').each(function (index) {
                playlist.push($(this).attr('id'));
            });
            if (playingCurrently !== null) {
                playingCurrently = $.inArray(activeSong, playlist);
            }
            $('#' + activeSong).addClass('now-playing');
            if ($('#jplayer').jPlayer("getData", "diag.isPlaying")) {
                $('.now-playing > .status > .status-icon').addClass('ui-icon ui-icon-volume-on');
            } else {
                $('.now-playing > .status > .status-icon').addClass('ui-icon ui-icon-volume-off');
            }
            if (play) {
                playSong(0);
            }
            $(".song").draggable({ helper: 'clone' });
        }
    });
};

var stopPlayback = function () {
    activeSong = null;
    playingCurrently = null;
    $("#jplayer").jPlayer("stop");
    $("#now-playing, #progress-bar, #play-time").hide();
    $('.now-playing > .status > .status-icon, .status > .ui-icon').removeClass('ui-icon ui-icon-volume-on ui-icon-volume-off');
    $('.now-playing').removeClass('now-playing');
    playerState = 'stopped';
};

var playNextSong = function () {
    if (playingCurrently !== null) {
        if ($('#repeat-button').is(':checked')) {
            if ($('#shuffle-button').is(':checked')) {
                if (playlist.length === 0) {
                    $('.song').each(function (index) {
                        playlist.push($(this).attr('id'));
                    });
                    playingCurrently = $.inArray(activeSong, playlist);
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
    $("#jplayer").jPlayer({
        ready: function () {
            return;
        },
        swfPath: "static/images",
        nativeSupport: false,
        customCssIds: true
        //oggSupport: true
    })
    .jPlayer("cssId", "play", "play-button")
    .jPlayer("cssId", "pause", "pause-button")
    .jPlayer("onProgressChange", function (loadPercent, playedPercentRelative, playedPercentAbsolute, playedTime, totalTime) {
        global_loadPercent = parseInt(loadPercent, 10);
        if (global_loadPercent > 0) {
            if ($('#progress-bar').slider("option", "disabled")) {
                $('#progress-bar').slider("enable");
            }
        } else if (!$('#progress-bar').slider("option", "disabled")) {
            $('#progress-bar').slider("disable");
        }
        $('#progress-bar').progressbar('option', 'value', global_loadPercent).slider('option', 'value', parseInt(playedPercentAbsolute, 10));
        $('#play-time-current').html($.jPlayer.convertTime(playedTime));
        $('#play-time-total').html($.jPlayer.convertTime(totalTime));
//        var myPlayedTime = new Date(playedTime);
//        var ptMin = (myPlayedTime.getUTCMinutes() < 10) ? "0" + myPlayedTime.getUTCMinutes() : myPlayedTime.getUTCMinutes();
//        var ptSec = (myPlayedTime.getUTCSeconds() < 10) ? "0" + myPlayedTime.getUTCSeconds() : myPlayedTime.getUTCSeconds();
//        var myTotalTime = new Date(totalTime);
//        var ttMin = (myTotalTime.getUTCMinutes() < 10) ? "0" + myTotalTime.getUTCMinutes() : myTotalTime.getUTCMinutes();
//        var ttSec = (myTotalTime.getUTCSeconds() < 10) ? "0" + myTotalTime.getUTCSeconds() : myTotalTime.getUTCSeconds();
//        $('#play_head').text(ptMin+":"+ptSec+" of "+ttMin+":"+ttSec);
    })
    .jPlayer("onSoundComplete", function () {
        playNextSong();
    });
    $("#next-button").click(function () {
        playNextSong();
    });
    $("#previous-button").click(function () {
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
    $.jPlayer.timeFormat.padMin = false;
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
    listSongs(null, null, $('#search-box').val());
    listAlbums(null, $('#search-box').val());
    listArtists($('#search-box').val());
};

$(document).ready(function () {
    $('#switcher').themeswitcher();
    mainLayout = $('body').layout({
        center__paneSelector:   "#songs-container",
        west__onresize:         "browserLayout.resizeAll",
        north__paneSelector:    "#header",
        north__resizable:       false,
        north__size:            'auto',
        north__closable:        false,
        south__paneSelector:    "#footer",
        south__closable:        true,
        south__resizable:       false,
        south__initClosed:      true,
        south__size:            'auto',
        east__paneSelector:     '#sidebar',
        east__slidable:         false,
        east__initClosed:       true,
        west__paneSelector:     "#browser",
        west__closable:         false,
        west__slidable:         false
    });
    
    browserLayout = $('#browser').layout({
        minSize:                100,
        center__paneSelector:   "#albums-container",
        north__paneSelector:    "#artists-container",
        north__size:            250,
        north__resizable:       true,
        north__closable:        false
    });

    setupPlayer();
    disableSelection(document.getElementById("browser"));
    disableSelection(document.getElementById("songs-container"));
    disableSelection(document.getElementById("controls"));
    disableSelection(document.getElementById("progress"));
    disableSelection(document.getElementById("sidebar"));

    listArtists();
    listAlbums();
    listSongs();

    $('#clear-search').click(function () {
        $('#search-box').val('');
        find();
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
    $('tr.song').live("mousedown", function (event) {
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
        selectedArtists = [];
        $('.artist.ui-state-default').not("#all-artists").each(function () {
            selectedArtists.push($(this).attr('id'));
        });
        selectedAlbums = [];
        if ($(this).attr('id') == "all-albums") {
            $('.album.ui-state-default').removeClass('ui-state-default');
            $(this).addClass('ui-state-default');
            listSongs(selectedArtists, null, $('#search-box').val());
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
        listSongs(selectedArtists, selectedAlbums, $('#search-box').val());
    });
    $('tr.artist').live("mousedown", function (event) {
        selectedArtists = [];
        selectedAlbums = [];
        if ($(this).attr('id') == "all-artists") {
            $('.artist.ui-state-default').removeClass('ui-state-default');
            $(this).addClass('ui-state-default');
            listAlbums(selectedArtists, $('#search-box').val());
            listSongs(selectedArtists, null, $('#search-box').val());
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
        listAlbums(selectedArtists, $('#search-box').val());
        listSongs(selectedArtists, null, $('#search-box').val());
    });
    $("#previous-button").button({
        icons: {
            primary: 'ui-icon-seek-first'
        },
        text: false
    });

    $("#progress-bar").progressbar().slider({
        max: 100,
        animate: true,
        disabled: true,
        slide: function (event, ui) {
            if (global_loadPercent > 0) {
                $("#jplayer").jPlayer("playHead", ui.value * (100.0 / global_loadPercent));
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
            playingCurrently = $.inArray(activeSong, playlist);
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
        }
    });
    $("#pause-button").button({
        icons: {
            primary: 'ui-icon-pause'
        },
        text: false
    }).click(function () {
        $(".now-playing .ui-icon-volume-on").toggleClass("ui-icon-volume-on ui-icon-volume-off");
    });
    $("#next-button").button({
        icons: {
            primary: 'ui-icon-seek-end'
        },
        text: false
    });
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
        $(".song").each(function () {
            downloadList.push($(this).attr('id'));
        });
        window.location.href = 'download?songs=' + downloadList.join(',');
    });
    $(".ui-layout-toggler").button();
    $("#cover-art-dialog img").hide()
    $("#cover-art-dialog").dialog({
        autoOpen: false,
        resizable: false,
        open: function (event, ui) {
            size = Math.floor($(document).height() * 0.85);
            $('#cover-art-dialog div').width(size).height(size);
            $('#cover-art-dialog img').attr({
                src: 'get_cover?songid=' + activeSong + '&size=' + size,
                width: size,
                height: size
            }).load(function () {
                $("#cover-art-dialog span").hide();
                $("#cover-art-dialog img").fadeIn(1000);
            });
            $('#cover-art-dialog').dialog({
                width: 'auto',
                height: 'auto',
                position: 'top',
                title: $('#' + activeSong + ' .artist').html() + ' - ' + $('#' + activeSong + ' .album').html()
            });
        },
        close: function (event, ui) {
            $('#cover-art-dialog img').hide();
            $('#cover-art-dialog span').show();
        }
    });
    $("#cover-art > img").click(function () {
        $("#cover-art-dialog").dialog('open');
    });
    $("#search-box").autocomplete({
        source: 'suggest'
    });
    setTimeout(function () {
        $('#splash-background').fadeOut(1250);
        setTimeout(function () {
            $('#splash-text').fadeOut(3000);
        }, 1000);
    }, 2000);
});

