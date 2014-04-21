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
    
    showMessage: function(content) {
	data = content.message;
	
	if (data.message_type == "cpu_usage") {
	    var alert_area = $("#virtual--device-alert-appender");
	    var appender_table = $("#appender-table");
	    var msg = "<div class='alert alert-error fade in hide' id='"+ content.message_id + "'>" + "CPU使用率: " + data.created_time + " / " +  "<a href='/xenserver/hosts/" + data.message.host + "/'>" + data.message.host + "</a> / ";
	}
	if (data.message_type == "disk_usage") {
	    var msg = "<div class='alert alert-error fade in hide' id='"+ content.message_id + "'>" + "磁盘使用率: " + data.created_time + " / " +  "<a href='/xenserver/hosts/" + data.message.host + "/'>" + data.message.host + "</a> / ";
	}
	if (data.message_type == "network_usage") {
	    var msg = "<div class='alert alert-error fade in hide' id='"+ content.message_id + "'>" + "网络使用率: " + data.created_time + " / " +  "<a href='/xenserver/hosts/" + data.message.host + "/'>" + data.message.host + "</a> / ";
	}
	msg += data.message.vm_name_label + " / ";
	msg += "Curren: " + data.message.current_value + " / ";
	msg += "More than: " + data.message.trigger_value;
	msg += "<i class='icon-bell' style='float: right'></i>";
	msg += "</div>";
	
    appender_table.show();
	alert_area.prepend(msg);
	
	var new_alert_area = $("#" + content.message_id);
	new_alert_area.show(500);
	
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



