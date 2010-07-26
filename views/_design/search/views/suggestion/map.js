function (doc) {
    if (doc.type == 'song') {
        emit(doc.artist, null);
        emit(doc.album, null);
    }
}
