function (doc) {
    if (doc.type == 'song') {
        emit([doc.artist, doc.album, doc.tracknumber, doc.title], {
            id: doc._id,
            artist: doc.artist,
            albumartist: doc.albumartist,
            album: doc.album,
            tracknumber: doc.tracknumber,
            totaltracks: doc.totaltracks,
            discnumber: doc.discnumber,
            totaldiscs: doc.totaldiscs,
            title: doc.title,
            date: doc.date,
            length: doc.length,
            bitrate: doc.bitrate,
            genre: doc.genre,
            artist_hash: doc.artist_hash,
            album_hash: doc.album_hash,
            replaygain_track_gain: doc.replaygain_track_gain,
            replaygain_album_gain: doc.replaygain_album_gain,
            replaygain_track_peak: doc.replaygain_track_peak,
            replaygain_album_peak: doc.replaygain_album_peak
        });
    }
}
