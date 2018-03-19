$(document).ready(function () {
    

    $("a.editar").on('click', function(event){
        event.preventDefault();

        var id_interv = $(this).attr("id");
        var $selector = $("#deformField2").select2();        

        $.getJSON(
            '/interv_edit',
            {'id_interv': id_interv},
            function(datajson) {
                // Asignamos el id de la intervencion al campo 'id' oculto del
                // formulario
                $('#deform').find('input[name="id"]').val(datajson.id);
                // Rellenamos la caja del selector con las etiquetas
                $selector.val(datajson.etiquetas).trigger("change");
            }
        );

        $("form").appendTo(".form." + id_interv);
                
        return false;
    });

    $('button[name="submit"]').on('click', function(event){
        event.preventDefault();

        var datos = $("#deformField2").select2('data');
        var num_etiquetas = [];
        for (var d = 0; d < datos.length; d++) {
            var id = datos[d].id;
            if ($.inArray(id, num_etiquetas) === -1) {
                num_etiquetas.push(Number(id));
            }
        }

        var id_interv = $('input[name="id"]').attr("value");

        $.ajax({
            type: 'POST',
            url: '/interv_process',
            data: {id_interv: id_interv, etiquetas: num_etiquetas},
            traditional: true,
            success: function(datajson) {
                var botones_sin_prov = "";
                var botones_prov = "";
                var num_etiq_sin_prov = datajson['lista_etiq_sin_prov'].length;
                var num_etiq_prov = datajson['lista_etiq_prov'].length;

                var etiq_sin_prov = datajson['lista_etiq_sin_prov']
                var etiq_prov = datajson['lista_etiq_prov']

                for (var i = 0; i < num_etiq_sin_prov; i++) {
                    botones_sin_prov += '<button type="button" class="btn btn-info btn-xs">'
                        + etiq_sin_prov[i] + '</button>';
                }
                for (var i = 0; i < num_etiq_prov; i++) {
                    botones_prov += '<button type="button" class="btn btn-warning btn-xs">'
                        + etiq_prov[i] + '</button>';
                }
                var botones = botones_sin_prov + botones_prov;
                $("span#" +id_interv).html(botones);

                $(".etiquetas button").after(" ");
            }

        });
    });
});
