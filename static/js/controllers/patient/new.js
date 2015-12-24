(function() {
    app.controller("PatientNewController", ['$http', '$scope', '$location', '$httpParamSerializer', "$q",
    function($http, $scope, $location, $httpParamSerializer, $q) {
        var ctrl = this;
        //console.log("PatientListController");
        if ($scope.main.need_login == true) {
            $location.path("/login");
            return;
        }
        $scope.main.page = 'patient';
        ctrl.data = {}
        ctrl.loading = true;
        ctrl.patient_types = [];
        ctrl.blood_types = [];
        
        ctrl.reset = function() {
            //console.log("reset", arguments);
            ctrl.data = {};
            if (ctrl.blood_types.length) {
                ctrl.data.blood_type = ctrl.blood_types[0];
            }
            if (ctrl.patient_types.length) {
                ctrl.data.type = ctrl.patient_types[0];
            }
        };
        ctrl.create = function(patient, form) {
            //console.log("reset", arguments);
            if(form.$invalid) {
                return;
            }
            var query = {'exact':true, 'q': patient.code, 'fields': 'code'}
            $http.get("/api/v1/patient?" + $httpParamSerializer(query)).then(function(response) {
                var patients = response.data.data;
                if (patients.length == 0) {
                    return $http.post("/api/v1/patient", ctrl.data).then(function(response) {
                        $scope.main.showSuccess("Paciente '" + ctrl.data.name + "' cadastrado", "Sucesso");
                        $location.path("/patient");
                    });
                }
                /* patient.code is duplicated */
                $scope.main.showError("Prontuário '" + ctrl.data.code +"' duplicado", "Erro");
            }, function(err) {
                $scope.main.showError("Paciente não pode ser cadastrado. contate o administrador", "Erro");
            });
        };
        var promisses = {};
        
        promisses['blood_types'] = $http.get("/api/v1/transfusion/blood/types").then(
        function(response) {
            var types = response.data.data.types;
            angular.forEach(types, function(t) {
                ctrl.blood_types.push(t);
            });
            ctrl.reset();
        });
        promisses['patient_types'] = $http.get("/api/v1/patient/types").then(function(response) {
            var types = response.data.data.types;
            angular.forEach(types, function(t) {
                ctrl.patient_types.push(t);
            });
            ctrl.reset();
        });

        $q.all(promisses).then(function(result) {
            ctrl.loading = false;
        }, function(errors, args) {
            ctrl.loading = false;
        });
    }]);
})();

