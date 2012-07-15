// called on load, defines drawChart function
$(function() {

	$.drawChart = function(callParams) {

	  callParams = callParams || {};

	  $.getJSON($SCRIPT_ROOT + '/get_chart_data', callParams, function(data) {

			// parse series out of returned data
			var chartSeries = [];
			for (i = 0; i < data.data.length; i++){
				var thisSeries = data.data[i];
				chartSeries.push({
									 name: thisSeries.name,
									 data: thisSeries.data,
									 step: true,
									 tooltip: {
										 valueDecimals: 2
									 }
								 });
			}

			switch(data.chart_type)
			{
			case 'stock_default':
			
			window.chart = new Highcharts.StockChart(
				{
					
					chart: {
						renderTo: 'chart',
						zoomType: 'x'
					},

					xAxis: {
						ordinal: false
					},

					rangeSelector: {
						selected: 1
					},

					title: {
						text: data.title
					},

					series: chartSeries
				})
			}

		});
};

});

// refreshes chart using args when form submitted
$('#chart-controls').submit(
	function() {

		// options boxes
		var $inputs = $('#chart-controls :input');
		var values = {};
		$inputs.each(function() {
						 if ($(this).attr('checked'))
							 values[this.name] = $(this).val();	 
					 });

		// selects
		var $selects = $('#contract-group, #contract-select');
		$selects.each(function() {
						  values[this.name] = $(this).val();
					  });

		// validation
		if (values['contract-group'] === 'no-selection' ||
		   values['contract-select'] === null ||
		   values['contract-select'] === 'no-selection') {
			$('#chart-alert').removeClass('hide');
			return false;
		} else {
			$('#chart-alert').addClass('hide');
		}

		$.drawChart(values);
		return false; // prevents page from reloading
	}
);

