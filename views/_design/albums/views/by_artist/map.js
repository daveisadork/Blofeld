function (doc) {
    if (doc.type == 'song') {
        emit(doc.album, {
            album_hash: doc.album_hash,
            artist: doc.artist_hash
        });
    }
}
