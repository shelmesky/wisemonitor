try {
    console.info('test console info');
    console.debug('test console debug');
    console.error('test console error');
    console.log('test console log');
} catch(e) {
    var emptyFunction = function(){};
    console = {};
    console.info = console.debug = console.error = console.log = emptyFunction;
}

var wisemonitor = {};

wisemonitor.status_interval = 6000;

wisemonitor.modal = function(modal_id, opts) {
	if (opts == undefined) {
		opts = {show:true, keyboard:true};
	}
	$('#' + modal_id).modal(opts);
};

wisemonitor.ajax_post = function(url, data, datatype,
				 success_callback, error_callback) {
	
	if (datatype == undefined) {
		datatype = 'json';
	}
	
	method = "POST";
	
	$.ajax({
		url: url,
		type: method,
		dataType: datatype,
		data: data,
		success: success_callback,
		error: error_callback
	})
}


wisemonitor.ajax_get = function(url, datatype,
				 success_callback, error_callback) {
	
	if (datatype == undefined) {
		datatype == 'json';
	}
	
	method = "GET";
	
	$.ajax({
		url: url,
		type: method,
		dataType: datatype,
		success: success_callback,
		error: error_callback
	})
}

var updater = {
    errorSleepTime: 500,
    cursor: null,
	
    success: function(response) {
	updater.cursor = response[response.length-1].message_id;
	console.info("cursor: " + updater.cursor);
	console.log(response);
	updater.errorSleepTime = 500;
	window.setTimeout(updater.poll, 0);
	for(var i=0; i<response.length; i++) {
	    updater.showMessage(response[i]); 
	}
    },
    
    error: function(response) {
	updater.errorSleepTime *= 2;
	console.log("Poll error; sleeping for", updater.errorSleepTime, "ms");
	console.log(response)
	window.setTimeout(updater.poll, updater.errorSleepTime);
    },
	    
    poll: function() {
        data = {
	    cursor: updater.cursor
	};
	wisemonitor.ajax_post("/system/alerts/xenserver/", data, "json",
					      updater.success, updater.error);
    },
    
    showMessage: function(data) {
	//console.log(data);
    }
}

// on document ready
$(function(){
    // fix: get remote url only once for the dialog
    $("#wisemonitorModal").on('hidden', function() {
        $(this).removeData('modal');  
    });
	updater.poll();
});



