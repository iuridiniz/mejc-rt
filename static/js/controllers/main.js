(function() {
    app.controller("MainController", ['$http', '$location', '$httpParamSerializer', function($http, $location, $httpParamSerializer) {
        var main = this;
        main.user = null;
        main.need_login = false;
        main.google_login_url = null;
        main.google_logout_url = null;
        main.message = null;
        main.showMessage = function(type, message, title) {
            classes = { 
                "error": 'box-danger',
                "warning": 'box-warning',
                "success": 'box-success',
                "info": 'box-info'
            };
            main.message = { content: message, title: title, 'class': classes[type]}
        };
        
        main.showInfo = function(message, title) {
            return main.showMessage('info', message, title);
        };
        
        main.showWarning = function(message, title) {
            return main.showMessage('warning', message, title);
        };
        main.showSuccess = function(message, title) {
            return main.showMessage('success', message, title);
        };
        main.showError = function(message, title) {
            return main.showMessage('error', message, title);
        };

        
        $http.get("/api/v1/user/me").then(function(response) {
            //console.log(response.data.data.user);
            main.user = response.data.data.user;
            main.user.since = new Date(main.user.added_at);
        }, function(err) {
            main.need_login = true;
            if (err.status == 401 || err.status == 403 ) {
                $location.path("/login");
            }
        });
        var query_string = $httpParamSerializer({'continue': window.location.origin})
        
        $http.get("/api/v1/user/login/google" + "?" +  query_string)
          .then(function(response) {
            main.google_login_url = response.data['continue'];
        });
        
        $http.get("/api/v1/user/logout/google" + "?" +  query_string)
        .then(function(response) {
          main.google_logout_url = response.data['continue'];
        });
        
        //main.showInfo("Conteudo", "Titulo");
        //main.showInfo("Conteudo");
        //main.showError("Conteudo", "Titulo");
        //main.showError("Conteudo");
        //main.showWarning("Conteudo", "Titulo");
        //main.showWarning("Conteudo");
        //main.showSuccess("Conteudo", "Titulo");
        //main.showSuccess("Conteudo");
    }]);
})();