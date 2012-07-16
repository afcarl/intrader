// fill or erase input rows based off of contract group selection
$(function() {$('select#contract-group').change(
	function() {
		if ($(this).val() === 'create-new') {
				  
			$('#new-group-controls').removeClass('hide');

			var $rows = $('.input-row');

			$rows.each(function() {
						   if ($(this).hasClass('row1') === false) {
							   $(this).remove();   
						   } else {
							   $(this).find('.contract-id').val('');
							   $(this).find('.contract-name').val('');
						   }
					   });

		} else {

			$('#new-group-controls').addClass('hide');

			var selected = $('#contract-group').val();

			$.getJSON($SCRIPT_ROOT + '/get_contract_names/' + selected, function(data){
    
    			$('.input-row').each(function() { 
    				if ($(this).hasClass('row1') === false) {
    					$(this).remove(); 
    				}
    			});
    
				for (i = 0; i < data.data.length; i++){
					
					// create and populate new input field
					var $new = $('.row1').clone();

					$new.find('.contract-id').val(data.data[i].id);
					$new.find('.contract-name').val(data.data[i].name);

					if (i === 0) {
						$('.row1').remove();
					} else {
						$new.removeClass('row1');
					}

					$('#group-inputs').append($new);					

					}});

				}
			});
			  
});

// delete individual row after user presses .delete-contract
$('.delete-contract').live('click',
	function () {
		if ($('#group-inputs').children().length > 1) {
			$(this).closest('.input-row').remove();
		}
		$('#group-inputs').children(':first').addClass('row1');
		return false;
	}
);

// add new contract row
$('#add').click(
	function() {
		var $new = $('.row1').clone();

		$new.find('.contract-id').val('');
		$new.find('.contract-name').val('');
		$new.removeClass('row1');
		$('#group-inputs').append($new);

		return false;
});

// delete selected group
$('#delete-group').click(
	function() {
		var data = {
			toDelete: $('#contract-group').val()
		};
		var $alert = $('#settings-alert');
		if (data.toDelete === 'create-new') {
			$alert.removeClass('hide');
			$alert.text('Please choose a valid group to delete.');
		} else {
			$alert.addClass('hide');
			$.post($SCRIPT_ROOT + '/delete_group', data, function() {
					   window.location.reload(true);
				   });
		}
		return false;
	}
);

// add new contract group using data from both forms
$('#save').click(
	function() {

		var $alert = $('#settings-alert');

		// get dict of all the data we need to post
		if ($('#contract-group').val() === 'create-new') {
			var group = $('#group-name').val();
			var createNew = true;
		} else {
			var group = $('#contract-group').val();
			var createNew = false;
		}

		if (createNew === true && group === '') {
			$alert.removeClass('hide');
			$alert.text('Please enter a valid name for the new group.');
			return false;
		}

		var data = {
			group: group,
			createNew: createNew
		};

		contracts = [];
		$('#group-inputs').children().each(
			function() {
				if ($(this).find('.contract-id').val() != '' &&
					$(this).find('contract-name').val() != '') {
					contracts.push({id: $(this).find('.contract-id').val(),
									name: $(this).find('.contract-name').val()});	
				}
			}
		);

		if (contracts.length < 1) {
			$alert.removeClass('hide');
			$alert.text('Please enter at least one valid id-name pair.');
			return false;
		}

		data['contracts'] = contracts;

		// post and refresh page
		$alert.addClass('hide');
		$.post($SCRIPT_ROOT + '/add_group', {data: JSON.stringify(data)}, function() {
			   window.location.reload(true);
			   });
		return false;

	}
);