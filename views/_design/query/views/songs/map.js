function (doc) {
    if (doc.type == 'song') {
        var artist, isvarious,
            various = ['various artists', 'various', 'va'];
        isvarious = various.indexOf(doc.albumartist.toLowerCase()) > -1;
        if (isvarious || doc.compilation) {
            artist = doc.artistsort;
        } else {
            artist = doc.albumartistsort;
        }
        query = [doc.artist, doc.album, doc.title].join(' ').toLowerCase();
        emit(
            [
                artist,
                doc.album,
                doc.date,
                doc.discnumber,
                doc.tracknumber,
                doc.titlesort
            ],
            {
                id: doc._id,
                artist: doc.artist,
                artistsort: doc.artistsort,
                album: doc.album,
                albumsort: doc.albumsort,
                albumartist: doc.albumartist,
                albumartistsort: doc.albumartistsort,
                tracknumber: doc.tracknumber,
                tracktotal: doc.tracktotal,
                totaltracks: doc.totaltracks,
                discnumber: doc.discnumber,
                disctotal: doc.disctotal,
                totaldiscs: doc.totaldiscs,
                title: doc.title,
                date: doc.date,
                year: doc.date.substring(0,4),
                duration: doc.length,
                length: doc.length,
                bitrate: doc.bitrate,
                genre: doc.genre,
                mimetype: doc.mimetype,
                query: query,
                compilation: doc.compilation,
                replaygain_track_gain: doc.replaygain_track_gain,
                replaygain_album_gain: doc.replaygain_album_gain,
                replaygain_track_peak: doc.replaygain_track_peak,
                replaygain_album_peak: doc.replaygain_album_peak
            }
        );
    }
}
