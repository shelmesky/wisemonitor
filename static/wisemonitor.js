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
		datatype == 'json';
	}
	
	method == "POST";
	
	$.ajax({
		type: method,
		url: url,
		data: data,
		dataType: datatype,
		success: success_callback,
		error: error_callback
	})
}


wisemonitor.ajax_get = function(url, datatype,
				 success_callback, error_callback) {
	
	if (datatype == undefined) {
		datatype == 'json';
	}
	
	method == "GET";
	
	$.ajax({
		type: method,
		url: url,
		dataType: datatype,
		success: success_callback,
		error: error_callback
	})
}

// on document ready
$(function(){
    // fix: get remote url only once for the dialog
    $("#wisemonitorModal").on('hidden', function() {
        $(this).removeData('modal');  
    });
});



