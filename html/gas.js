$(function() {
  var options = {
    series: {
      pie: { show: true }
    }
  };

  var raw = [[], [], [], []];
  var ready = [false, false, false, false];
  var data = [];

  function load_data() {
    end = new Date().getTime();
    start = new Date(end - 3600*24*1000);
    start = Math.floor(start / 1000);
    end = Math.floor(end / 1000);

    function createCb(i) {
      return function(data) {
        onDataReceived(i, data);
      };
    }

    for (i = 1; i < 4; i++) {
      var url = 'http://192.168.1.201:8080/nodes/637673797374656D/series/';
      url += i.toString() + "?npoints=" + 360*24;
      url += "&start=" + start + "&end=" + end;

      $.ajax({
        url: url,
        method: 'GET',
        dataType: 'json',
        success: createCb(i)
      });
    }
  }

  function onDataReceived(i, series) {
    switch (i) {
      case 1: // central heating
        raw[0] = series;
        ready[0] = true;
        break;
      case 2: // domestic hot water
        raw[1] = series;
        ready[1] = true;
        break;
      case 3: // flame status
        raw[2] = series;
        ready[2] = true;
        break;
      case 4: // gas usage
        raw[3] = series;
        ready[3] = true;
        break;
    };

    var isReady = true;
    for (j = 0; j < ready.length; j++)
      isReady = isReady && ready[j];

    if (isReady) {
      for (j = 0; j < ready.length; j++)
        ready[j] = false;

      // compute gas usage per hour
      // compute 
    }
  }

  function reload_graph() {
    $.plot('#gas', data, options);
  }

  $(document).ready(function () {
    load_data();
    window.setInterval(reload_graph, 10000);
  });
});
