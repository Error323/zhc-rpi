$(function() {
  var options = {
    lines: { show: true },
    points: { show: false },
    xaxis: { mode: 'time', tickLength: 5 },
    yaxis: { },
  };

  function reload_graph() {
    // Restrict to last couple of hours
    end = new Date().getTime();
    start = new Date(end - 3600000*4);
    start = Math.floor(start / 1000);
    end = Math.floor(end / 1000);
    var all_series = [];
		var done = [];

    function createCb(i) {
      return function(data) {
        onDataReceived(i, data);
      };
    }

		var indices = [8, 10, 14];
    for (i = 0; i < indices.length; i++)
    {
      all_series.push([]);
			done.push(false);
      var url = 'http://utrecht.kubiko.nl:8082/nodes/637673797374656D/series/';
      url += indices[i].toString() + "?npoints=1400";
      url += "&start=" + start + "&end=" + end;

      $.ajax({
        url: url,
        method: 'GET',
        dataType: 'json',
        success: createCb(i)
      });
    }


    function onDataReceived(i, series) {
      all_series[i] = series;
			done[i] = true;
			render = true;
			for (j = 0; j < done.length; j++)
				render = render && done[j];
      if (render)
			{
				var data = [
					{label: "boiler", data: all_series[0]},
					{label: "room desired", data: all_series[1]},
					{label: "room actual", data: all_series[2]},
				];
        $.plot('#temperature', data, options);
			}
    }

  }

  $(document).ready(function () {
    reload_graph();
    window.setInterval(reload_graph, 10000);
  });
});
