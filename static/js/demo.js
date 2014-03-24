
(function(){
	var demos = [
		'核心对象', 
		{text:'Hello world', href:'helloworld.html'},
		{text:'节点', href:'node.html'},
		{text:'节点文本定位', href:'node-label-position.html'},		
		{text:'导出PNG', href:'save-as-png.html'},
		{text:'Gif模拟', href:'animate_gif.html'},
		{text:'动画节点', href:'animate_sprite.html'},
		{text:'动画', href:'animate_stepbystep.html'},		
		{text:'圆形节点', href:'circle_sprite.html'},
		{text:'场景切换', href:'scence_change.html'},
		{text:'场景事件', href:'scence_event.html'},

		'动画效果',
		{text:'重力', href:'animate_grivty.html'},	
		{text:'重力2', href:'topo-grivty.html'},
		{text:'重力3', href:'topo-grivty2.html'},
		{text:'重力4', href:'topo-grivty3.html'},
		{text:'节点切割', href:'effect-split-node.html'},
		
		'拓扑图形',
		{text:'基本拓扑', href:'topo.html'},
		{text:'连线', href:'topo-link.html'},
		{text:'布局', href:'topo-layout.html'},
		{text:'布局2', href:'topo-layout2.html'},		
		{text:'混合布局', href:'topo-layout-mix-1.html'},
		{text:'混合布局2', href:'topo-layout-mix-2.html'},
		{text:'布局-动态', href:'topo-layout3.html'},
		{text:'容器分组', href:'topo-container.html'},	
		{text:'节点告警', href:'topo-node-alarm.html'},	
		
		'统计图表',
		{text:'饼图', href:'topo-pieChart.html'},
		'Twaver示例',
		{text:'statictis', href:'twaver-statictis.html'},
		{text:'PSTN', href:'twaver-pstn.html'},
		{text:'Matrix', href:'twaver-matrix.html'},	
		'其他',
		{text:'UML图', href:'topo-uml.html'},
		{text:'Win7桌面', href:'topo-desktop.html'},
		{text:'联系作者', href:'contact.html'}
			
	];

	function drawMenus(menus){
		var ul = $('#menu').empty();
		var li = null;
		var children = null;
		$.each(demos, function(i, e){
			if(typeof e == 'string'){
				li = $('<li>').appendTo(ul).addClass('cat-item cat-item-1').appendTo(ul);
				$('<a>').html(e).appendTo(li);
				children = $('<ul>').addClass('children').appendTo(li);
			}else{
				var cli = $('<li>').addClass('cat-item cat-item-5').appendTo(children);
				$('<a>').attr('href', './' + e.href).html(e.text).appendTo(cli);
			}
		});
	}

	String.prototype.replaceAll = function(reallyDo, replaceWith, ignoreCase) {
    if (!RegExp.prototype.isPrototypeOf(reallyDo)) {
        return this.replace(new RegExp(reallyDo, (ignoreCase ? "gi": "g")), replaceWith);
    } else {
        return this.replace(reallyDo, replaceWith);
    }};
	
	$(document).ready(function(){
		var content = $('#content').empty();
		var canvas = $('<canvas width="800" height="500">').attr('id', 'canvas').appendTo(content);
		canvas.css({
			'background-color': '#EEEEEE',
			'border': '1px solid #444'
		});
		drawMenus(demos);	
		var code = $('#code').text();
		code = code.replaceAll('>', '&gt;');
		code = code.replaceAll('<', '&lt;');
		var pre = $('<pre width="600">').appendTo($('#canvas').parent().css('width', '800px')).html(code);
		pre.snippet("javascript",{style:"acid",collapse:true});
	});
})();

