(function() {
    app.controller("PatientListController", ['$route', '$timeout', '$http', '$location', '$scope', '$httpParamSerializer', "$uibModal",
    function($route, $timeout, $http, $location, $scope, $httpParamSerializer, $uibModal) {
        //({fields:fields})
        var ctrl = this;
        //console.log("PatientListController");
        if ($scope.main.need_login == true) {
            $location.path("/login");
            return;
        }
        $scope.main.page = 'patient';

        ctrl.loading = true;

        ctrl.patients = [];
        ctrl.page = 1;
        ctrl.filter = "";
        ctrl.applied_filter = null;
        ctrl.fields = "name,code";
        ctrl.offset = 0;
        ctrl.max = 10;
        
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
        
        ctrl.edit = function(key) {
            $location.path("/patient/" + key + "/edit");
        };
        ctrl.deleteConfirm = function(p) {
            var modalInstance = $uibModal.open({
                animation: true,
                templateUrl: 'templates/patient/delete.html',
                controller: 'PatientDeleteController as modal',
                windowClass: 'modal-danger',
                resolve: {
                    patient: function() {
                        return p;
                    }
                }
            });
            modalInstance.result.then(function (ret) {
                console.log(arguments);
                //console.log('Modal confirm (patient' + patient + "') at " + new Date());
                if (! ret.success) {
                    $scope.main.showError("Não pude apagar '" + ret.patient.name + "'", "Erro");
                    return;
                }
                $scope.main.showSuccess("Paciente '" + ret.patient.name + "' apagado", "Sucesso");
                $route.reload();
            }, function () {
                //console.log('Modal dismissed at ' + new Date());
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
            //console.log("clearSearchClick");
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

