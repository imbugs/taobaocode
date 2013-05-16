
function __fclean(uri, name) {
    var o = $('#'+name);
    var v = o.find('input').val();
    if (v.length > 0) {
        $.post(uri,{"v":v},
               function(result){
		   var tip = o.find('#clean_result');
		   tip.empty();
		   var t = $("<span><img src='/img/"+(result[0] ? "yes" : "no")+
			     ".png' style='width:15px;height:15px;'></img></span>");
		   tip.append(t);
		   
		   if (!result[0]) {
		       tip.append($('<span>'+result[1]+'</span>'));
		   }
               });
    } else {
	o.find('#clean_result').empty();
    }
}
