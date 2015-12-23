(function() {
    app.controller("PatientDeleteController", function($http, $scope, $uibModalInstance, patient) {
        console.log(arguments);
        var modal = this;
        modal.patient = angular.copy(patient);

        modal.confirm = function () {
            modal.loading = true;
            $http['delete']("/api/v1/patient/" + modal.patient.key).then(function (ret) {
                modal.loading = false;
                $uibModalInstance.close({success:true, patient: modal.patient});
            }, function(err) {
                modal.loading = false;
                $uibModalInstance.close({success:false, patient: modal.patient});
            });
        };

        modal.cancel = function () {
            $uibModalInstance.dismiss('cancel');
        };
    });
})();