function (doc) {
    if (doc.type == 'song') {
        emit([doc.artist, doc.album, doc.title], doc.artist_hash);
    }
}
