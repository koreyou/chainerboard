

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
            Plotly.plot(scope.myCtrl.graphs[i].name, // the ID of the div
                scope.myCtrl.graphs[i].graph.data,
                scope.myCtrl.graphs[i].graph.layout || {});

        });
    };
});

app.controller('eventsGraphCtrl', ['$log', '$http',
function($log, $http) {

var self = this;
self.graphs = [];

$http.get($SCRIPT_ROOT + '/events/data').
then(function(response) {
    $log.info("success");
    var d = response.data;
    $.each(d.graphs, function(i, g) {
        self.graphs.push({
            'name': d.ids[i],
            'graph': g
        });
    });

}, function(response) {
    alert("error");
});


}]);
}());
