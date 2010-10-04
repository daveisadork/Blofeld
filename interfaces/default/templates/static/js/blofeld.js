var mainLayout, browserLayout;
var global_loadPercent = 0;
var loadingSongs = '<div class="scrolling-container"><table id="songs"><thead class="ui-widget-header"><th class="ui-corner-all"><center>Loading...</center></th></tr></thead></table></div>';
var loadingArtists = '<div class="scrolling-container"><table id="artists"><tbody><tr class="artist ui-state-default" id="all-artists"><td class="ui-corner-all">All Artists (<span id="artist-count">Loading</span>)</td></tr></tbody></div>';
var loadingAlbums = '<div class="scrolling-container"><table id="albums"><tbody><tr class="album ui-state-default" id="all-albums"><td class="ui-corner-all">All Albums (<span id="album-count">Loading</span>)</td></tr></tbody></div>';
var state = {
    selectedAlbums: [],
    selectedArtists: [],
    activeSong: null
};
var playlist = [];
var playingCurrently = null;
var ajaxQueue = {'artists': null, 'albums': null, 'songs': null};
var bitrates = [48, 64, 96, 128, 160, 192, 256, 320];
var bitrate = 320;
var randomTrack = null;
var playerState = 'stopped';

function PageQuery(q) {
    if(q.length > 1) this.q = q.substring(1, q.length);
    else this.q = null;
    this.keyValuePairs = new Array();
    if(q) {
        for(var i=0; i < this.q.split("&").length; i++) {
            this.keyValuePairs[i] = this.q.split("&")[i];
        }
    }
    this.getKeyValuePairs = function() { return this.keyValuePairs; }
    this.getValue = function(s) {
        for(var j=0; j < this.keyValuePairs.length; j++) {
            if(this.keyValuePairs[j].split("=")[0] == s)
                return this.keyValuePairs[j].split("=")[1];
            }
        return false;
    }
    this.getParameters = function() {
        var a = new Array(this.getLength());
        for(var j=0; j < this.keyValuePairs.length; j++) {
            a[j] = this.keyValuePairs[j].split("=")[0];
        }
        return a;
    }
    this.getLength = function() { return this.keyValuePairs.length; } 
}





var trackState = function () {
    var stateArray = [];


    if ($('#search-box').val() !== '') {
        stateArray.push('query=' + $('#search-box').val());
    }
    if (state.selectedArtists.length > 0) {
        stateArray.push('artists=' + state.selectedArtists.join(','));
    }
    if (state.selectedAlbums.length > 0) {
        stateArray.push('albums=' + state.selectedAlbums.join(','));
    }
    if (playerState === 'playing') {
        stateArray.push('song=' + state.activeSong);
    }
    window.location.href = '#?' + stateArray.join('&')
};

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
    size = Math.floor($(document).height() * 0.85);
    $('#cover-art-dialog img').attr({
        src: 'get_cover?songid=' + state.activeSong + '&size=' + size
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
    state.activeSong = song;
    playerState = 'playing';
    trackState();
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
            if (state.selectedArtists.length > 0) {
                $("#all-artists").removeClass('ui-state-default');
                state.selectedArtists.forEach(function (artistHash) {
                    $('#' + artistHash).addClass('ui-state-default');
                });
            }
            state.selectedArtists = [];
            $('.artist.ui-state-default').not("#all-artists").each(function () {
                state.selectedArtists.push($(this).attr('id'));
            });
            var offset = $('.artist.ui-state-default').first().position().top - $('#artists-container').height() / 2;
            $('#artists-container div').scrollTop(offset);
            trackState();
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
            if (state.selectedAlbums.length > 0) {
                $("#all-albums").removeClass('ui-state-default');
                state.selectedAlbums.forEach(function (albumHash) {
                    $('#' + albumHash).addClass('ui-state-default');
                });
            }
            state.selectedAlbums = [];
            $('.album.ui-state-default').not("#all-albums").each(function () {
                state.selectedAlbums.push($(this).attr('id'));
            });
            var offset = $('.album.ui-state-default').first().position().top - $('#albums-container').height() / 2;
            $('#albums-container div').scrollTop(offset);
            trackState();
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
                playingCurrently = $.inArray(state.activeSong, playlist);
            }
            $('#' + state.activeSong).addClass('now-playing');
            if ($('#jplayer').jPlayer("getData", "diag.isPlaying")) {
                $('.now-playing > .status > .status-icon').addClass('ui-icon ui-icon-volume-on');
            } else {
                $('.now-playing > .status > .status-icon').addClass('ui-icon ui-icon-volume-off');
            }
            if (play) {
                setTimeout(function() {
                    playSong($.inArray(play, playlist));
                }, 3000);
            }
            $(".song").draggable({ helper: 'clone' });
            trackState();
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
    trackState();
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
    $('#search-box').autocomplete("close");
    listArtists($('#search-box').val());
    listAlbums(state.selectedArtists, $('#search-box').val());
    listSongs(state.selectedArtists, state.selectedAlbums, $('#search-box').val());
};

