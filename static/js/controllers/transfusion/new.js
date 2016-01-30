(function() {
    app.controller("TransfusionNewController", ['$http', '$timeout', '$scope', '$location', '$httpParamSerializer', "$q", '$routeParams',
    function($http, $timeout, $scope, $location, $httpParamSerializer, $q, $routeParams) {
        var ctrl = this;
        if ($scope.main.need_login == true) {
            $location.path("/login");
            return;
        }
        $scope.main.page = 'transfusion';
        ctrl.transfusion = {}
        ctrl.blood_types = [];
        ctrl.locals = [];
        ctrl.blood_contents = [];
        ctrl.patient_key = $routeParams.key;
        ctrl.patient_data = null;

        ctrl.reset = function($form) {
            ctrl.transfusion = {};
            if ($form) {
                $form.$setPristine();
            }
            if (ctrl.locals.length) {
                ctrl.transfusion.local = ctrl.locals[0];
            }
            ctrl.query = "";
            ctrl.transfusion.date = new Date();
            ctrl.transfusion.patient = ctrl.patient_data;
            /* default tags for new patient */
            ctrl.transfusion.tags = ["naovisitado"];
        };

        ctrl.create = function(transfusion, form) {
            //console.log(form);
            if(form.$invalid) {
                return;
            }

            var query = {'exact':true, 'q': transfusion.code, 'fields': 'code'}
            $http.get("/api/v1/transfusion?" + $httpParamSerializer(query)).then(function(response) {
                var transfusions = response.data.data;
                if (transfusions.length == 0) {
                    return $http.post("/api/v1/transfusion", transfusion).then(function(response) {
                        $scope.main.showSuccess("Transfusão para '" + transfusion.patient.name + "' cadastrada", "Sucesso");
                        $location.path("/transfusion");
                    });
                }
                /* patient.code is duplicated */
                $scope.main.showError("Código '" + transfusion.code +"' duplicado", "Erro");
            }, function(err) {
                $scope.main.showError("Transfusão não pode ser cadastrada. contate o administrador", "Erro");
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

        promisses['locals'] = $http.get("/api/v1/transfusion/locals").then(
        function(response) {
            var types = response.data.data.locals;
            angular.forEach(types, function(t) {
                ctrl.locals.push(t);
            });
        });

        promisses['contents'] = $http.get("/api/v1/transfusion/blood/contents").then(
        function(response) {
            var contents = response.data.data.contents;
            angular.forEach(contents, function(t) {
                ctrl.blood_contents.push(t);
            });
        });

        if (ctrl.patient_key) {
            promisses['patient'] = $http.get("/api/v1/patient/" + ctrl.patient_key).then(
            function(response) {
                patient_data = response.data.data[0];
                patient_data.code = parseInt(patient_data.code);
                ctrl.patient_data = patient_data;
            }, function(err) {
               if (err.status == 404) {
                   $scope.main.showWarning("Paciente não encontrado", "Não encontrado");
                   $location.path("/transfusion");
               }
            });
        }

        $q.all(promisses).then(function(result) {
            ctrl.reset();
            ctrl.loading = false;
        }, function(errors, args) {
            ctrl.loading = false;
        });

        ctrl.transfusionFormReady = function($form) {
          var combining = /[\u0300-\u036F]/g;
          $("#query").typeahead({
            source: function(q, setEntries) {
                var query = {
                        offset: 0,
                        max: 10,
                        q: q,
                        fields: "name,code",
                };
                var url =  "/api/v1/patient/?" + $httpParamSerializer(query);
                $http.get(url).then(function(response){
                    var data = new Array();
                    angular.forEach(response.data.data, function(v){
                        if (typeof String.prototype.normalize === "function") { /* ECMA6 feature */
                            v.normalized_name=v.name.normalize('NFKD').replace(combining, '');
                        } else {
                            v.normalized_name = v.name;
                        }
                        data.push(v);
                    });
                    setEntries(data);
                });
            },
            displayText: function(entry) {
                return entry.code + " | " + entry.normalized_name;
            },
            afterSelect: function(entry) {
                $scope.$apply(function() {
                    ctrl.transfusion.patient = entry;
                    ctrl.query = entry.name;
                    if ($form) {
                        $form.$setPristine();
                    }
                });
            },
            minLength: 0,
            items: 10,
            delay: 200,
            autoSelect: false,
            showHintOnFocus: true,
        });
      };
    }]);
})();

