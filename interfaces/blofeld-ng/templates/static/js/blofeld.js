var mainLayout, browserLayout;
var global_loadPercent = 0;
var loadingImage = '<div class="scrollingContainer"><table id="artists"><thead class="ui-widget-header"><th class="ui-corner-all"><center>Loading...</center></th></tr></thead></table></div>';
var playlist = [];
var selectedAlbums = [];
var selectedArtists = [];
var playingCurrently = null;
var activeSong = null;
var ajaxQueue = {'artists': null, 'albums': null, 'songs': null};
var bitrates = [48, 64, 96, 128, 160, 192, 256, 320];
var bitrate = 320;
var randomTrack = null;

var playSong = function (songIndex) {
    $("#progress-bar").slider("disable");
    var song = playlist[songIndex];
    playingCurrently = songIndex;
    $("#player").jPlayer('setFile', 'get_song?format=mp3&songid=' + song + '&bitrate=' + parseInt(bitrate, 10), 'get_song?format=ogg&songid=' + song + '&bitrate=' + parseInt(bitrate, 10)).jPlayer("play");
    $('#cover_art').html('<img id="cover-img" "src="get_cover?size=32&songid=' + song + '" width="32" height="32">');
    $('#cover_link').hide();
    $('#np_title').html($('#' + song + ' .title').html());
    $('#np_artist').html($('#' + song + ' .artist').html());
    $('#np_album').html($('#' + song + ' .album').html());
    $('.now-playing > .status > .status-icon, .status > .ui-icon').removeClass('ui-icon ui-icon-volume-on ui-icon-volume-off');
    $('.now-playing').removeClass('now-playing');
    $('#' + song).addClass('now-playing');
    $('.now-playing > .status > .status-icon, .status > .ui-icon').addClass('ui-icon ui-icon-volume-on');
    $("#now_playing, #progress").show();
    activeSong = song;
};

