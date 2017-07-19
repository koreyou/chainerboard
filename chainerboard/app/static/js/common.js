

(function () {

'use strict';

angular.module('myApp',[])
.config(function($interpolateProvider) {
  $interpolateProvider.startSymbol('[[');
  $interpolateProvider.endSymbol(']]');
})
.service('common', ['$q', '$timeout',
function($q, $timeout) {

var self = this;

self.argDefault = function (arg, defaultValue) {
    return arg = typeof arg !== 'undefined' ? arg : defaultValue;
};

self.movingAverage = function(x, y, window){
    if(x.length <= window){
        // Let's return nothing even for x.length == window because it's useless
        return [[], []];
    }
    var j = 0;
    // Let's just interpolate y but not x
    var interpolatedY = [];
    var interpolatedX = [];
    var mid = (window + 1) / 2;
    while (j < x.length) {
        var total = 0.0;
        for(var i = 0; i < window; j++){
            if (y[j] == 'nan') {
                // just reset i and total
                i = 0;
                total = 0.0;
            } else {
                i = i + 1;
                total += y[j];
                if (j > mid) {
                    interpolatedY.push('nan');
                    interpolatedX.push(x[j - mid + 1]);
                }
            }
        }
        interpolatedY.push(total / window);
        interpolatedX.push(x[j - mid]);
        for (; j < x.length; j++){
            if (y[j] == 'nan') {
                break;
            }
            var i = j - mid + 1;
            total = total + y[j] - y[j - window];
            interpolatedY.push(total / window);
            interpolatedX.push(x[i]);
        }

    }
    return {'x': interpolatedX, 'y': interpolatedY};
};


self.createLayout = function (isLogarithmatic) {
    var yaxisType = isLogarithmatic ? 'log' : 'linear';
    return {
        "title": null,
        "xaxis": {'title': 'iterations'},
        "yaxis": {'type': yaxisType},
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
    };
};

self.pollWithTimeout = function(fn, timeout, interval, initialDelay) {
    interval = self.argDefault(interval, 10);
    initialDelay = self.argDefault(initialDelay, 0);
    return $q(function(resolve, reject) {
        $timeout(function() {
            if (fn()) {
                // condition fulfilled
                resolve();
            } else {
                var newInterval = timeout - interval - initialDelay;
                if (newInterval > 0) {
                    self.pollWithTimeout(fn, newInterval, interval)
                    .then(
                        function() {resolve();},
                        function() {reject();}
                    );
                } else {
                    reject();
                }
            }
        }, interval + initialDelay);
    });
};

}]);

}());
