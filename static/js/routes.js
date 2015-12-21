/*******************************************************************/
/* ROUTES */
/*******************************************************************/
(function() {
    app.config(function($routeProvider) {
      $routeProvider.when("/dashboard", {
          templateUrl : "templates/dashboard.html",
          controller : "DashboardController as ctrl"
      });
    });
    app.config(function($routeProvider) {
        $routeProvider.when("/login", {
            templateUrl : "templates/login.html",
            controller : "LoginController as ctrl"
        });
      });
    app.config(function($locationProvider) {
        $locationProvider.html5Mode(false);
    });
})();