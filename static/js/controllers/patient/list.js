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
        
        ctrl.loading = true;

        ctrl.patients = [];
        ctrl.page = 1;
        ctrl.filter = "";
        ctrl.applied_filter = null;
        ctrl.fields = "name,code";
        ctrl.offset = 0;
        ctrl.max = 20;
        
        ctrl.total = 0;
        ctrl.count = 0;

        ctrl.prev_link = null;
        ctrl.next_link = null;
        ctrl.requestPatients = function(url) {
            ctrl.loading = true;
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
                ctrl.offset = data.offset;
                ctrl.page = Math.floor(data.offset / data.max) + 1;
                ctrl.total = data.total;
                ctrl.count = data.count;
                ctrl.applied_filter = data.filter;
                ctrl.loading = false;
            });
        };
        
        ctrl.goToNext = function() {
            if (ctrl.next_link) {
                ctrl.requestPatients(ctrl.next_link);
            }
        };
        ctrl.goToPrev = function() {
            if (ctrl.prev_link) {
                ctrl.requestPatients(ctrl.prev_link);
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
        
        ctrl.searchKeyUp = function(ev) {
            //console.log("SearchKeyUp", ev);
            if (ev.keyCode == 13) {
                ev.preventDefault();
                ctrl.searchClick();
            }
        };
        ctrl.clearSearchClick = function() {
            console.log("clearSearchClick");
            ctrl.filter = "";
            ctrl.offset = 0;
            ctrl.requestPatients(ctrl.buildUrl());
        };
        ctrl.searchClick = function() {
            //console.log("searchClick");
            ctrl.offset = 0;
            ctrl.requestPatients(ctrl.buildUrl());
        };
        ctrl.requestPatients(ctrl.buildUrl());
        
    }]);
})();

