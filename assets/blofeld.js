var loadingImage = "<div class='scrollingContainer'><img src='assets/images/loading.gif' alt='loading...' class='loading'></div>";

var playSong = function (song) {
    $("#player").setFile('get_song?format=mp3&songid=' + song, 'get_song?format=ogg&songid=' + song).play();
    $('#cover_art').html('<a href="get_cover?size='+ Math.floor(document.body.clientHeight * 0.75) + '&songid=' + song + '"><img src="get_cover?size=32&songid=' + song + '" width="32" height="32"></a>')
    $('#cover_art > a').lightBox({imageLoading:'assets/images/loading.gif', songid:song});
    $('#np_title').html($('#' + song + ' .title').html())
    $('#np_artist').html($('#' + song + ' .artist').html())
    $('#np_album').html($('#' + song + ' .album').html())
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
        }
    )
}

var listSongs = function (artists, albums, query) {
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
            $('.song').unbind('dblclick');
            $('.song').dblclick(function () {
                playSong($(this).attr('id'))
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
        }
    )
}

var setupPlayer = function () {
    $("#player").jPlayer({
        ready: function () {
            return
        },
        swfPath: "assets"
    })
    .jPlayerId("play", "play")
    .jPlayerId("pause", "pause")
    .onProgressChange( function(loadPercent, playedPercentRelative, playedPercentAbsolute, playedTime, totalTime) {
        return
    })
    .onSoundComplete( function() {
        return
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
    $('#clear_search').click(function () {
        $('#query').val('');
        find();
    })
})


