var loadingImage = "<div class='scrollingContainer'><img src='static/images/loading.gif' alt='loading...' class='loading'></div>";
var playlist = []
var playingCurrently = null

var playSong = function (songIndex) {
    song = playlist[songIndex];
    playingCurrently = songIndex;
    $("#player").setFile('get_song?format=mp3&songid=' + song, 'get_song?format=ogg&songid=' + song);
    $('#cover_art').html('<a href="get_cover?size='+ Math.floor(document.body.clientHeight * 0.75) + '&songid=' + song + '"><img src="get_cover?size=32&songid=' + song + '" width="32" height="32"></a>')
    $('#cover_art > a').lightBox({imageLoading:'assets/images/loading.gif', songid:song});
    $('#np_title').html($('#' + song + ' .title').html())
    $('#np_artist').html($('#' + song + ' .artist').html())
    $('#np_album').html($('#' + song + ' .album').html())
    $('#player').play();
    $("#now_playing").show();
    $("#progress").show();
}

var listArtists = function (query) {
    options = {'output': 'html'}
    if (query) {
        options['query'] = query
    }
    $("#artistsContainer").html(loadingImage).load(
        'list_artists',
        options, 
        function () {
            $("#artists").tablesorter({
                sortForce: [[0,0]],
                sortList: [[0,0]]
            }); 
            $('.artist').unbind('click');
            $('.artist').click(function (event) {
                if (!event.ctrlKey) {
                    $('.artist.selected').removeClass('selected')
                }
                if ($(this).hasClass('selected')) {
                    $(this).removeClass('selected')
                } else {
                    $(this).addClass('selected')
                }
                var selectedArtists = []
                $('.artist.selected').each(function () {
                    selectedArtists.push($(this).attr('id'))
                })
                listAlbums(selectedArtists, $('#query').val())
                listSongs(selectedArtists, null, $('#query').val())
            })
        }
    )
}

var listAlbums = function (artists, query) {
    options = {'output': 'html'}
    if (query) {
        options['query'] = query
    }
    if (artists) {
        options['artists'] = artists.join(',')
    }
    $("#albumsContainer").html(loadingImage).load(
        'list_albums', 
        options,
        function () {
            $("#albums").tablesorter({
                sortForce: [[0,0]],
                sortList: [[0,0]]
            })
            $('.album').unbind('click');
            $('.album').click(function (event) {
                if (!event.ctrlKey) {
                    $('.album.selected').removeClass('selected')
                }
                if ($(this).hasClass('selected')) {
                    $(this).removeClass('selected')
                } else {
                    $(this).addClass('selected')
                }
                var selectedAlbums = []
                $('.album.selected').each(function () {
                    selectedAlbums.push($(this).attr('id'))
                })
                listSongs(artists, selectedAlbums, $('#query').val())
            })
            $('.album').dblclick(function () {
                listSongs(artists, selectedAlbums, $('#query').val(), true)
            })
        }
    )
}

var listSongs = function (artists, albums, query, play) {
    options = {'output': 'html'}
    if (query) {
        options['query'] = query
    }
    if (artists) {
        options['artists'] = artists.join(',')
    }
    if (albums) {
        options['albums'] = albums.join(',')
    }
    $("#songsContainer").html(loadingImage).load(
        'list_songs',
        options, 
        function () {
            $("#songs").tablesorter({
                sortForce: [[3,0], [4,0], [0,0]],
                sortList: [[3,0], [4,0], [0,0]]
            }); 
            $("#songs tr:odd").addClass('tinted')
            playlist = []
            playingCurrently = null
            $('.song').each(function (index) {
                playlist.push($(this).attr('id'))
            })
            $('.song').unbind('dblclick');
            $('.song').dblclick(function () {
                playSong(playlist.indexOf($(this).attr('id')))
            })
            $('.song').unbind('click');
            $('.song').click(function (event) {
                if (!event.ctrlKey) {
                    $('.song.selected').removeClass('selected')
                }
                if ($(this).hasClass('selected')) {
                    $(this).removeClass('selected')
                } else {
                    $(this).addClass('selected')
                }
            })
            if (play) {
                playSong(0)
            }
        }
    )
}

var playNextSong = function () {
    if (playingCurrently != null) {
        if (playingCurrently < playlist.length - 1) {
            playSong(playingCurrently + 1);
        } else {
            stopPlayback();
        }
    } else {
        playSong(0);
    }
}

var stopPlayback = function () {
    $("#player").stop();
    $("#now_playing").hide();
    $("#progress").hide();
}


var setupPlayer = function () {
    $("#player").jPlayer({
        ready: function () {
            return
        },
        swfPath: "static/images",
        //oggSupport: true
    })
    .jPlayerId("play", "play")
    .jPlayerId("pause", "pause")
    .onProgressChange( function(loadPercent, playedPercentRelative, playedPercentAbsolute, playedTime, totalTime) {
        $('#load_progress').width(loadPercent)
        $('#play_head').width(playedPercentRelative)
//        var myPlayedTime = new Date(playedTime);
//        var ptMin = (myPlayedTime.getUTCMinutes() < 10) ? "0" + myPlayedTime.getUTCMinutes() : myPlayedTime.getUTCMinutes();
//        var ptSec = (myPlayedTime.getUTCSeconds() < 10) ? "0" + myPlayedTime.getUTCSeconds() : myPlayedTime.getUTCSeconds();
//        var myTotalTime = new Date(totalTime);
//        var ttMin = (myTotalTime.getUTCMinutes() < 10) ? "0" + myTotalTime.getUTCMinutes() : myTotalTime.getUTCMinutes();
//        var ttSec = (myTotalTime.getUTCSeconds() < 10) ? "0" + myTotalTime.getUTCSeconds() : myTotalTime.getUTCSeconds();
//        $('#play_head').text(ptMin+":"+ptSec+" of "+ttMin+":"+ttSec);
    })
    .onSoundComplete( function() {
        playNextSong();
    })
    $("#skip_forward").click(function () {
        playNextSong();
    })
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
    })
}

var disableSelection = function (target){
    if (typeof target.onselectstart!="undefined") //IE route
        target.onselectstart=function(){return false}
    else if (typeof target.style.MozUserSelect!="undefined") //Firefox route
        target.style.MozUserSelect="none"
    else //All other route (ie: Opera)
        target.onmousedown=function(){return false}
    target.style.cursor = "default"
}

var resizeInterface = function () {
    if (window.innerHeight) {
        $('#browser').height(window.innerHeight - 86);
    } else if (document.all) {
        $('#browser').height(document.body.clientHeight - 86);
    }
}

var find = function () {
    listSongs(null, null, $('#query').val())
    listAlbums(null, $('#query').val())
    listArtists($('#query').val())
}

$(document).ready(function() {
    $.ajaxSetup ({
        cache: true
    })
    setupPlayer();
    disableSelection(document.getElementById("browser"))
    listArtists();
    listAlbums();
    resizeInterface();
    window.onresize = resizeInterface();
    $('#clear_search').click(function () {
        $('#query').val('');
        find();
    })
    $("#now_playing").hide();
    $("#progress").hide();
})


