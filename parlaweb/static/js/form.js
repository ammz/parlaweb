$(document).ready(function () {
    

    $("a.editar").on('click', function(event){
        event.preventDefault();

        var id_interv = $(this).attr("id");
        var $selector = $("#deformField2").select2();        

        $.getJSON(
            '/interv.edit',
            {'id_interv': id_interv},
            function(datajson) {
                $('#deform').find('input[name="id"]').val(datajson.id);
                $selector.val(datajson.etiquetas).trigger("change");
            }
        );

        $("form").appendTo(".form." + id_interv);
                
        return false;
    });

    $('button[name="submit"]').on('click', function(event){
        event.preventDefault();

        var datos = $("#deformField2").select2('data');
        var val = [];
        for (var d = 0; d < datos.length; d++) {
            var id = datos[d].id;
            if ($.inArray(id, val) === -1) {
                val.push(id);
            }
        }

        var id_interv = $('input[name="id"]').attr("value");
        var $id = $('#' + id_interv);
        console.log($id);
    });
});

