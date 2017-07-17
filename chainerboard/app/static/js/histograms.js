

(function () {

'use strict';


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


angular.module('myApp').controller('hitogramsGraphCtrl', ['$log', '$http', '$interval', '$q', 'common',
function($log, $http, $interval, $q, common) {

var self = this;
self.sessionId = '';  // 12 character id. Should be empty for uninitialized session
self.graphs = {}; // map from internal hash id to a graph id (str)
self.hiddenGraphs = []; // list of graph ids (str)
self.graphData = {};  // map graph id (str) -> graph obj (object)
self.graphStates = {}; // map graph id (str) -> graph status hash (str)
self.updateInterval= 5;  // Constant for update interval in second
self.connected = true;  // Status of connection (bool)
self.next = 0;  // time until the next update (int)
self.layout = common.createLayout(false);

self.redraw = function (groupId) {
    if (angular.element('#' + groupId).size() == 0) {
        return false;
    }
    // I wanted to use Plotly.update, but it looks like it's buggy
    Plotly.newPlot(
      groupId, // the ID of the div
      self.graphData[self.graphs[groupId]], self.layout);
    return true;
}

self.getPlotData = function (graphId) {
    return $q(function(resolve, reject) {
        $log.info("Getting graph data for " + graphId);
        $http.get($SCRIPT_ROOT + '/histograms/data', {
            'params': {'graphId': graphId}
        }).
        then(function(response) {
            self.connected = true;
            var colors = generateGradientColors('red', response.data.y.length - 1, 0.5);
            var data = [];
            for (var j = 0; j < response.data.y.length; j++) {
                var d = {
                    "x": response.data.x,
                    "y": response.data.y[j].data,
                    'type': 'scatter',
                    // 0 width line because fill does not work with mode=none
                    'mode': "lines",
                    'line': {'width': 0},
                    'showlegend': false,
                    "name": response.data.y[j].label
                };
                if (j > 0) {
                    d.fill = 'tonexty';
                    d.fillcolor = colors[j - 1];
                    d.line.color = colors[j - 1];
                } else {
                    d.line.color = colors[0];
                }
                if (response.data.y[j].label == '50%') {
                    d.line.color = 'black';
                    d.line.width = 3;
                }
                data.push(d);
            }
            self.graphData[graphId] = data;
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
    $http.post($SCRIPT_ROOT + '/histograms/updates',
        {
            'active': self.graphs,
            'states': self.graphStates,
            'sessionId': self.sessionId
        }
    ).
    then(function(response) {
        $log.debug("Received response from /histograms/updates");
        self.connected = true;
        self.sessionId = response.data.sessionId;
        $.each(response.data.newPlots, function(i, newPlot) {
            self.graphData[newPlot.graphId] = [];
            self.graphStates[newPlot.graphId] = '';  // initialize with empty hash
            if (newPlot.type == 'new') {
                self.graphs[newPlot.graphDiv] = newPlot.graphId;
            } else if (newPlot.type == 'hidden') {
                self.hiddenGraphs.append(newPlot.graphId);
            } else {
                self.connected = false;
                $log.error('Invalid newPlot.type ' + newPlot.type);
            }
            $log.debug("Added new plot " + newPlot);
        });

        $.each(response.data.updates, function(i, graphDiv) {
            $q.all([
                self.getPlotData(self.graphs[graphDiv]),
                common.pollWithTimeout(
                function(id) { return function () {
                    return angular.element('#' + id).size() > 0;
                };}(graphDiv), 2000, 200)
            ])
            .then(function (id) { return function () {
                self.redraw(id);
            };}(graphDiv));
        });
    }, function(response) {
        $log.error("Failed to receive resposne /histograms/updates");
        self.connected = false;
    });
};

$interval(function () {
    if (self.next == 0) {
        self.update();
    } else {
        self.next = self.next - 1;
    }
}, 1000);

}]);
}());
