function (doc) {
    if (doc.type == 'song') {
        var artist, various = ['various artists', 'various', 'va'];
        if (various.indexOf(doc.albumartist.toLowerCase()) < 0 || doc.compilation) {
            artist = doc.artist;
        } else {
            artist = doc.albumartist;
        }
        query = [doc.artist, doc.album, doc.title].join(' ').toLowerCase();
        emit(
            [
                artist,
                doc.date,
                doc.album,
                doc.discnumber,
                doc.tracknumber,
                doc.title
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
                bitrate: doc.bitrate,
                genre: doc.genre,
                mimetype: doc.mimetype,
                query: query
                // replaygain_track_gain: doc.replaygain_track_gain,
                // replaygain_album_gain: doc.replaygain_album_gain,
                // replaygain_track_peak: doc.replaygain_track_peak,
                // replaygain_album_peak: doc.replaygain_album_peak
            }
        );
    }
}
