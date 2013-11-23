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
	wisemonitor.ajax_post("/system/alerts/physical_device/", data, "json",
					      updater.success, updater.error);
    },
    
    showMessage: function(content) {
	data = content.message
	var alert_area = $("#physical-device-alert");
	if (data.message.return_code == 1) {
	    var msg = "<div class='alert alert-error fade in hide'>" + "警告：" + data.created_time +  " / " + data.message.host + " / ";
	}
	if (data.message.return_code == 2) {
	    var msg = "<div class='alert alert-error fade in hide' id='"+ content.message_id + "'>" + "严重：" + data.created_time +  " / " + data.message.host + " / ";
	}
	if (data.message.service != "") {
	    msg += data.message.service + " / ";
	}
	msg += data.message.output;
	msg += "<i class='icon-bell' style='float: right'></i>";
	msg += "</div>";
	alert_area.prepend(msg);
	
	var new_alert_area = $("#" + content.message_id);
	new_alert_area.show(300);
	
	var alert_counter = $("#alert_counter").html();
	var alert_counter_number = parseInt(alert_counter, 10);
	alert_counter_number += 1;
	$("#alert_counter").html(alert_counter_number);
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