var listArtists = function (query) {
    if (ajaxQueue.artists) {
        ajaxQueue.artists.abort();
    }
    var options = {'output': 'html'};
    if (query) {
        options.query = query;
    }
    $("#artistsContainer").html(loadingImage);
    ajaxQueue.artists = $.ajax({
        url: 'list_artists',
        data: options, 
        success: function (response) {
            $("#artistsContainer").html(response);
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
    $("#albumsContainer").html(loadingImage);
    ajaxQueue.albums = $.ajax({
        url: 'list_albums', 
        data: options,
        success: function (response) {
            $("#albumsContainer").html(response);
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
    $("#songsContainer").html(loadingImage);
    ajaxQueue.songs = $.ajax({
        url: 'list_songs',
        data: options, 
        success: function (response) {
            $("#songsContainer").html(response);
            ajaxQueue.songs = null;
            playlist = [];
            $('.song').each(function (index) {
                playlist.push($(this).attr('id'));
            });
            playingCurrently = playlist.indexOf(activeSong);
            $('#' + activeSong).addClass('now-playing');
            if ($('#player').jPlayer("getData", "diag.isPlaying")) {
                $('.now-playing > .status > .status-icon').addClass('ui-icon ui-icon-volume-on');
            } else {
                $('.now-playing > .status > .status-icon').addClass('ui-icon ui-icon-volume-off');
            }
            if (play) {
                playSong(0);
            }
        }
    });
};

var stopPlayback = function () {
    activeSong = null;
    $("#player").jPlayer("stop");
    $("#now_playing").hide();
    $("#progress").hide();
    $('.now-playing > .status > .status-icon, .status > .ui-icon').removeClass('ui-icon ui-icon-volume-on ui-icon-volume-off');
    $('.now-playing').removeClass('now-playing');
};

var playNextSong = function () {
    if (playingCurrently !== null) {
        if ($('#repeat-button:checked').val() !== null) {
            if ($('#shuffle-button:checked').val() !== null) {
                if (playlist.length === 0) {
                    $('.song').each(function (index) {
                        playlist.push($(this).attr('id'));
                    });
                    playingCurrently = playlist.indexOf(activeSong);
                }
                playlist.splice(playingCurrently, 1);
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
        } else if ($('#shuffle-button:checked').val() !== null) {
            playlist.splice(playingCurrently, 1);
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
    $("#player").jPlayer({
        ready: function () {
            return;
        },
        swfPath: "static/images",
        nativeSupport: false,
        customCssIds: true
        //oggSupport: true
    })
    .jPlayer("cssId", "play", "play")
    .jPlayer("cssId", "pause", "pause")
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
    $("#skip_forward").click(function () {
        playNextSong();
    });
    $("#skip_back").click(function () {
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
    listSongs(null, null, $('#query').val());
    listAlbums(null, $('#query').val());
    listArtists($('#query').val());
};

$(document).ready(function () {
    $('#switcher').themeswitcher();
    mainLayout = $('body').layout({
        center__paneSelector:   "#songsContainer",
        west__onresize:         "browserLayout.resizeAll",
        north__paneSelector:    "#header",
        north__resizable:       false,
        north__size:            'auto',
        south__paneSelector:    "#footer",
        south__closable:        true,
        south__resizable:       false,
        south__initClosed:      true,
        south__size:            'auto',
        east__paneSelector:     '#sidebar',
        east__closable:         true,
        east__initClosed:       true,
        west__paneSelector:     "#browser"
    });
    
    browserLayout = $('#browser').layout({
        minSize:                100,
        center__paneSelector:   "#albumsContainer",
        north__paneSelector:    "#artistsContainer",
        north__size:            250,
        north__resizable:       true,
        north__closable:        false
    });

    setupPlayer();
    disableSelection(document.getElementById("browser"));
    disableSelection(document.getElementById("songsContainer"));
    disableSelection(document.getElementById("progress-bar"));

    listArtists();
    listAlbums();
    listSongs();

    $('#clear-search').click(function () {
        $('#query').val('');
        find();
    });
    $("#now_playing").hide();
    $("#progress").hide();
    $('#songs .song').live("dblclick", function () {
        if ($('#shuffle-button:checked').val() !== null) {
            playlist = [];
            $('.song').each(function (index) {
                playlist.push($(this).attr('id'));
            });
        }
        playSong(playlist.indexOf($(this).attr('id')));
    });
    $('#songs .song').live("click", function (event) {
        if (!event.ctrlKey) {
            $('.song.ui-state-default').removeClass('ui-state-default');
        }
        $(this).toggleClass('ui-state-default');
    });
    $('#albums .album').live("click", function (event) {
        selectedArtists = [];
        $('.artist.ui-state-default').each(function () {
            selectedArtists.push($(this).attr('id'));
        });
        selectedAlbums = [];
        if (!event.ctrlKey) {
            $('.album.ui-state-default').removeClass('ui-state-default');
        }
        $(this).toggleClass('ui-state-default');
        
        $('.album.ui-state-default').each(function () {
            selectedAlbums.push($(this).attr('id'));
        });
        listSongs(selectedArtists, selectedAlbums, $('#query').val());
    });
    $('#artists .artist').live("click", function (event) {
        selectedArtists = [];
        if (!event.ctrlKey) {
            $('.artist.ui-state-default').removeClass('ui-state-default');
        }
        $(this).toggleClass('ui-state-default');
        $('.artist.ui-state-default').each(function () {
            selectedArtists.push($(this).attr('id'));
        });
        listAlbums(selectedArtists, $('#query').val());
        listSongs(selectedArtists, null, $('#query').val());
    });
    $("#skip_back").button({
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
                $("#player").jPlayer("playHead", ui.value * (100.0 / global_loadPercent));
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
        if ($('#shuffle-button:checked').val() === null) {
            playlist = [];
            $('.song').each(function (index) {
                playlist.push($(this).attr('id'));
            });
            playingCurrently = playlist.indexOf(activeSong);
        }
    });
    $("#play").button({
        icons: {
            primary: 'ui-icon-play'
        },
        text: false
    }).click(function () {
        $(".now-playing .ui-icon-volume-off").toggleClass("ui-icon-volume-on ui-icon-volume-off");
    });
    $("#pause").button({
        icons: {
            primary: 'ui-icon-pause'
        },
        text: false
    }).click(function () {
        $(".now-playing .ui-icon-volume-on").toggleClass("ui-icon-volume-on ui-icon-volume-off");
    });
    $("#skip_forward").button({
        icons: {
            primary: 'ui-icon-seek-end'
        },
        text: false
    });
    $('#bitrate').slider({
        value: 7,
        min: 0,
        max: 7,
        step: 1,
        slide: function (event, ui) {
            bitrate = bitrates[ui.value];
            $("#amount").html(bitrate);
            
        }
    });
    $('#options').button({
        icons: {
            primary: 'ui-icon-wrench'
        },
        text: false
    });
    $('#splash-bg, #splash-text').fadeOut();

});


