function (doc) {
    if (doc.type == 'song') {
        emit(doc.album_hash, {
            search_string: [doc.artist, doc.album, doc.title].join(';'),
            title: doc.album,
            artist_hash: doc.artist_hash
        });
    }
}
