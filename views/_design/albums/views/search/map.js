function (doc) {
    if (doc.type == 'song') {
        emit(doc.artist_hash, {
            search_string: [doc.artist, doc.album, doc.title].join(';'),
            album: doc.album,
            album_hash: doc.album_hash
        });
    }
}
