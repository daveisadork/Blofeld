function (doc) {
    if (doc.type == 'song') {
        emit(doc.artist, doc.artist_hash);
    }
}
