function (doc) {
    if (doc.type == 'song') {
        emit(doc.artist_hash, {
            album_hash: doc.album_hash,
            album: doc.album
        });
    }
}
