

(function () {

'use strict';

var app = angular.module('myApp',[]);



/**
 * Convert a rgb color to hsl color. RGB color should in [0, 254] range and
 * returned HSL is in range of [0., 1.0].
 * Adopted from http://axonflux.com/handy-rgb-to-hsl-and-rgb-to-hsv-color-model-c
 */
function hslToRgb(h, s, l){
    if (arguments.length === 1) {
        s = h.s, vl= h.l, h = h.h;
    }
    var r, g, b;

    if(s == 0){
        r = g = b = l; // achromatic
    }else{
        function hue2rgb(p, q, t){
            if(t < 0) t += 1;
            if(t > 1) t -= 1;
            if(t < 1/6) return p + (q - p) * 6 * t;
            if(t < 1/2) return q;
            if(t < 2/3) return p + (q - p) * (2/3 - t) * 6;
            return p;
        }

        var q = l < 0.5 ? l * (1 + s) : l + s - l * s;
        var p = 2 * l - q;
        r = hue2rgb(p, q, h + 1/3);
        g = hue2rgb(p, q, h);
        b = hue2rgb(p, q, h - 1/3);
    }
    return {
        r: Math.round(r * 255),
        g: Math.round(g * 255),
        b: Math.round(b * 255)
    };
}

/**
 * Convert a rgb color to hsl color. RGB color should in [0, 254] range and
 * returned HSL is in range of [0., 1.0].
 * Adopted from http://axonflux.com/handy-rgb-to-hsl-and-rgb-to-hsv-color-model-c
 */
function rgbToHsl(r, g, b){
    if (arguments.length === 1) {
        g = r.g, b = r.b, r = r.r;
    }
    r /= 255, g /= 255, b /= 255;
    var max = Math.max(r, g, b), min = Math.min(r, g, b);
    var h, s, l = (max + min) / 2;

    if(max == min){
        h = s = 0; // achromatic
    }else{
        var d = max - min;
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
        switch(max){
            case r: h = (g - b) / d + (g < b ? 6 : 0); break;
            case g: h = (b - r) / d + 2; break;
            case b: h = (r - g) / d + 4; break;
        }
        h /= 6;
    }
    return {
        h: h,
        s: s,
        l: l
    };
}
/**
 * Generate gradually changing colors for hitograms from a seed color.
 * @param {(string|object)} seed - A seed color. Could be "red", "blue", "green"
 *      or rgb object.
 * @param {number} n - Number of colors to create
 * @returns {object[]}: Array of colors. Each object has r, g and b property.
 */
function generateGradientColors(seed, n, alpha) {
    // FIXME: This does not properly deal with case n = 1
    var MINL = 0.3; /* minimum l to use */
    var MAXL = 0.8;
    if (typeof seed === 'string') {
        switch (seed) {
            case "red": seed = {"h": 0.0056, "s": 0.64, "l": 0.58}; break;
            case "blue": seed = {"h": 0.58, "s": 0.56, "l": 0.53}; break;
            case "green": seed = {"h": 0.33, "s": 0.39, "l": 0.54}; break;
            default: throw "Invalid color";
        }
    } else {
        seed = rgbToHsl(seed);
    }
    var mid = Math.floor((n + 1) / 2.0);
    var colors = [];
    var l, c;
    for (var i = 0; i < mid; i++) {
        l = MAXL - (MAXL - MINL) * i / (mid - 1);
        c = hslToRgb(seed.h, seed.s, l);
        c.a = alpha;
        colors.push(c);
    }
    for (var i = mid; i < n; i++) {
        colors.push(colors[n - i - 1]);
    }
    return colors;
}

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
                    var colors = generateGradientColors('red', y.length - 1, 0.5);
                    var data = [];
                    var d;
                    for (var j = 0; j < y.length; j++) {
                        d = {
                            "x": x,
                            "y": y[j].data,
                            'type': 'scatter',
                            // 0 width line because fill does not work with mode=none
                            'mode': "lines",
                            'line': {'width': 0},
                            'showlegend': false,
                            "name": y[j].label
                        };
                        if (j > 0) {
                            d.fill = 'tonexty';
                            d.fillcolor = colors[j - 1];
                            d.line.color = colors[j - 1];
                        } else {
                            d.line.color = colors[0];
                        }
                        if (y[j].label == '50%') {
                            d.line.color = 'black';
                            d.line.width = 3;
                        }
                        data.push(d);
                    }
                    var graphId = scope.myCtrl.graphs[i];
                    scope.myCtrl.graphData[graphId] = {
                        "data": data,
                        "layout": {
                            "title": null,
                            "xaxis": {'title': 'iterations'},
                            "yaxis": {'type': 'linear'},
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
                    scope.myCtrl.isReady[graphId] = true;
                }
            );
        });
    };
});


app.controller('hitogramsGraphCtrl', ['$log', '$http', '$interval',
function($log, $http, $interval) {

var self = this;
self.graphs = [];
self.graphData = {};
self.isReady = {};
self.updateInterval= 5;
self.connected = true;
self.next = self.updateInterval;


self.redraw = function (graphId){
    Plotly.newPlot(
      graphId, // the ID of the div
      self.graphData[graphId].data, self.graphData[graphId].layout);
}

self.getEventsData = function (graphId, func) {
    // func should take x, y and display the graph
    $log.info("Getting graph data for " + graphId);
    $http.get($SCRIPT_ROOT + '/histograms/data', {
        'params': {'graphId': graphId}
    }).
    then(function(response) {
        self.connected = true;
        func(response.data.x, response.data.y);
    }, function(response) {
        self.connected = false;
    });
};

self.updateGraph = function (graphId) {
    self.getEventsData(
        graphId,
        function (x, y) {
            for (var i = 0; i < self.graphData[graphId].data.length; i++) {
                self.graphData[graphId].data[i].x = x;
                self.graphData[graphId].data[i].y = y[i].data;
            }
            self.redraw(graphId);
        }
    );
};

$http.get($SCRIPT_ROOT + '/histograms/plots').
then(function(response) {
    $log.info("Getting plots list");
    $.each(response.data, function(i, id) {
        self.isReady[id] = false;
        self.graphs.push(id);
    });
    self.connected = true;
    $log.info("collected " + self.graphs);
}, function(response) {
    self.connected = false;
});


$interval(function () {
    if (self.next == 0) {
        self.next = self.updateInterval;
        $.each(self.graphs, function(i, graphId) {
            if (self.isReady[graphId]){
                self.updateGraph(graphId);
            }
        });
    } else {
        self.next = self.next - 1;
    }
}, 1000);


}]);
}());
