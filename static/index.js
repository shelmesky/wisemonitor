Object.size = function(obj) {
    var size = 0, key;
    for (key in obj) {
        if (obj.hasOwnProperty(key)) size++;
    }
    return size;
};
var wisemonitor = {};
var poll_func;

wisemonitor.status_interval = 6000;

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

function show_config_modal(host_type, host_name) {
    var config_modal = $("#configModal");
    var config_modal_head = $("#config_modal_head");
    var config_modal_body = $("#config_modal_body");
    config_modal_head.html("配置: " + host_name);
    if (host_type == "host") {
        $("#node_type option")[0].selected = true;
    } else {
        $("#node_type option[name=" + host_type + "]").attr({selected: true});
    }
    config_modal.modal({show: true, keyboard: true});
}


$(document).ready(function(){
        var canvas = document.getElementById('canvas');
        var stage = new JTopo.Stage(canvas);
        var scene = new JTopo.Scene(stage);	
        scene.setBackground('/static/img/bg.jpg');
        
        var all_host_data;
        var nodes = {};
        var nodes_data = {};
        var critical_nodes = {};
        var warnning_nodes = {};
        var anis = [];
        
        function draw_tipNode(msgtype) {
            if (msgtype == undefined) {
                return
            }
            
            var tipNode = new JTopo.Node();
            if (msgtype == "OK") {
                tipNode.setImage('/static/img/success.png');
            }
            if (msgtype == "ERROR") {
                tipNode.setImage('/static/img/error.png');
            }
            tipNode.setLocation(scene.width/2, 0);
            scene.add(tipNode);
            
            setTimeout(function() {
                scene.remove(tipNode);
            }, 1500)
        }
        
        
        $("#submit_button").click(function () {
            var node_type = $("#node_type option:selected").attr("name")
            var node_name = $("#node_type").attr("host_name")
            if (node_type != undefined && node_type != "unselected") {
                var node_config = {"node_type": node_type, "node_name": node_name};
                wisemonitor.ajax_post(
                    "/node_config/",
                    JSON.stringify({data: node_config}),
                    "json",
                    function(data, textStatus, xhr) {
                        console.log("Save node config success.");
                        var config_modal = $("#configModal");
                        config_modal.modal("hide");
                        scene.clear();
                        poll_func();
                        draw_saveNode();
                        draw_refreshNode();
                        draw_tipNode("OK");
                    },
                    function(xhr, textStatus, error) {
                        alert(error);
                        console.log(error);
                        console.log("Failed while save node config.");
                    }
                );
            }
            return false;
        });
        
                        
        function save_position() {
            var node_position = {};
            for (var i in nodes) {
                var temp = {};
                temp["X"] = parseInt(nodes[i].x);
                temp["Y"] = parseInt(nodes[i].y);
                node_position[i] = temp;
            }
            wisemonitor.ajax_post(
                "/save_position/",
                JSON.stringify({data: node_position}),
                "json",
                function(data, textStatus, xhr) {
                    draw_tipNode("OK");
                },
                function(xhr, textStatus, error) {
                    console.log(error);
                    draw_tipNode("ERROR");
                }
            );
        }
        
        function get_status(node) {
            var html = "";
            html += "<p>Name: " + all_host_data[node]["host_name"] + "</p>";
            html += "<p>Alias: " + all_host_data[node]["host_alias"] + "</p>";
            html += "<p>Address: " + all_host_data[node]["host_address"] + "</p>";
            html += "<p>Last Update: " + all_host_data[node]["last_update"] + "</p>";
            html += "<p>Output: " + all_host_data[node]["output"] + "</p>";
            html += "<p><span style='color: #00FF00;'>Service OK: </span>" + all_host_data[node]["service_ok"] + " ";
            html += "<span style='color: yellow;'>WARN: </span>" + all_host_data[node]["service_warn"] + " ";
            html += "<span style='color: red;'>CRITICAL: </span>" + all_host_data[node]["service_critical"] + " ";
            html += "UNKNOWN: " + all_host_data[node]["service_unknow"] + "</p>";
            return html;
        }
        
        function draw_saveNode() {
            // save button
            var saveNode = new JTopo.Node();
            saveNode.setImage('/static/img/save.png');
            saveNode.setSize(32, 32);
            saveNode.setLocation(scene.width - 34, 0)
            saveNode.dragable = false;
            scene.add(saveNode);
            
            saveNode.addEventListener('mouseup', function(event){
                if(event.button == 0){// 左键
                    save_position();
                }
            });
        }
        draw_saveNode();
        
        function draw_refreshNode() {
            // refresh button
            var refreshNode = new JTopo.Node();
            refreshNode.setImage('/static/img/refresh.png');
            refreshNode.setSize(32, 32);
            refreshNode.setLocation(scene.width - 70, 0)
            refreshNode.dragable = false;
            scene.add(refreshNode);
        
            refreshNode.addEventListener('mouseup', function(event){
                if(event.button == 0){// 左键
                    scene.clear();
                    draw_refreshNode();
                    draw_saveNode();
                    poll_func();
                    draw_tipNode("OK");
                }
            });
        }
        draw_refreshNode();
    
        var play = function(data) {
            
            var response = data["data"];
            all_host_data = data["all_host_data"]
            var topo_has_saved = data["topo_has_saved"]
            
            var cloudNode = new JTopo.Node();
            cloudNode.setImage('/static/img/cloud.png');
            cloudNode.setSize(64, 64);
            cloudNode.dragable = false;
            cloudNode.setCenterLocation(canvas.width/2, canvas.height/2);
            if (topo_has_saved == 0) {
                cloudNode.layout = {type: 'star', radius:180, auto:true};
            }
            scene.add(cloudNode);
            
            scene.addEventListener('mouseup', function(event){
                if (event.button == 0) {
                        $("#contextmenu").hide();
                }
            });
            
            // draw all subtree
            for(var i=0; i<response.length; i++) {
                
                var root = response[i]["root"];
                
                var node_data = root["data"];
                var link = new JTopo.Link(cloudNode, node);
                var node = new JTopo.Node();
                node.name = root["node"];
                nodes[node.name] = node;			    
                node.setLocation(node_data["X"], node_data["Y"]);
                
                //save data of all node
                nodes_data[node.name] = node_data;
                
                if (node_data['status'] == 2) {
                    node.setImage('/static/img/' + node_data['node_type'] + '_critical.png');
                    node.setSize(30, 26);
                    if (topo_has_saved == 0) {
                        node.layout = {type: 'star', radius:110, auto:true};
                    }
                    var link = new JTopo.FoldLink(cloudNode, node);
                    link.style.strokeStyle = '255,0,0';
                    link.style.fillStyle = '255,0,0';
                    scene.add(node);
                    var ani = JTopo.Animate.stepByStep(node, {alpha: 0.2}, 800, true);
                    anis.push(ani);
                } else {
                    node.setImage('/static/img/' + node_data['node_type'] + '.png');
                    node.setSize(30, 26);
                    if (topo_has_saved == 0) {
                        node.layout = {type: 'star', radius:110, auto:true};
                    }
                    var link = new JTopo.FoldLink(cloudNode, node);
                    link.style.strokeStyle = '0,255,0';
                    link.style.fillStyle = '0,255,0';
                    scene.add(node);								
                }
                scene.add(link);
                
                // add mouse over menu
                node.addEventListener('mouseup', function(event){
                    if (event.button == 2) {
                        var node_type = nodes_data[event.target.name]["node_type"];
                        var args = node_type + "','" + event.target.name;
                        $("#menu_content").html(get_status(event.target.name));
                        $("#menu_footer").html("<a href='/infra/server/" +  event.target.name + "/'>Detail</a>&nbsp;&nbsp;<a href='#' onclick=\"show_config_modal('" + args + "')\"'>Edit</a>");
                        $("#node_type").attr("host_name", event.target.name);
                        // show menu
                        $("#contextmenu").css({
                            //top: scene.stage.offsetY,
                            //left: scene.stage.offsetX,
                            top: event.pageY,
                            left: event.pageX,
                            display: "inline-table",
                        }).show();
                    }
                });
                
                /*
                // add mouse leave event
                node.addEventListener('mouseout', function(event){
                        // hide menu
                        $("#contextmenu").hide();
                });
                */
                
                var childs = response[i]["child"];
                
                for(var j=0; j<childs.length; j++) {
                    
                    var node_name = childs[j]["node"];
                    var parent_name = childs[j]["parent"];
                    var child_node_data = childs[j]["data"];
                    var child_node = new JTopo.Node();
                    child_node.name = node_name;
                    nodes[child_node.name] = child_node;
                    child_node.setLocation(child_node_data["X"], child_node_data["Y"]);
                    
                    //save data of all child node
                    nodes_data[child_node.name] = child_node_data;
                    
                    if (child_node_data['status'] == 2) {
                        child_node.setImage('/static/img/' + child_node_data['node_type'] + '_critical.png');
                        child_node.setSize(30, 26);
                        if (topo_has_saved == 0) {
                            child_node.layout = {type: 'star', radius:110, auto:true};
                        }
                        child_node.style.fillStyle = '0,255,0';
                        child_node.radius = 10;
                        scene.add(child_node);								
                        var node_link = new JTopo.FoldLink(nodes[parent_name], child_node);
                        node_link.style.strokeStyle = '255,0,0';
                        node_link.style.fillStyle = '255,0,0';
                        scene.add(node_link);
                        var ani = JTopo.Animate.stepByStep(child_node, {alpha: 0.2}, 800, true);
                        anis.push(ani);
                    } else {
                        child_node.setImage('/static/img/' + child_node_data['node_type'] + '.png');
                        child_node.setSize(30, 26);
                        if (topo_has_saved == 0) {
                            child_node.layout = {type: 'star', radius:110, auto:true};
                        }
                        child_node.style.fillStyle = '0,255,0';
                        child_node.radius = 10;
                        scene.add(child_node);								
                        var node_link = new JTopo.FoldLink(nodes[parent_name], child_node);
                        node_link.style.strokeStyle = '0,255,0';
                        node_link.style.fillStyle = '0,255,0';
                        scene.add(node_link);
                    }
                    
                    // add mouse over menu
                    child_node.addEventListener('mouseup', function(event){
                        if (event.button == 2) {
                            // show menu
                            var node_type = nodes_data[event.target.name]["node_type"];
                            var args = node_type + "','" + event.target.name;
                            $("#menu_content").html(get_status(event.target.name));
                            $("#menu_footer").html("<a href='/infra/server/" +  event.target.name + "/'>Detail</a>&nbsp;&nbsp;<a href='#' onclick=\"show_config_modal('" + args + "')\"'>Edit</a>");
                            $("#node_type").attr("host_name", event.target.name);
                            $("#contextmenu").css({
                                //top: scene.stage.offsetY,
                                //left: scene.stage.offsetX,
                                top: event.pageY,
                                left: event.pageX + 15,
                            }).show();
                        }
                    });
                    
                    /*
                    // add mouse leave event
                    child_node.addEventListener('mouseout', function(event){
                            // hide menu
                            $("#contextmenu").hide();
                    });
                    */
                }
            }
            
            for (var n=0; n<anis.length; n++) {
                anis[n].start();
            }
            
            
            scene.layoutNode(cloudNode);
            
            scene.addEventListener('mouseup', function(e){
                    if(e.target && e.target.layout){
                            scene.layoutNode(e.target);	
                    }				
            });
            
            stage.play(scene);
        };
        
        var error = function(err) {
            console.log(err);
        };
        
        poll_func = function() {
            wisemonitor.ajax_get(
                "/getdata/",
                "json",
                play,
                error
            );
        }
        poll_func();

        var updater = {
            errorSleepTime: 500,
            cursor: null,

            success: function(response, textStatus, xhr) {
                console.log(response);
                updater.cursor = response[response.length-1].message_id;
                updater.errorSleepTime = 500;
                scene.clear();
                draw_refreshNode();
                draw_saveNode();
                poll_func();
                draw_tipNode("OK");
                window.setTimeout(updater.poll, 100);
            },

            error: function(xhr, textStatus, error) {
                console.log(error);
                updater.errorSleepTime *= 2;
                    window.setTimeout(updater.poll, updater.errorSleepTime);
            },

            poll: function() {
                var data = {
                    cursor: updater.cursor,
                    post_from: "ajax"
                };
                    wisemonitor.ajax_post("/system/alerts/physical_device/", data, "json", updater.success, updater.error);
            }
        };
        updater.poll();
        
        
        var cloud_capacity = {
            guages: {},
            capacity_type: {
                0: "内存",
                1: "CPU",
                2: "存储",
                3: "已分配的主存储",
                4: "公用 IP 地址",
                5: "管理类 IP",
                6: "二级存储",
                7: "VLAN",
                8: "直接 IP",
                9: "本地存储"
            },
            errorSleepTime: 500,
            success: function(response, textStatus, xhr) {
                var capacitys = response.capacitys.listcapacityresponse.capacity;
                cloud_capacity.show_capacity(capacitys);
            },
            error: function(xhr, textStatus, error) {
                console.log(error);
            },
            poll: function() {
                wisemonitor.ajax_get("/wizcloud_capacity/", "json", cloud_capacity.success, cloud_capacity.error);
            },
            show_capacity: function(capacitys) {
                function sleep(d){
                    for(var t = Date.now();Date.now() - t <= d;);
                }

                if (Object.size(cloud_capacity.guages) == 0) {
                    for (var i=0; i<capacitys.length; i++) {
                        var gid = 'g' + capacitys[i].type;
                        var g1 = new JustGage({
                            id: gid,
                            value: parseInt(capacitys[i].percentused),
                            min: 0,
                            max: 100,
                            title: cloud_capacity.capacity_type[capacitys[i].type],
                            label: "",
                            levelColorsGradient: false
                        });
                        cloud_capacity.guages[gid] = g1;
                    }
                } else {
                    for (var i=0; i<capacitys.length; i++) {
                        var g = cloud_capacity.guages['g' + capacitys[i].type];
                        g.refresh(parseInt(capacitys[i].percentused));
                    }
                }
                window.setTimeout(cloud_capacity.poll, 30000);
            },
            manual_update: function() {
                window.setTimeout(cloud_capacity.poll, 0);
            }
        };
        cloud_capacity.poll();
        
        $("#manual_update_capacity").click(function() {
            cloud_capacity.manual_update();
        });
        
        var perfranker = {
            content_type: {
                "cpu_usage": "CPU 使用率",
                "network_io": "网络 I/O",
                "disk_io": "磁盘 I/O"
            },
            perfrank_type: "",
            errorSleepTime: 500,
            success: function(response, textStatus, xhr) {
                perfranker.show_rank(response['data']);
            },
            error: function(xhr, textStatus, error) {
                console.log(error);
                var perfrank_html = $("#perfrank");
                perfrank_html.empty();
                perfrank_html.html(error);
            },
            poll: function(perfrank_type) {
                perfranker.perfrank_type = perfrank_type;
                wisemonitor.ajax_get("/perf_rank/" + perfrank_type + "/", "json", perfranker.success, perfranker.error);
            },
            show_rank: function(ranks) {
                var perfrank_html = $("#perfrank");
                perfrank_html.empty();
                for(var i=0; i<ranks.length; i++) {
                    var vm_uuid = ranks[i][0];
                    var vm_data = ranks[i][1];
                    var rank_content = vm_data[perfranker.perfrank_type];
                    var html = '<div class="alert alert-error"> VM UUID: ' + vm_uuid + " / ";
                    html += perfranker.content_type[perfranker.perfrank_type] + ": " + parseFloat(rank_content).toFixed(2) + "</div>";
                    perfrank_html.append(html);
                }
            },
            manual_update: function(perfrank_type) {
                perfranker.poll(perfrank_type);
            }
        };
        perfranker.poll("cpu_usage");
        $("#perfrank_cpu_usage").addClass("active");
        
        $("#perfrank_cpu_usage").click(function() {
                $("#perfrank_cpu_usage").addClass("active");
                $("#perfrank_network_io").removeClass("active");
                $("#perfrank_disk_io").removeClass("active");
                perfranker.poll("cpu_usage");
        });
        
        $("#perfrank_network_io").click(function() {
                $("#perfrank_network_io").addClass("active");
                $("#perfrank_cpu_usage").removeClass("active");
                $("#perfrank_disk_io").removeClass("active");
                perfranker.poll("network_io");
        });
        
        $("#perfrank_disk_io").click(function() {
                $("#perfrank_disk_io").addClass("active");
                $("#perfrank_network_io").removeClass("active");
                $("#perfrank_cpu_usage").removeClass("active");
                perfranker.poll("disk_io");
        });
        
        
         var alert_updater = {
            alert_type: "",
            errorSleepTime: 500,
            success: function(response, textStatus, xhr) {
                if (alert_updater.alert_type == "physical") {
                    alert_updater.show_physical_alert(response.objects);
                } else if (alert_updater.alert_type == "virtual") {
                    alert_updater.show_virtual_alert(response.objects);
                }
            },
            error: function(xhr, textStatus, error) {
                console.log(error);
                var alerter_html = $("#alerter");
                alerter_html.empty();
                alerter_html.html(error);
            },
            poll: function(alert_type) {
                alert_updater.alert_type = alert_type;
                wisemonitor.ajax_get("/top_alerts/" + alert_type + "/", "json", alert_updater.success, alert_updater.error);
            },
            show_physical_alert: function(alerts) {
                console.log(alerts);
                var alerter_html = $("#alerter");
                alerter_html.empty();
                for(var i=0; i<alerts.length; i++) {
                    var deli = ' / ';
                    var created_time = alerts[i].created_time;
                    var host = alerts[i].message.host;
                    var output = alerts[i].message.output;
                    var return_code = alerts[i].message.return_code;
                    if (return_code == 1) {
                        var html = '<div class="alert alert-info">';
                    }
                    else if (return_code == 2) {
                        var html = '<div class="alert alert-error">';
                    }
                    else if (return_code == 3) {
                        var html = '<div class="alert alert-block">';
                    }
                    html += created_time + deli + host + deli + output;
                    html += '</div>';
                    alerter_html.append(html);
                }
            },
            show_virtual_alert: function(alerts) {
                var deli = ' / ';
                console.log(alerts);
                var alerter_html = $("#alerter");
                alerter_html.empty();
                for(var i=0; i<alerts.length; i++) {
                    var created_time = alerts[i].created_time;
                    var message_type = alerts[i].message_type;
                    var host = alerts[i].message.host;
                    var vm_name_label = alerts[i].message.vm_name_label;
                    var trigger_value = alerts[i].message.trigger_value;
                    var current_value = alerts[i].message.current_value;
                    var html = '<div class="alert alert-error">';
                    html += created_time + deli + message_type + deli + host + deli + vm_name_label + deli;
                    html += "Current Value: " + parseFloat(current_value).toFixed(2) + " More than: " + trigger_value;
                    html += '</div>';
                    alerter_html.append(html);
                }
            }
        };
        alert_updater.poll("physical");
        $("#alerter_physical").addClass("active");
        
        $("#alerter_physical").click(function() {
            $("#alerter_physical").addClass("active");
            $("#alerter_virtual").removeClass("active");
            alert_updater.poll("physical");
        });
        
        $("#alerter_virtual").click(function() {
            $("#alerter_physical").removeClass("active");
            $("#alerter_virtual").addClass("active");
            alert_updater.poll("virtual");
        });
});