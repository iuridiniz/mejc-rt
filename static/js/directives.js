/*******************************************************************/
/* DIRECTIVES */
/*******************************************************************/
(function() {
    app.directive("loading", function() {
        return {
            restrict: 'E',
            replace: true,
            template:  '<div>' + 
                           '<i class="fa fa-refresh fa-spin fa-5x loading-icon"></i>' +
                       '</div>'
        };
    });
    
    app.directive("patientModal", function() {
        return {
            restrict: 'E',
            scope: {
                patients: '=patients',
                click: '&onClick'
            },
            replace: false,
            templateUrl: "tmpl/patient_modal.html"
        };
    });

    app.directive("loginPage", function() {
        return {
            restrict: 'E',
            scope: {},
            replace: false,
            templateUrl: "templates/login.html"
        };
    });
    
    app.directive("mainPage", function() {
        return {
            restrict: 'E',
            scope: {},
            replace: true,
            templateUrl: "templates/main.html"
        };
    });
    app.directive("mainHeader", function() {
        return {
            restrict: 'E',
            replace: true,
            templateUrl: "templates/main_header.html"
        };
    });
    app.directive("mainLeftSideColumn", function() {
        return {
            restrict: 'E',
            replace: true,
            templateUrl: "templates/main_left_side_column.html"
        };
    });
    app.directive("mainFooter", function() {
        return {
            restrict: 'E',
            replace: true,
            templateUrl: "templates/main_footer.html"
        };
    });
    app.directive("messageBox", function() {
        return {
            restrict: 'E',
            replace: true,
            templateUrl: "templates/message_box.html"
        }
    });
    app.directive("patientForm", function() {
        return {
            restrict: 'E',
            scope: {
                patient: '=patient',
                reset: '&onReset',
                submit: '&onSubmit',
                patient_types: "=patientTypes",
                blood_types: "=bloodTypes"
            },
            replace: false,
            templateUrl: "templates/patient/form.html"
        };
    });
})();