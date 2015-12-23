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
    /* Patient pages */
    app.config(function($routeProvider) {
        $routeProvider.when("/patient", {
            templateUrl : "templates/patient/list.html",
            controller : "PatientListController as ctrl"
        });
    });
    app.config(function($routeProvider) {
        $routeProvider.when("/patient/new", {
            templateUrl : "templates/patient/new.html",
            controller : "PatientNewController as ctrl"
        });
    });
    /* OTHERS PAGES */
    app.config(function($routeProvider) {
        $routeProvider.when("/blank", {
            templateUrl : "templates/blank.html",
        });
    });

    app.config(function($routeProvider) {
        $routeProvider.when("/404", {
            templateUrl : "templates/404.html",
        });
    });
    app.config(function($routeProvider) {
        $routeProvider.otherwise({
            redirectTo: "/404",
        });
    });
    app.config(function($locationProvider) {
        $locationProvider.html5Mode(false);
    });
    
})();