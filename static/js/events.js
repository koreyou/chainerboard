

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
                function (graph){
                    Plotly.plot(scope.myCtrl.graphs[i], // the ID of the div
                        graph.data,
                        graph.layout || {});
                }
            );
        });
    };
});

app.controller('eventsGraphCtrl', ['$log', '$http', '$interval',
function($log, $http, $interval) {

var self = this;
self.graphs = [];

self.getEventsData = function (graphId, func) {
    // func should take "graph" and display the graph
    $log.info("Getting graph data for " + graphId);
    $http.get($SCRIPT_ROOT + '/events/data', {
        'params': {'graphId': graphId}
    }).
    then(function(response) {
        func(response.data);
    }, function(response) {
        alert("error");
    });
};

self.redraw = function (graphId) {
    self.getEventsData(
        graphId,
        function (graph){
            Plotly.update(
              graphId, // the ID of the div
              graph.data, {});
        }
    );
};

$http.get($SCRIPT_ROOT + '/events/plots').
then(function(response) {
    $log.info("Getting plots list");
    $.each(response.data, function(i, id) {
        self.graphs.push(id);
    });
    $log.info("collected " + self.graphs);
}, function(response) {
    alert("error");
});

$interval(function () {
    $.each(self.graphs, function(i, graphId) {
        self.redraw(graphId);
    });
}, 5000);


}]);
}());
