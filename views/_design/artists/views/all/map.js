function (doc) {
    if (doc.type == 'song') {
        emit(doc.artist_hash, doc.artist);
    }
}
