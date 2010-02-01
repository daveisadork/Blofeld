function (doc) {
    if (doc.type == 'song') {
        emit(doc.album_hash, {
            title: doc.album,
            artist: doc.artist_hash
        });
    }
}
