function (doc) {
    if (doc.type == 'song') {
        emit(doc.location, {
            'mtime': doc.mtime,
            '_rev': doc._rev
        });
    }
}
