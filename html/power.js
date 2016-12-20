$(function() {
  var options = {
    lines: { show: true },
    points: { show: false },
    xaxis: { mode: 'time', tickLength: 5 },
    yaxis: { },
  };

  function reload_graph() {
    var url = 'http://192.168.1.201:8080/nodes/8000736D65746572/series/5?npoints=360'; //rx

    // Restrict to last couple of hours
    end = new Date().getTime();
    start = new Date(end - 3600000);
    start = Math.floor(start / 1000);
    end = Math.floor(end / 1000);
    url = url + "&start=" + start + "&end=" + end;

    function onDataReceived(series) {
      $.plot('#power', [series], options);
    }

    $.ajax({
      url: url,
      method: 'GET',
      dataType: 'json',
      success: onDataReceived
    });
  }

  $(document).ready(function () {
    reload_graph();
    window.setInterval(reload_graph, 10000);
  });
});
