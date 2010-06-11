$(document).ready(function () {
    var mainLayout, browserLayout, filterLayout;
//    
//    $('.ui-artists').load('artists.html', function () {
//        var artistTable = $('#artists').dataTable({
//            bFilter: false,
//            bPaginate: false,
//            bLengthChange: false,
//            bSort: false,
//            bInfo: false,
//            bJQueryUI: true,
//        });
//        new FixedHeader( artistTable, { "bottom": false } );
//    })
//    
//    $('.ui-albums').load('albums.html', function () {
//        var albumTable = $('#albums').dataTable({
//            bFilter: false,
//            bPaginate: false,
//            bLengthChange: false,
//            bSort: false,
//            bInfo: false,
//            bJQueryUI: true,
//        });
//        new FixedHeader( albumTable, { "bottom": false } );
//    })
//    
//    $('.ui-songs').load('songs.html', function () {
//        var songTable = $('#songs').dataTable({
//            bFilter: false,
//            bPaginate: false,
//            bLengthChange: false,
//            bSort: true,
//            bInfo: false,
//            bJQueryUI: true,
//        });
//        new FixedHeader( songTable, { "bottom": false } );
//    })
    
    
    
    var mainLayout, browserLayout, filterLayout;
    
    mainLayout = $('body').layout({
        center__paneSelector:   ".ui-browser",
        //center__onresize:       "browserLayout.resizeAll",
        north__paneSelector:    ".ui-header",
        north__closable:        false,
        north__resizable:       false,
        north__spacing_open:    0,
        south__paneSelector:    ".ui-statusbar",
        south__closable:        false,
        south__resizable:       false,
        south__spacing_open:    0,
        west__paneSelector:     ".ui-sources",
        applyDefaultStyles:     true,
    })
    
    browserLayout = $('.ui-browser').layout({
        center__paneSelector:   ".ui-songs",
        center__onresize:       "filterLayout.resizeAll",
        west__paneSelector:     ".ui-filters",
        center__onresize:       "filterLayout.resizeAll",
        applyDefaultStyles:     true,
    })

    filterLayout = $('.ui-filters').layout({
        //center__onresize:       "filterLayout.resizeAll",
        north__paneSelector:    ".ui-artists",
//        north__size:            "auto",
        center__paneSelector:    ".ui-albums",
//        center__size:           "auto",
        applyDefaultStyles:     true,
    })


});
