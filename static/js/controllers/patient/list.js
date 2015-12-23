(function() {

    app.controller("PatientListController", ['$http', '$scope', '$httpParamSerializer',
    function($http, $scope, $httpParamSerializer) {
        //({fields:fields})
        var ctrl = this;
        //console.log("PatientListController");
        if ($scope.main.need_login == true) {
            $location.path("/login");
            return;
        }

        ctrl.patients = [];
        ctrl.page = 1;
        ctrl.filter = "";
        ctrl.fields = "name,code";
        ctrl.offset = 0;
        ctrl.max = 20;
        
        ctrl.total = 0;
        ctrl.count = 0;
        

        ctrl.prev_link = null;
        ctrl.next_link = null;
        ctrl.requestPatients = function(url) {
            return $http.get(url).then(function(ret) {
                var data = ret.data;
                var patients = data.data;
                ctrl.patients = patients;
                //console.log(ctrl.patients);
                ctrl.prev_link = null;
                ctrl.next_link = null;
                ctrl.cur_link = url;
                if (data.offset > 0) {
                    ctrl.prev_link = data.prev;
                }
                if (data.offset + patients.length < data.count) {
                    ctrl.next_link = data.next;
                }
                
                ctrl.total = data.total;
                ctrl.count = data.count;
            });
        };
        
        ctrl.goToNext = function() {
            if (ctrl.next_link) {
                ctrl.requestPatients(ctrl.next_link);
                ctrl.page += 1;
            }
        };
        ctrl.goToPrev = function() {
            if (ctrl.prev_link) {
                ctrl.requestPatients(ctrl.prev_link).then(function() {
                    ctrl.page -= 1;
                });
            }
        };
        ctrl.buildUrl = function() {
            var query = {
                    offset: ctrl.offset,
                    max: ctrl.max,
                    q: ctrl.filter,
                    fields: ctrl.fields,
            };
            return  "/api/v1/patient/?" + $httpParamSerializer(query)
        };
        ctrl.requestPatients(ctrl.buildUrl());
        
    }]);
})();

