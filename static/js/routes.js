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
        $routeProvider.when("/", {
            redirectTo: "/dashboard"
        });
    });
    app.config(function($routeProvider) {
        $routeProvider.when("/login", {
            templateUrl : "templates/login.html",
            controller : "LoginController as ctrl"
        });
    });
    app.config(function($routeProvider) {
        $routeProvider.when("/blank", {
            templateUrl : "templates/blank.html",
        });
    });
    app.config(function($locationProvider) {
        $locationProvider.html5Mode(false);
    });
})();