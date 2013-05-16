
function get_cookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
	var cookies = document.cookie.split(';');
	for (var i = 0; i < cookies.length; i++) {
	    var cookie = jQuery.trim(cookies[i]);
	    // Does this cookie string begin with the name we want?
	    if (cookie.substring(0, name.length + 1) == (name + '=')) {
		cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
		break;
	    }
	}
    }
    return cookieValue;
}	    

function init_csrf() {
    jQuery.ajaxSetup({'beforeSend': function(xhr){
	xhr.setRequestHeader("X-CSRFToken", get_cookie("csrftoken"));
    }});
    
}

function start_call() {

}

function start_auth_call() {
    window.setTimeout(get_unread_msg_count, 5000);
}

function q_get(uri, args, onok, onfail, oncomplete) {
    $.post('/ajax/'+uri+'/',
	   args,
	   function (result) {
	       if (typeof(result) == 'object'){
		   if(typeof(result[0]) != 'boolean' || 
		      !result[0]) {
		       if (onfail != undefined) {
			   onfail();
		       }
		   } else {
		      onok(result[1]); 
		   }
		   return;
	       }
	       // result is True or False
	       if (typeof(result) == 'boolean' && !result) {
		   if (onfail != undefined) {
		       onfail();
		   }
	       } else {
		   onok(result);
	       }
	   }).error(function(xhr) {
	       show_error(xhr.responseText);
	   }).complete(function() {
	       if (oncomplete != undefined) {
		   oncomplete();
	       }
	   });
}


function get_unread_msg_count() {
    q_get('msg/unread_count', {}, function(r){
	if (typeof(r) == 'number') { 
	    $('#msg_count').html('(' + r +')');
	}
    });
}
