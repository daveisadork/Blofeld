function (doc) {
    if (doc.type == 'song') {
        emit(doc.album_hash, {
            id: doc._id,
            artist: doc.artist,
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
            album_hash: doc.album_hash
        });
    }
}
