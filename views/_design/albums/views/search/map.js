function (doc) {
    if (doc.type == 'song') {
        emit(doc.album, {
            search_string: [doc.artist, doc.album, doc.title].join(';'),
            artist_hash: doc.artist_hash,
            album_hash: doc.album_hash
        });
    }
}
