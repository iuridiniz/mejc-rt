(function() {
    app.controller("TransfusionListController", ['$http', '$location', '$scope', '$httpParamSerializer', '$timeout', function($http, $location, $scope, $httpParamSerializer, $timeout) {
        var ctrl = this;
        if ($scope.main.need_login == true) {
            $location.path("/login").search({});
            return;
        }
        $scope.main.page = 'transfusion';

        ctrl.transfusions = [];
        ctrl.page = 1;
        ctrl.filter = "";
        ctrl.applied_filter = null;
        ctrl.fields = "patient.name,code,patient.code";
        ctrl.offset = 0;
        ctrl.max = 10;
        ctrl.total = 0;
        ctrl.count = 0;

        ctrl.prev_link = null;
        ctrl.next_link = null;
        ctrl.requestTransfusions = function(url) {
            ctrl.loading = true;
            return $http.get(url).then(function(response) {
                var data = response.data;
                var transfusions = data.data;
                ctrl.transfusions = transfusions;
                ctrl.prev_link = null;
                ctrl.next_link = null;
                ctrl.cur_link = url;
                if (data.offset > 0) {
                    ctrl.prev_link = data.prev;
                }
                if (data.offset + transfusions.length < data.count) {
                    ctrl.next_link = data.next;
                }
                ctrl.offset = data.offset;
                ctrl.page = Math.floor(data.offset / data.max) + 1;
                ctrl.total = data.total;
                ctrl.count = data.count;
                ctrl.applied_filter = data.q;
                ctrl.loading = false;
            }, function(err) {
                $scope.main.showError("Ocorreu um erro ao realizar sua consulta, por favor contacte o administrador", "Erro");
                ctrl.loading = false;
            });
        };
        
        ctrl.goToNext = function() {
            if (ctrl.next_link) {
                ctrl.requestTransfusions(ctrl.next_link);
            }
        };
        ctrl.goToPrev = function() {
            if (ctrl.prev_link) {
                ctrl.requestTransfusions(ctrl.prev_link);
            }
        };
        ctrl.buildUrl = function() {
            var query = {
                    offset: ctrl.offset,
                    max: ctrl.max,
                    q: ctrl.filter,
                    fields: ctrl.fields,
            };
            return  "/api/v1/transfusion?" + $httpParamSerializer(query)
        };
        ctrl.searchKeyUp = function(ev) {
            if (ev.keyCode == 13) {
                ev.preventDefault();
                ctrl.searchClick();
            }
        };
        ctrl.clearSearchClick = function() {
            ctrl.filter = "";
            ctrl.offset = 0;
            ctrl.requestTransfusions(ctrl.buildUrl());
        };
        ctrl.searchClick = function() {
            //console.log("searchClick");
            ctrl.offset = 0;
            ctrl.requestTransfusions(ctrl.buildUrl());
        };
        
        ctrl.action = function() {
            console.log(arguments);
        }
        ctrl.requestTransfusions(ctrl.buildUrl());
    }]);
})();