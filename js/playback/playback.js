/*
 * noVNC: HTML5 VNC client
 * Copyright (C) 2012 Joel Martin
 * Licensed under MPL 2.0 (see LICENSE.txt)
 */

"use strict";
/*jslint browser: true, white: false */
/*global Util, VNC_frame_data, finish */

var ws;

var rfb, mode, test_state, frame_idx, frame_length,
    iteration, iterations, istart_time,

    // Pre-declarations for jslint
    send_array, next_iteration, queue_next_packet, do_packet;
var run_client;
var VNC_frame_encoding = 'binary';

// Override send_array
send_array = function (arr) {
    // Stub out send_array
};

var bytes_processed = 0;

do_packet = function (frame) {
    if (VNC_frame_encoding === 'binary') {
        var u8 = new Uint8Array(frame.length);
        for (var i = 0; i < frame.length; i++) {
            u8[i] = frame.charCodeAt(i);
        }
        rfb.recv_message({'data' : u8});
    } else {
        rfb.recv_message({'data' : frame.slice(start)});
    }
};

function ArrayBufferToString(buffer) {
    return BinaryToString(String.fromCharCode.apply(null, Array.prototype.slice.apply(new Uint8Array(buffer))));
}


function BinaryToString(binary) {
    var error;
    try {
        return decodeURIComponent(escape(binary));
    } catch (_error) {
        error = _error;
        if (error instanceof URIError) {
            return binary;
        } else {
            throw error;
        }
    }
}

run_client = function (fname) {
    var path = "ws://localhost:23456/serv/playback?filename=";
    path += fname
    ws = new WebSocket(path);
    rfb.connect('test', 0, "bogus");
    
    ws.onopen = function () {
          ws.binaryType = "arraybuffer";
          console.log("open");
    };
       
    ws.onmessage = function (e) {
        var data = ArrayBufferToString(e.data);
        do_packet(data);
    };
    
    ws.onclose = function (e) {
       ws.close();
       console.log("websocket closed");
    };
}