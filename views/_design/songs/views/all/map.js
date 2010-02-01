function (doc) {
    if (doc.type == 'song') {
        emit(null, {
            artist: doc.artist,
            album: doc.album,
            tracknumber: doc.tracknumber,
            genre: doc.genre,
            title: doc.title,
            location: doc.location,
            artist_hash: doc.artist_hash,
            album_hash: doc.album_hash,
            mtime: doc.mtime
        });
    }
}
