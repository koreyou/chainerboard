

(function () {

'use strict';

var app = angular.module('myApp',[]);


app.config(function($interpolateProvider) {
  $interpolateProvider.startSymbol('[[');
  $interpolateProvider.endSymbol(']]');
});

app.directive('graphContainerShown', function($log) {
    return function(scope, element, attrs) {
        attrs.$observe('graphContainerShown', function (i) {
            scope.myCtrl.getEventsData(
                scope.myCtrl.graphs[i],
                function (x, y){
                    var graphId = scope.myCtrl.graphs[i];
                    scope.myCtrl.graphData[graphId] = {
                        "data": [
                            {
                                "x": x,
                                "y": y,
                                'type': 'scatter',
                                'marker': {'color': 'red'},
                                'name': graphId,
                                'opacity': 0.3
                            },
                            {
                                "x": [],
                                "y": [],
                                "type": 'scatter',
                                "name": graphId + '(window=11)',
                                "marker": {'color': 'red'},
                                "opacity": 0.9
                            }
                        ],
                        "layout": {
                            "title": null,
                            "xaxis": {'title': 'iterations'},
                            "yaxis": {'type': 'log'},
                            "autosize": true,
                            "margin": {
                                'l': 15,
                                'r': 0,
                                'b': 30,
                                't': 0,
                                'pad': 0
                            },
                            "legend": {
                                'x': 0,
                                'y': -0.2
                            },
                            "hidesources": true
                        }
                    };
                    scope.myCtrl.redraw(graphId);
                    scope.myCtrl.graphsToUpdate.push(scope.myCtrl.graphs[i]);
                }
            );
        });
    };
});

function movingAverage(x, y, window){
    if(x.length <= window){
        // Let's return nothing even for x.length == window because it's useless
        return [[], []];
    }
    var i = 0;
    var j = 0;
    // Let's just interpolate y but not x
    var total = 0.0;
    var interpolatedY = [];
    var interpolatedX = [];
    for(; j < window; j++){
        total += y[j];
    }
    var mid = (window + 1) / 2;
    interpolatedY.push(total / window);
    interpolatedX.push(x[i + mid - 1]);
    for (; j < x.length; j++, i++){
        total = total + y[j] - y[i];
        interpolatedY.push(total / window);
        interpolatedX.push(x[i + mid]);
    }
    return {'x': interpolatedX, 'y': interpolatedY};
}

app.controller('eventsGraphCtrl', ['$log', '$http', '$interval',
function($log, $http, $interval) {

var self = this;
self.graphs = [];
self.graphData = {};
self.graphsToUpdate = [];
self.movingAverageWindow = {};

self.redraw = function (graphId){
    // I wanted to use Plotly.update, but it looks like it's buggy
    var ret = movingAverage(
        self.graphData[graphId].data[0].x,
        self.graphData[graphId].data[0].y,
        self.movingAverageWindow[graphId]);
    self.graphData[graphId].data[1].x = ret.x;
    self.graphData[graphId].data[1].y = ret.y;

    Plotly.newPlot(
      graphId, // the ID of the div
      self.graphData[graphId].data, self.graphData[graphId].layout);
}

self.getEventsData = function (graphId, func) {
    // func should take x, y and display the graph
    $log.info("Getting graph data for " + graphId);
    $http.get($SCRIPT_ROOT + '/events/data', {
        'params': {'graphId': graphId}
    }).
    then(function(response) {
        func(response.data.x, response.data.y);
    }, function(response) {
        alert("error");
    });
};

self.updateGraph = function (graphId) {
    self.getEventsData(
        graphId,
        function (x, y) {
            self.graphData[graphId].data[0].x = x;
            self.graphData[graphId].data[0].y = y;
            self.redraw(graphId);
        }
    );
};


self.movingAverageChanged = function (i) {
    if (self.graphsToUpdate.length <= i){
        return;
    }
    var graphId = self.graphsToUpdate[i];
    self.redraw(graphId);
};

$http.get($SCRIPT_ROOT + '/events/plots').
then(function(response) {
    $log.info("Getting plots list");
    $.each(response.data, function(i, id) {
        self.movingAverageWindow[id] = 3;
        self.graphs.push(id);
    });
    $log.info("collected " + self.graphs);
}, function(response) {
    alert("error");
});

$interval(function () {
    $.each(self.graphsToUpdate, function(i, graphId) {
        self.updateGraph(graphId);
    });
}, 5000);


}]);
}());
