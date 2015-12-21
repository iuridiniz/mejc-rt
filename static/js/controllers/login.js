(function() {
    app.controller("LoginController", ['$http', '$location', '$scope', '$httpParamSerializer', '$timeout', function($http, $location, $scope, $httpParamSerializer, $timeout) {
        var ctrl = this;
        
        if ($scope.main.need_login == false) {
            $location.path("/").search({});
            return;
        }
        ctrl.forbidden = false;
        $http.get("/api/v1/user/me").then(function(response) {
            /* already logged */
            $location.path("/").search({});
        }, function(err) {
            if (err.status == 403) {
                ctrl.forbidden = true;
            }
        });
        

    }]);
})();