function (doc) {
    if (doc.type == 'song') {
        emit(doc.album, doc.album_hash);
    }
}
