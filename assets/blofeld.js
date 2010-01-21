var loadingImage = "<div class='scrollingContainer'><img src='assets/images/loading.gif' alt='loading...' class='loading'></div>";


var playSong = function (song) {
    audioElement.setAttribute('src', 'get_song?songid=' + song);
    audioElement.setAttribute('controls', 'true');
    audioElement.load();
    audioElement.addEventListener("canplay", function () {
        audioElement.play()
    }, false);
}

var listArtists = function () {
    $("#artistsContainer").html(loadingImage).load(
        'list_artists',
        {'output': 'html'}, 
        function () {
            $("#artists").tablesorter({
                sortForce: [[0,0]],
                sortList: [[0,0]]
            }); 
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
                listAlbums(selectedArtists)
                listSongs(selectedArtists)
            })
        }
    )
}

var listAlbums = function (artists) {
    options = {'output': 'html'}
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
                listSongs(artists, selectedAlbums)
            })
        }
    )
}

var listSongs = function (artists, albums) {
    options = {'output': 'html'}
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
            $('.song').dblclick(function () {
                playSong($(this).attr('id'))
            })
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

var disableSelection = function (target){
    if (typeof target.onselectstart!="undefined") //IE route
        target.onselectstart=function(){return false}
    else if (typeof target.style.MozUserSelect!="undefined") //Firefox route
        target.style.MozUserSelect="none"
    else //All other route (ie: Opera)
        target.onmousedown=function(){return false}
    target.style.cursor = "default"
}

var setupPlayer = function () {
    audioElement = document.createElement('audio');
    $('#media-playback-pause').hide();
    audioElement.addEventListener('playing', function () {
        $('#media-playback-start').hide();
        $('#media-playback-pause').show();
    }, false)
    audioElement.addEventListener('pause', function () {
        $('#media-playback-pause').hide();
        $('#media-playback-start').show();
    }, false)
    $('#media-playback-pause').click(function () {
        audioElement.pause();
    })
    $('#media-playback-start').click(function () {
        audioElement.play();
    })
}

$(document).ready(function() {
    $.ajaxSetup ({
        cache: true
    })
    setupPlayer();
    disableSelection(document.getElementById("browser"))
    
    listArtists();
    listAlbums();

    
})


