$(function() {
  // constants - computed from energy bills
  var HIGH_EURO = 0.19862318840579712;
  var LOW_EURO = 0.1833774834437086;
  var GAS_EURO = 0.689871794871795;
  var BASE_URL = 'http://utrecht.kubiko.nl:8082/nodes';

  var counter = 0;
  var euro_high = [];
  var euro_low = [];
  var euro_gas = [];
  var raw_data = [];
  var days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

  // plot options
  var options = {
    series: {
      stack: 0,
      bars: {
        show: true,
        barWidth: 0.6
      }
    },
    xaxis: { 
      ticks: []
    },
    yaxis: {
      tickFormatter: euro_formatter
    }
  };

  function update_graph() {
  }

  function euro_formatter(v, axis) {
    return '&euro;' + v;
  }

  function on_data_received(values) {
    counter++;
    raw_data.push([values.timestamp, values.values]);

    if (counter == 8) {
      raw_data.sort();

      for (i = 0; i < 7; i++) {
        date = new Date(raw_data[i+1][0]);
        options.xaxis.ticks.push([i, days[date.getDay()]]);
        euro_low.push([i, (raw_data[i+1][1][0] - raw_data[i][1][0])*LOW_EURO]);
        euro_high.push([i, (raw_data[i+1][1][1] - raw_data[i][1][1])*HIGH_EURO]);
        euro_gas.push([i, (raw_data[i+1][1][4] - raw_data[i][1][4])*GAS_EURO]);
      }

      var data = [
        {label: "Low", data: euro_low }, 
        {label: "High", data: euro_high },
        {label: "Gas", data: euro_gas }
      ];
      $.plot('#cost', data, options);
    }
  }

  function load_graph() {
    now = new Date();
    end = new Date(now.getTime() - (now.getHours()*3600 + now.getMinutes()*60 + now.getSeconds()+1)*1000);
    start = new Date(end.getTime() - 3600*24*7*1000);
    start = Math.floor(start / 1000);

    for (i = 0; i < 8; i++) {
      time = start + i*3600*24;
      var url = BASE_URL + '/8000736D65746572/values/' + time;

      $.ajax({
        url: url,
        method: 'GET',
        dataType: 'json',
        success: on_data_received
      });
    }
  }

  $(document).ready(function () {
    load_graph();
    window.setInterval(update_graph, 10000);
  });
});
