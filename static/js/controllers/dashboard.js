(function() {
    app.controller("DashboardController", 
            ['$http', '$httpParamSerializer', '$q', '$location', '$scope', "$timeout",
    function($http, $httpParamSerializer, $q, $location, $scope, $timeout) {
        var ctrl = this;
        ctrl.loading = true;
        ctrl.stats = {};
        if ($scope.main.need_login == true) {
            $location.path("/login");
            return;
        }

        ctrl.updateStats = function () {
            //console.log("update", ctrl.stats);
            /* animate patients */
            var animate_effect_duration = 2000;
            $("#qtd-patients").numerator({
                duration: animate_effect_duration,
                delimiter: " ",
                toValue: ctrl.stats.patients.all,
                onStep: function(v, fx) {},
                onComplete: function() {},
            });
            
            /* animate transfusions */
            $("#qtd-transfusions").numerator({
                duration: animate_effect_duration,
                delimiter: " ",
                toValue: ctrl.stats.transfusions.all,
                onStep: function(v, fx) {},
                onComplete: function() {},
            });
            
            /* animate reactions */
            $("#qtd-reactions").numerator({
                duration: animate_effect_duration,
                delimiter: " ",
                toValue: ctrl.stats.transfusions.rt,
                onStep: function(v, fx) {},
                onComplete: function() {},
            });
            if (ctrl.stats.transfusions.rt) {
                /* animate percent reactions */
                var percent = (1-(ctrl.stats.transfusions.rt/ctrl.stats.transfusions.all)) * 100;
                $("#percent-no-reactions").numerator({
                    duration: animate_effect_duration,
                    rounding: 2,
                    toValue: percent,
                    onStep: function(v, fx) {
                        $("#percent-no-reactions-bar").css("width", percent + "%");
                    },
                    onComplete: function() {},
                });
            }
            $timeout(function() {
                ctrl.loading = false;
            }, 200);

        };
        
        promisses = {};
        promisses['stats.transfusions'] = $http.get("/api/v1/transfusion/stats?tags=all,rt").then(function(response) {
            //console.log(response);
            ctrl.stats.transfusions = response.data.data.stats;
        });
        
        promisses['stats.patients'] = $http.get("/api/v1/patient/stats").then(function(response) {
            //console.log(response);
            ctrl.stats.patients = response.data.data.stats;
        });
        
        $q.all(promisses).then(function(result) {
            //console.log("OK", result);
            /* ctrl.loading = false; */
            ctrl.stats_loaded = true;
            ctrl.updateStats();
        }, function(errors, args) {
            ctrl.loading = false;
        });
        
    }]);
})();