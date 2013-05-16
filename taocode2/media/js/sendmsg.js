function init_send_msg(uname){
    $('#send-msg').click(function(e) {
	show_send_box(e.pageX, e.pageY, uname);
    });
}

function show_send_box(x, y, target) {

    if ($('body').find('#send-msg-form').length > 0) {
	return;
    } 

    var t = $("<div id='send-msg-form'><div id='send-msg-box'>"+
	      "<div>Send to <span class='username'>"+target+"</span></div>"+
	      "<div><textarea id='content' rows='5' cols='35'></textarea></div>"+
	      "<p><a id='send' class='button green' href='javascript:;'>send</a>" +
	      "<a id='cancel' class='button orange' href='javascript:;'>cancel</a>" +
	      "</p></div></div>");
    
    t.css({"top":y, "left":x});
    t.find('#cancel').click(function () {
	t.remove();
    });

    t.find('#send').click(function () {
	var c = t.find('#content').val();
	if (c.length <= 0) {
	    show_info('please input some text!');
	    return;
	}
	q_get('msg/send', {'u':target, 'c':c}, function(result) {
	    show_info('send message ok!');
	}, function() { // onfail
	    show_info('send message fail!');
	});
	
	t.remove();
    });
    
    $('body').append(t);
}