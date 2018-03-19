from pyramid.response import Response
from pyramid.view import view_config

from ..models import Intervencion, Etiqueta

from pyramid.renderers import get_renderer
from pyramid.interfaces import IBeforeRender
from pyramid.events import subscriber

import transaction
from sqlalchemy import func, extract, and_, or_

from .schema import IntervencionSchema
from deform import Form
from deform import Button
from deform import ValidationFailure


@subscriber(IBeforeRender)
def globals_factory(event):
    master = get_renderer('../templates/master.pt').implementation()
    event['master'] = master


provincias = ['Almería', 'Cádiz', 'Córdoba', 'Granada', 'Huelva', 'Jaén',
              'Málaga', 'Sevilla']

link = "http://www.parlamentodeandalucia.es/" +\
       "webdinamica/portal-web-parlamento/pdf.do?tipodoc=diario&id="


class DefaultViews(object):

    def __init__(self, request):
        self.request = request

    @property
    def lista_etiquetas(self):
        lista = self.request.dbsession.query(Etiqueta).all()
        options = ()
        for etiqueta in lista:
            options += ((etiqueta.id, etiqueta.nombre),)
        return options

    @property
    def form_intervencion(self, formid="deform"):
        """
        This helper code generates the form that will be used to add
        and edit the tags based on the schema of the form.
        """
        schema = IntervencionSchema().bind(
            lista_etiquetas=self.lista_etiquetas,
            default=None)

        return Form(
            schema,
            buttons=[Button('submit', title='Enviar')],
            formid=formid,
            use_ajax=True,
        )

    @property
    def form_resources(self):
        """ Obtine una lista de recursos css y javascript para un formulario
            dado. Después se usan para situar estos recursos en la template
        """
        resources = self.form_intervencion.get_widget_resources()
        js_resources = resources['js']
        css_resources = resources['css']
        js_links = [r for r in js_resources]
        css_links = [r for r in css_resources]
        return (css_links, js_links)

    @view_config(renderer='../templates/principal.pt')
    def selector_view(self):
        form = self.generate_form_selector()
        css_resources, js_resources = self.form_resources(form)

        capturado = None

        if 'submit' in self.request.POST:
            controles = self.request.POST.items()

            try:
                capturado = form.validate(controles)
            except ValidationFailure as e:
                return {
                    'css_resources': css_resources,
                    'js_resources':  js_resources,
                    'form': e.render(),
                    'form_label': 'Errores'
                }

            tipo = capturado.get('tipo')
            anualidad = list(capturado.get('anualidad'))
            etiquetas_consejeria = list(capturado.get('consejeria'))
            etiquetas_provincia = list(capturado.get('provincia'))
            etiquetas = list(capturado.get('etiquetas'))
            selec_etiquetas = self.etiquetas_filtradas(list(etiquetas))

            selector = []
            for num in range(len(etiquetas)):
                selec = Intervencion.etiquetas.any(id=etiquetas[num])
                selector.append(selec)

            def condicion(tipo):
                if tipo == 'union':
                    condicion = (or_(*selector))
                else:
                    condicion = (and_(*selector))
                return condicion

            criterio_etiquetas = [condicion(tipo)]
            criterio_fechas = [
                extract('year', Intervencion.fecha).in_(anualidad),
                condicion(tipo)]
            criterio_provincias = [
                Intervencion.etiquetas.any(
                    Etiqueta.id.in_(etiquetas_provincia)),
                condicion(tipo)]
            criterio_consejerias = [
                Intervencion.consejeria.in_(etiquetas_consejeria),
                condicion(tipo)]
            criterio_total = [
                extract('year', Intervencion.fecha).in_(anualidad),
                Intervencion.etiquetas.any(Etiqueta.id.in_(
                    etiquetas_provincia)),
                Intervencion.consejeria.in_(etiquetas_consejeria),
                condicion(tipo)]

            if anualidad == []:
                if etiquetas_provincia == []:
                    if etiquetas_consejeria == []:
                        intervenciones = self.request.dbsession.query(
                            Intervencion).filter(*criterio_etiquetas)
                    else:
                        intervenciones = self.request.dbsession.query(
                            Intervencion).filter(*criterio_consejerias)
                else:
                    intervenciones = self.request.dbsession.query(
                        Intervencion).filter(and_(*criterio_provincias))
            else:
                if etiquetas_provincia == []:
                    intervenciones = self.request.dbsession.query(
                        Intervencion).filter(and_(*criterio_fechas)).all()
                else:
                    intervenciones = self.request.dbsession.query(
                        Intervencion).filter(and_(*criterio_total))

            return {
                'seleccion': selec_etiquetas,
                'intervenciones': ([dict(
                    id=interv.id,
                    fecha=interv.fecha.strftime('%d/%m/%Y'),
                    nombre=interv.nombre,
                    lista_total_etiquetas=[
                        etiq.nombre for etiq in interv.etiquetas],
                    lista_etiquetas=set([
                        etiq.nombre for etiq in interv.etiquetas]
                    )-set(provincias),
                    lista_provincias=set([
                        etiq.nombre for etiq in interv.etiquetas]
                    ).intersection(provincias),

                    enlace="%s%s#page=%s" % (
                        self.link, interv.referencia, interv.pagina)
                    ) for interv in intervenciones]),
                'css_resources': css_resources,
                'js_resources': js_resources,
                'form_label': 'Etiquetas de selección',
                'form': form.render()
            }

        return {
            'css_resources': css_resources,
            'js_resources': js_resources,
            'form_label': 'Etiquetas de selección',
            'form': form.render(),
            'seleccion': None,
            'intervenciones': None
        }

    @view_config(route_name='intervenciones',
                 renderer='parlaweb:templates/intervenciones.pt')
    def intervenciones_view(self):
        """Presenta la lista de intervenciones junto con las etiquetas
        """
        def intervenciones(con_etiquetas):
            """
            devuelve un diccionario con los datos de las intervenciones
            incluyendo una lista de etiquetas y provincias
            """
            if con_etiquetas is None:
                categoria = [Intervencion.etiquetas == None]
            else:
                categoria = []

            query = self.request.dbsession.query(
                Intervencion,
                func.string_agg(Etiqueta.nombre, ';')).outerjoin(
                    Intervencion.etiquetas
                ).filter(
                    *categoria
                ).group_by(Intervencion.id).order_by(
                    Intervencion.fecha.desc()).all()

            # build_cadena = lambda s: '' if s is None else str(s)
            def build_cadena(cadena):
                if cadena is None:
                    return ''
                else:
                    return str(cadena)

            intervenciones = [dict(
                id=intervencion.id,
                fecha=intervencion.fecha.strftime('%d/%m/%Y'),
                nombre=intervencion.nombre,
                lista_etiquetas=set(
                    build_cadena(etiquetas).split(";"))-set(provincias),
                lista_provincias=set(
                    build_cadena(etiquetas).split(";")).intersection(
                        set(provincias)),
                enlace="%s%s#page=%s" % (link, intervencion.referencia,
                                         intervencion.pagina),
            ) for intervencion, etiquetas in query]

            return intervenciones

        form = self.form_intervencion

        if 'submit' in self.request.POST:
            self.process_form(form)

        css_resources, js_resources = form_resources(form)

        return {
            'intervenciones': intervenciones('todas'),
            'css_resources': css_resources,
            'js_resources': js_resources,
            'form': form.render(),
            'section': 'intervenciones'}

    @view_config(name='interv_edit', renderer='json')
    def editar_etiquetas(self):

        id_intervencion = self.request.params.get('id_interv')

        intervencion = self.request.dbsession.query(Intervencion).filter(
            Intervencion.id == id_intervencion).first()

        def appstruct(modelo):
            """ Returns the appstruct model for use with deform. """
            appstruct = {}
            for k in sorted(modelo.__dict__):
                if k[:4] == "_sa_":
                    continue
                appstruct[k] = modelo.__dict__[k]
            # Special case for the etiquetas
            appstruct['etiquetas'] = set(
                [c.id for c in modelo.etiquetas])
            return appstruct

        appstruct = appstruct(intervencion)

        return {
            'id': intervencion.id,
            'etiquetas': list(appstruct['etiquetas']),
        }

    @view_config(name='interv_process', renderer='json')
    def procesar_etiquetas(self):

        # la intervencion que vamos a procesar
        id_intervencion = self.request.params.get('id_interv')

        with transaction.manager:
            i_captured = self.request.dbsession.query(Intervencion).filter(
                Intervencion.id == id_intervencion).first()

            # las nuevas etiquetas de la intervencion
            lista_etiquetas = self.request.params.getall('etiquetas')

            etiquetas = []
            for id in lista_etiquetas:
                etiquetas.append(Etiqueta(id=id))

            intervencion = Intervencion(
                etiquetas=etiquetas,
                nombre=i_captured.nombre,
                fecha=i_captured.fecha,
                pagina=i_captured.pagina,
                referencia=i_captured.referencia,
                comision_pleno=i_captured.comision_pleno,
                nombre_comision=i_captured.nombre_comision,
                sesion=i_captured.sesion,
                tipo=i_captured.tipo,
                interviniente=i_captured.interviniente,
                consejeria_id=i_captured.consejeria_id,
            )

            if intervencion.comision_pleno == "P":
                intervencion.nombre_comision = ""
            elif intervencion.comision_pleno == "C":
                intervencion.interviniente = ""

            if id_intervencion is not None:
                intervencion.id = id_intervencion

            self.request.dbsession.merge(intervencion)

        etiquetas = []
        for etiq in lista_etiquetas:
            query = self.request.dbsession.query(
                Etiqueta.nombre).filter(Etiqueta.id == etiq).one()
            etiquetas.append(query.nombre)
        lista_etiq_sin_prov = set(etiquetas)-set(provincias)
        lista_etiq_prov = set(etiquetas).intersection(set(provincias))
        return {'lista_etiq_sin_prov': list(lista_etiq_sin_prov),
                'lista_etiq_prov': list(lista_etiq_prov)}


