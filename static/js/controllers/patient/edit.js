(function() {
    app.controller("PatientEditController", ['$http', '$timeout', '$scope', '$location', '$routeParams', '$httpParamSerializer', "$q",
    function($http, $timeout, $scope, $location, $routeParams, $httpParamSerializer, $q) {
        var ctrl = this;
        //console.log($routeParams);
        if ($scope.main.need_login == true) {
            $location.path("/login");
            return;
        }
        $scope.main.page = 'patient';
        
        ctrl.patient_key = $routeParams.key;

        ctrl.patient_data = {}
        ctrl.loading = true;
        ctrl.patient_types = [];
        ctrl.blood_types = [];
        ctrl.save = function(patient, form) {
            if(form.$invalid) {
                return;
            }
            $timeout(function() {
                $http.put("/api/v1/patient", patient).then(function(response) {
                    $scope.main.showSuccess("Paciente '" + patient.name + "' atualizado", "Salvo");
                    $location.path("/patient");
                });
            });
        };
        var promisses = {};
        
        promisses['blood_types'] = $http.get("/api/v1/transfusion/blood/types").then(
          function(response) {
            var types = response.data.data.types;
            angular.forEach(types, function(t) {
                ctrl.blood_types.push(t);
            });
        });
        
        promisses['patient_types'] = $http.get("/api/v1/patient/types").then(
          function(response) {
            var types = response.data.data.types;
            angular.forEach(types, function(t) {
                ctrl.patient_types.push(t);
            });
        });
        
        promisses['patient'] = $http.get("/api/v1/patient/" + ctrl.patient_key).then(
        function(response) {
            //console.log(response);
            patient_data = response.data.data;
            patient_data.code = parseInt(patient_data.code); 
            ctrl.patient_data = response.data.data;
           
        }, function(err) {
           if (err.status == 404) {
               $scope.main.showWarning("Paciente não encontrado", "Não encontrado");
               $location.path("/patient");
           }
        });

        $q.all(promisses).then(function(result) {
            ctrl.loading = false;
        }, function(errors, args) {
            ctrl.loading = false;
        });
    }]);
})();

