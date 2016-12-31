$(function() {
  // constants - computed from energy bills
  const HIGH_EURO = 0.19862318840579712;
  const LOW_EURO = 0.1833774834437086;
  const GAS_EURO = 0.689871794871795;
  const BASE_URL = 'http://utrecht.kubiko.nl:8082/nodes';
  const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const SMETER_METRICS = [0, 1, 4];
  const BOILER_METRICS = [2, 3];
  const NUM_DAYS = 7;

  var counter = 0;
  var raw_data = [];

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


  function euro_formatter(v, axis) {
    return '&euro;' + v;
  }


  function callback(m) {
    return function(data) { on_data_received(m, data); };
  }


  function on_data_received(metric, values) {
    counter++;
    raw_data.push([metric, values]);

    if (counter == (SMETER_METRICS.length + BOILER_METRICS.length + 2)) {
      raw_data.sort();

      for (i = 0; i < SMETER_METRICS.length; i++) {
        metric = SMETER_METRICS[i];
        raw_data[metric][1].push([raw_data[5][1].timestamp, raw_data[5][1].values[metric]]);
      }

      for (i = 0; i < BOILER_METRICS.length; i++) {
        metric = BOILER_METRICS[i];
        raw_data[metric][1].push([raw_data[6][1].timestamp, raw_data[6][1].values[metric]]);
      }

      var euro_high = [];
      var euro_low = [];
      var euro_dhw = [];
      var euro_ch = [];

      for (i = 0; i < NUM_DAYS; i++) {
        date = new Date(raw_data[0][1][i][0]);
        options.xaxis.ticks.push([i, DAYS[date.getDay()]]);

        euro_low.push([i, (raw_data[0][1][i+1][1] - raw_data[0][1][i][1])*LOW_EURO]);
        euro_high.push([i, (raw_data[1][1][i+1][1] - raw_data[1][1][i][1])*HIGH_EURO]);
        gas_total = (raw_data[4][1][i+1][1] - raw_data[4][1][i][1]);
        dhw = raw_data[2][1][i][1] / raw_data[3][1][i][1];
        euro_dhw.push([i, gas_total*dhw*GAS_EURO]);
        euro_ch.push([i, gas_total*(1.0-dhw)*GAS_EURO]);
      }

      var data = [
        {label: "low", data: euro_low }, 
        {label: "high", data: euro_high },
        {label: "dhw", data: euro_dhw },
        {label: "ch", data: euro_ch }
      ];
      $.plot('#cost', data, options);
    }
  }


  function load_graph() {
    counter = 0;
    raw_data = [];
    options.xaxis.ticks = [];
    now = new Date();
    end = new Date(now.getTime() - (now.getHours()*3600 + now.getMinutes()*60 + now.getSeconds())*1000);
    end = Math.floor(end.getTime()/1000);
    start = end - 3600*24*(NUM_DAYS-1);
    
    var url = BASE_URL + '/8000736D65746572/values/';

    $.ajax({
      url: url,
      method: 'GET',
      dataType: 'json',
      success: callback(5)
    });

    for (i = 0; i < SMETER_METRICS.length; i++) {
      metric = SMETER_METRICS[i];
      url = BASE_URL + '/8000736D65746572/series/' + metric + '?npoints=' + NUM_DAYS + '&start=' + start + '&end=' + end;

      $.ajax({
        url: url,
        method: 'GET',
        dataType: 'json',
        success: callback(metric)
      });
    }
    
    url = BASE_URL + '/637673797374656D/values/';

    $.ajax({
      url: url,
      method: 'GET',
      dataType: 'json',
      success: callback(6)
    });

    for (i = 0; i < BOILER_METRICS.length; i++) {
      metric = BOILER_METRICS[i];
      url = BASE_URL + '/637673797374656D/series/' + metric + '?npoints=' + NUM_DAYS + '&start=' + start + '&end=' + end;

      $.ajax({
        url: url,
        method: 'GET',
        dataType: 'json',
        success: callback(metric)
      });
    }
  }

  $(document).ready(function () {
    load_graph();
    window.setInterval(load_graph, 10000);
  });
});
