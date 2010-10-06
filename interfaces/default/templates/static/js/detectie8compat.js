/*
 * Author: Rob Reid
 * CreateDate: 20-Mar-09
 * Description: Little helper function to return details about IE 8 and its various compatibility settings either use as it is
 * or incorporate into a browser object. Remember browser sniffing is not the best way to detect user-settings as spoofing is
 * very common so use with caution.
*/
function IEVersion(){
	var _n=navigator,_w=window,_d=document;
	var version="NA";
	var na=_n.userAgent;
	var ieDocMode="NA";
	var ie8BrowserMode="NA";
	// Look for msie and make sure its not opera in disguise
	if(/msie/i.test(na) && (!_w.opera)){
		// also check for spoofers by checking known IE objects
		if(_w.attachEvent && _w.ActiveXObject){		
			// Get version displayed in UA although if its IE 8 running in 7 or compat mode it will appear as 7
			version = (na.match( /.+ie\s([\d.]+)/i ) || [])[1];
			// Its IE 8 pretending to be IE 7 or in compat mode		
			if(parseInt(version)==7){				
				// documentMode is only supported in IE 8 so we know if its here its really IE 8
				if(_d.documentMode){
					version = 8; //reset? change if you need to
					// IE in Compat mode will mention Trident in the useragent
					if(/trident\/\d/i.test(na)){
						ie8BrowserMode = "Compat Mode";
					// if it doesn't then its running in IE 7 mode
					}else{
						ie8BrowserMode = "IE 7 Mode";
					}
				}
			}else if(parseInt(version)==8){
				// IE 8 will always have documentMode available
				if(_d.documentMode){ ie8BrowserMode = "IE 8 Mode";}
			}
			// If we are in IE 8 (any mode) or previous versions of IE we check for the documentMode or compatMode for pre 8 versions			
			ieDocMode = (_d.documentMode) ? _d.documentMode : (_d.compatMode && _d.compatMode=="CSS1Compat") ? 7 : 5;//default to quirks mode IE5				   			
		}
	}
				 
	return {
		"UserAgent" : na,
		"Version" : version,
		"BrowserMode" : ie8BrowserMode,
		"DocMode": ieDocMode
	}			
}

if (IEVersion().BrowserMode === "Compat Mode") {
    $(document.createElement('div')).html("<p>You're viewing this site using Internet Explorer 8 Compatibility View. As you can see, this causes the page to render incorrectly. Please disable Compatibility View and refresh the page.</p><br><p><small><em>Hint: Try un-checking ‘Display intranet sites in Compatibility View’ at Tools -> Compatibility View Settings</em></small></p>").dialog({
        resizable: false,
        draggable: false,
        modal: true,
        title: "IE8 Compatibility View"
    });
}
