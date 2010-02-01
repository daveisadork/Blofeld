function (doc) {
    if (doc.type == 'song') {
        emit(doc.album_hash, doc.album);
    }
}
