function format_string(src, args){
    return src.replace(/\{(\d+)\}/g, function(m, i){
	return args[i];
    });
}

function show_msg_text(level, text) {
    var o = $('#'+level+'-message');
    o.html(text);
    o.clearQueue();
    o.fadeIn(200).delay(5000).fadeOut(200);
};

function show_info(text) {
    show_msg_text('info',text);
}

function show_error(text) {
    show_msg_text('info',text);
}

function show_debug(text) {
    show_msg_text('info',text);
}

function sure(e, question,yes, no,  on_yes) {
    $('#__confirm_box__').remove();
    
    e.preventDefault();
    var box = $("<div id='__confirm_box__' class='confirm-overlay'><div class='confirm-box'>"+
		"<h1>"+question+"</h1><span><a id='yes'  href='javascript:;' class='button'>"+yes+"</a></span>"+
		"<span><a id='no' href='javascript:;' class='button'>"+no+"</a></span>"+
		"</div></div>");
    box.css({"top":e.pageY, "left":e.pageX});
    box.find('#yes').click(function() {
	box.remove();
	if (on_yes != undefined) {
	    on_yes();
	}
    });
    
    box.find('#no').click(function() {
	box.remove();
    });		    
    $('body').append(box);    
}

(function($) {
    $.fn.extend({
	confirm: function(question, yes, no, on_yes) {
	    return this.each(function() {
		$(this).click(function(e) {
		    sure(e, question, yes, no, on_yes)
		});
	    });
	}
    })
})(jQuery);

