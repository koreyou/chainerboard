

(function () {

'use strict';

angular.module('myApp').controller('eventsGraphCtrl', ['$log', '$http', '$interval', '$q', '$timeout', 'common',
function($log, $http, $interval, $q, $timeout, common) {

var self = this;
self.sessionId = '';  // 12 character id. Should be empty for uninitialized session
self.groups = {}; // list of dict (groupId (str) -> list of graph ids (str))
self.hiddenGraphs = []; // list of graph ids (str)
self.graphData = {};  // map graph id (str) -> graph obj (object)
self.graphStates = {}; // map graph id (str) -> graph status hash (str)
self.movingAverageWindow = {}; // map group id (str) -> window size (int)
self.isLogarithmatic = {}; // map group id (str) -> if logarithmatic (bool)
self.graphNames = {}; // map group id (str) -> graph name (str)
self.updateInterval= 5;  // Constant for update interval in second
self.connected = true;  // Status of connection (bool)
self.next = 0;  // time until the next update (int)


self.redraw = function (groupId) {
    if (angular.element('#' + groupId).size() == 0) {
        return false;
    }
    var data = [];
    $.each(self.groups[groupId], function (i, graphId) {
        var ret = common.movingAverage(
            self.graphData[graphId][0].x,
            self.graphData[graphId][0].y,
            self.movingAverageWindow[groupId]);
        self.graphData[graphId][1].x = ret.x;
        self.graphData[graphId][1].y = ret.y;
        data = data.concat(self.graphData[graphId]);
    });
    var layout = common.createLayout(self.isLogarithmatic[groupId]);
    // I wanted to use Plotly.update, but it looks like it's buggy
    Plotly.newPlot(
      groupId, // the ID of the div
      data, layout);
    return true;
}

self.getEventsData = function (graphId) {
    return $q(function(resolve, reject) {
        $log.info("Getting graph data for " + graphId);
        $http.get($SCRIPT_ROOT + '/events/data', {
            'params': {'graphId': graphId}
        }).
        then(function(response) {
            self.connected = true;
            self.graphData[graphId][0].x = response.data.x;
            self.graphData[graphId][0].y = response.data.y;
            self.graphStates[graphId] = response.data.stateHash;
            $log.info("Updated graph " + graphId + " with hash " + response.data.stateHash);
            resolve("operation successful");
        }, function(response) {
            self.connected = false;
            reject("operation unsuccessful");
        });
    });
};

self.update = function() {
    $log.info("Getting plots list");
    $http.post($SCRIPT_ROOT + '/events/updates',
        {
            'active': self.groups,
            'states': self.graphStates,
            'sessionId': self.sessionId
        }
    ).
    then(function(response) {
        $log.debug("Received response from /events/updates");
        self.connected = true;
        self.sessionId = response.data.sessionId;
        $.each(response.data.newPlots, function(i, newPlot) {
            self.graphData[newPlot.graphId] = [
                {
                    "x": [],
                    "y": [],
                    'type': 'scatter',
                    'marker': {'color': 'red'},
                    'showlegend': false,
                    'opacity': 0.3
                },
                {
                    "x": [],
                    "y": [],
                    "type": 'scatter',
                    "name": newPlot.graphId,
                    "marker": {'color': 'red'},
                    "opacity": 0.9
                }
            ];
            self.graphStates[newPlot.graphId] = '';  // initialize with empty hash
            if (newPlot.type == 'new') {
                // Create new group
                self.movingAverageWindow[newPlot.groupId] = 3;
                self.isLogarithmatic[newPlot.groupId] = false;
                self.graphNames[newPlot.groupId] = newPlot.name;
                self.groups[newPlot.groupId] = [newPlot.graphId];
            } else if (newPlot.type == 'hidden') {
                self.hiddenGraphs.append(newPlot.graphId);
            } else if (newPlot.type == 'append') {
                self.groups[newPlot.groupId].push(newPlot.groupId);
            } else {
                self.connected = false;
                $log.error('Invalid newPlot.type ' + newPlot.type);
            }
            $log.debug("Added new plot " + newPlot);
        });

        for (var groupId in response.data.updates) {
            if (response.data.updates.hasOwnProperty(groupId)) {
                var promises = [];
                $.each(response.data.updates[groupId], function(i, graphId) {
                    promises.push(self.getEventsData(graphId));
                });
                promises.push(common.pollWithTimeout(
                    function(id) { return function () {
                        return angular.element('#' + id).size() > 0;
                    };}(groupId), 2000, 200));

                $q.all(promises).then(function (id) { return function () {
                    self.redraw(id);
                };}(groupId));
            }
        }
    }, function(response) {
        $log.error("Failed to receive resposne /events/updates");
        self.connected = false;
    });
}



$interval(function () {
    if (self.next == 0) {
        self.update();
    } else {
        self.next = self.next - 1;
    }
}, 1000);


}]);
}());
