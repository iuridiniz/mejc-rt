(function() {
    
    var datatables_ptBR = {
        //"sEmptyTable":     "No data available in table",
        "sEmptyTable":     "Não há dadados",
        //"sInfo":           "Showing _START_ to _END_ of _TOTAL_ entries",
        "sInfo":           "Mostrando _START_ até _END_ de _TOTAL_ registros",
        //"sInfoEmpty":      "Showing 0 to 0 of 0 entries",
        "sInfoEmpty":      "Mostrando 0 to 0 of 0 registros",
        //"sInfoFiltered":   "(filtered from _MAX_ total entries)",
        "sInfoFiltered":   "(filtrado de um total de _MAX_ registros)",
        "sInfoPostFix":    "",
        //"sInfoThousands":  ",",
        "sInfoThousands":  "",
        //"sLengthMenu":     "Show _MENU_ entries",
        "sLengthMenu":     "Mostrar _MENU_ registros",
        //"sLoadingRecords": "Loading...",
        "sLoadingRecords": "Carregando...",
        //"sProcessing":     "Processing...",
        "sProcessing":     "Processando...",
        //"sSearch":         "Search:",
        "sSearch":         "Localizar:",
        //"sZeroRecords":    "No matching records found",
        "sZeroRecords":    "Nenhum registro encontrado",
        "oPaginate": {
            //"sFirst":    "First",
            "sFirst":    "Primeiro",
            //"sLast":     "Last",
            "sLast":     "Último",
            //"sNext":     "Next",
            "sNext":     "Próximo",
            //"sPrevious": "Previous"
            "sPrevious": "Anterior"
        },
        "oAria": {
            //"sSortAscending":  ": activate to sort column ascending",
            "sSortAscending":  ": ative para ordenar a coluna de forma ascendente",
            //"sSortDescending": ": activate to sort column descending"
            "sSortDescending": ": ative para ordenar a coluna de forma descendente"
        }
    }
    
    
    app.controller("PatientListController", ['DTOptionsBuilder', 'DTColumnDefBuilder', '$http',
    function(DTOptionsBuilder, DTColumnDefBuilder, $http) {
        var ctrl = this;
        ctrl.dtOptions = DTOptionsBuilder
            .newOptions()
            .withBootstrap()
            .withLanguage(datatables_ptBR)
            .withOption('ajax', {
                "url": '/api/v1/patient/list?format=datatables.net',
                "contentType": "application/json",
                "type": "POST",
                "data": function ( d ) {
                  return JSON.stringify( d );
                }
            });
        ctrl.dtOptions.withDataProp('data')
            .withOption('processing', true)
            .withOption('serverSide', true)
            .withPaginationType('full_numbers');

//        ctrl.dtColumnDefs = [
//           DTColumnDefBuilder.newColumnDef(0).notVisible().withOption('sName', 'key'),//.withOption('sName', 'key'),
//           DTColumnDefBuilder.newColumnDef(1).withOption('sName', 'name'),
//           DTColumnDefBuilder.newColumnDef(2).withOption('sName', 'code'),
//           DTColumnDefBuilder.newColumnDef(3).withOption('sName', 'blood_type'),
//           DTColumnDefBuilder.newColumnDef(4).notVisible(),//.withOption('sName', 'type'),
//       ];
        
        ctrl.dtColumns = $http.get("/api/v1/patient/list/columns").then(function(response) {
            return response.data
        });
        console.log(ctrl.dtColumns);
        //ctrl.dtColumns = $resource('/api/v1/patient/list/columns').query().$promise;

    }]);
})();