$(document).ready(function () {
    $('#switcher').themeswitcher();
    setupPlayer();
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

    disableSelection(document.getElementById("browser"));
    disableSelection(document.getElementById("songs-container"));
    disableSelection(document.getElementById("controls"));
    disableSelection(document.getElementById("progress"));
    disableSelection(document.getElementById("sidebar"));

    queryString = window.location.hash.substring(1);

    if (queryString !== '?') {
        var page = new PageQuery(queryString);
        var query = page.getValue('query');
        var artists = page.getValue('artists');
        var albums = page.getValue('albums');
        var song = page.getValue('song');

        if (query) {
            $('#search-box').val(query);
        }
        if (artists) {
            state.selectedArtists = artists.split(',');
        }
        listArtists($('#search-box').val());
        if (albums) {
            state.selectedAlbums = albums.split(',');
        }
        listAlbums(state.selectedArtists, $('#search-box').val());
        listSongs(state.selectedArtists, state.selectedAlbums, $('#search-box').val(), song);
    } else {
        listArtists($('#search-box').val());
        listAlbums(state.selectedArtists, $('#search-box').val());
        listSongs(state.selectedArtists, state.selectedAlbums, $('#search-box').val());
    }

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
        state.selectedArtists = [];
        $('.artist.ui-state-default').not("#all-artists").each(function () {
            state.selectedArtists.push($(this).attr('id'));
        });
        state.selectedAlbums = [];
        if ($(this).attr('id') == "all-albums") {
            $('.album.ui-state-default').removeClass('ui-state-default');
            $(this).addClass('ui-state-default');
            listSongs(state.selectedArtists, null, $('#search-box').val());
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
            state.selectedAlbums.push($(this).attr('id'));
        });
        listSongs(state.selectedArtists, state.selectedAlbums, $('#search-box').val());
    });
    $('tr.artist').live("mousedown", function (event) {
        state.selectedArtists = [];
        state.selectedAlbums = [];
        if ($(this).attr('id') == "all-artists") {
            $('.artist.ui-state-default').removeClass('ui-state-default');
            $(this).addClass('ui-state-default');
            listAlbums(state.selectedArtists, $('#search-box').val());
            listSongs(state.selectedArtists, null, $('#search-box').val());
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
            state.selectedArtists.push($(this).attr('id'));
        });
        listAlbums(state.selectedArtists, $('#search-box').val());
        listSongs(state.selectedArtists, null, $('#search-box').val());
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
        $("tbody .song").each(function () {
            downloadList.push($(this).attr('id'));
        });
        window.location.href = 'download?songs=' + downloadList.join(',');
    });
    $(".ui-layout-toggler").button();
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
    $("#cover-art > img").click(function () {
        $("#cover-art-dialog").dialog('open');
    });
    $("#search-box").autocomplete({
        source: 'suggest',
        select: function (event, ui) {
            $("#search-box").val(ui.item.value);
            find();
            return false;
        }
    });
    setTimeout(function () {
        $('#splash-background').fadeOut(1250);
        setTimeout(function () {
            $('#splash-text').fadeOut(2000);
        }, 1000);
    }, 2000);
    
});

