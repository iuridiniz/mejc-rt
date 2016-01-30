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
                reset: '&?onReset',
                submit: '&onSubmit',
                submit_text: "@submitText",
                patient_types: "=patientTypes",
                blood_types: "=bloodTypes",
                disable: "=disable" /* TODO: today code only disables code input */
            },
            replace: false,
            templateUrl: "templates/patient/form.html"
        };
    });
    app.directive("transfusionForm", function($parse) {
        var combining = /[\u0300-\u036F]/g;
        var translit = function(s) {
            if (typeof String.prototype.normalize === "function") { /* ECMA6 feature */
                return s.normalize('NFKD').replace(combining, '');
            }
            return s;
        };
        return {
            restrict: 'E',
            scope: {
                transfusion: "=transfusion",
                reset: '&?onReset',
                query: '=query',
                submit: '&onSubmit',
                submit_text: "@submitText",
                blood_types: "=bloodTypes",
                blood_contents: "=bloodContents",
                locals: "=locals",
                disable: "=disable",
                onReady: "&onReady",
            },
            link: function($scope, $elem, attrs){
                $scope.translit = translit;
                $scope.onReady({form:$scope.form});
                $scope.addBag = function() {
                    if (! $scope.transfusion.bags) {
                        $scope.transfusion.bags = [];
                    }
                    /* insert a copy of last bag */
                    var bag = {};
                    if (typeof Object.assign === 'function') { /* ECMA6 feature */
                        if ($scope.transfusion.bags.length) {
                            var last_bag = $scope.transfusion.bags[$scope.transfusion.bags.length - 1];
                            Object.assign(bag, last_bag)
                        }
                    }
                    $scope.transfusion.bags.push(bag);
                };
                $scope.removeBag = function($index) {
                    $scope.transfusion.bags.splice($index, 1);
                };
            },
            replace: false,
            templateUrl: "templates/transfusion/form.html"
        };
    });
})();