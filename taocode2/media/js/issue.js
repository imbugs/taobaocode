function issue_list_ready(project) {

};

function build_prop_text(project, prop_type, 
			 has_remove, prop) {
    var t = "<div class='issue-{0}-item' id='issue-{0}-{1}'>{1}";
    if (has_remove) {
	t += "<a href='javascript:;'>&nbsp;&nbsp;X</a></div>";
    } else {
	t += '</div>';
    }

    var prop_id = prop[0];
    var prop_name = prop[1];

    var new_elm = $(format_string(t, [prop_type, prop_name]));
    
    new_elm.data('pid', prop_id);
    new_elm.find('a').click(function() {
	del_prop(project.name, prop_type, prop_name);
    });
    
    new_elm.click(function() {
	$(this).toggleClass('issue-'+prop_type+'-item-choice');
    });


    return new_elm;
}

function add_issue_prop_event(project, prop_type) {
    $('#new-'+prop_type+' #form #add').click(function() {
	var n = $('#new-'+prop_type+' #form #name').val();
	if ( n == null || n.length <= 0) {
	    return;
	}
	var args = {'name':n};
	if (prop_type == 'tag') {
	    var c = $('#new-'+prop_type+' #form #color').val() || '';
	    args['color'] = c;
	}
	
	q_get("issue/new_"+prop_type+"/"+project.name, args, function (result) {
	    var new_p = build_prop_text(project, prop_type, 
					project.isowner, result)
	    $('#issue-'+prop_type+'s').append(new_p);
	}, function () {
	    show_info("the "+prop_type+" already exist!");
	});
    });
}

function get_issue_props(project, prop_type) {
    q_get("issue/"+prop_type+"s/"+project.name, {}, function(result){
	var t = $('#issue-'+prop_type+'s');
	t.empty();
	for(var i = 0; i < result.length; i++) {
	    var new_p = build_prop_text(project, prop_type, 
					project.isowner, result[i]);
	    t.append(new_p);
	}
    });
}

function del_prop(project_name, prop_type, prop_name) {
    q_get("issue/del_"+prop_type+"/"+project_name,
	   {"name":prop_name}, function () {
	       $('#issue-'+prop_type+'-' + prop_name).remove();
	   }, function () {
	       show_info("can not del the "+prop_type+"");
	   });
}


function do_del_issue(issue_id, o) {
    q_get("issue/del", {'issue_id':issue_id}, function (result) {
	o.remove();
	$("span[name='page-record-count']").each(function(){
	    var c = parseInt($(this).text());
	    $(this).text(--c);
	});  
    }, function () {
	show_info("can not del issue");
    });
}
