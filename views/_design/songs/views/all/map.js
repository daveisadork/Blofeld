function (doc) {
    if (doc.type == 'song') {
        emit([doc.artist, doc.album, doc.tracknumber, doc.title], {
            id: doc._id,
            artist: doc.artist,
            album: doc.album,
            tracknumber: doc.tracknumber,
            title: doc.title,
            genre: doc.genre,
            artist_hash: doc.artist_hash,
            album_hash: doc.album_hash
        });
    }
}
