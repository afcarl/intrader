$(function() {
	  $('select#contract-group').change(function(){
		  $.getJSON($SCRIPT_ROOT + '/get_contract_names/' + $(this).val(), function(data) {
			  var options = '';
			  for (var i = 0; i < data.data.length; i++) {
				  options += '<option value="' + data.data[i].id + '">' + data.data[i].name + '</option>';
			  }
			  $('select#contract-select').html(options);
		  }
);
});
});