def form_resources(form):
    """ Obtine una lista de recursos css y javascript para un formulario
        dado. Después se usan para situar estos recursos en la template
    """
    resources = form.get_widget_resources()
    js_resources = resources['js']
    css_resources = resources['css']
    js_links = [r for r in js_resources]
    css_links = [r for r in css_resources]
    return (css_links, js_links)


def generate_form_intervencion(request, formid="deform"):
    """
    This helper code generates the form that will be used to add
    and edit the tags based on the schema of the form.
    """

    def lista_etiquetas(request):
        lista = request.dbsession.query(Etiqueta).all()
        options = ()
        for etiqueta in lista:
            options += ((etiqueta.id, etiqueta.nombre),)
        return options

    schema = IntervencionSchema().bind(
        lista_etiquetas=lista_etiquetas(request),
        default=None)

    return Form(
        schema,
        buttons=[Button('submit', title='Enviar')],
        formid=formid,
        use_ajax=True,
    )


@view_config(name='form')
def form(request, id_intervencion=1786):
    form = generate_form_intervencion(request)
    # form = form_editar_etiquetas(request, id_intervencion)
    html = form.render()
    return Response(html)


@view_config(route_name='home', renderer='../templates/principal.pt')
def selector_view(request):
    return {
        'section': 'home',
        'project': 'parlaweb'}


@view_config(route_name='etiquetas', renderer='../templates/etiquetas.pt')
def etiquetas_view(request):
    return {
        'section': 'etiquetas',
        'project': 'parlaweb'}
