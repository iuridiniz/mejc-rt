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
            $http.get("/api/v1/patient/code/" + ctrl.data.code).then(function(success) {
                /* duplicated code */
                $scope.main.showError("Prontuário '" + ctrl.data.code +"' duplicado", "Erro");
            }, function(err) {
                if (err.status == 404) {
                    $http.post("/api/v1/patient", ctrl.data).then(function(response) {
                        $scope.main.showSuccess("Paciente '" + ctrl.data.name + "' cadastrado", "Sucesso");
                        $location.path("/patient");
                    });
                    return;
                } 
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

