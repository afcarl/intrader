$(function() {
	  var path = location.pathname.substring(1);
	  if ( path )
		  $('#navbar-top li[id$="' + path + '"]').attr('class', 'active');
}
);