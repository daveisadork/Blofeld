function (doc) {
    if (doc.type == 'song') {
        emit(doc.location, doc.mtime);
    }
}
