from pyramid.response import Response
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

from ..models import Intervencion, Etiqueta

from pyramid.renderers import get_renderer
from pyramid.interfaces import IBeforeRender
from pyramid.events import subscriber

import transaction
from sqlalchemy import func

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

            build_cadena = lambda s: '' if s is None else str(s)

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
            # 'intervenciones_sin_etiquetas': intervenciones(None),
            'css_resources': css_resources,
            'js_resources': js_resources,
            'form': form.render(),
            'section': 'intervenciones'}

    @view_config(name='interv.edit', renderer='json')
    def editar_etiquetas(self):

        id_intervencion = self.request.params.get('id_interv')

        intervencion = self.request.dbsession.query(Intervencion).filter(
            Intervencion.id == id_intervencion).first()

        def appstruct(self):
            """ Returns the appstruct model for use with deform. """
            appstruct = {}
            for k in sorted(self.__dict__):
                if k[:4] == "_sa_":
                    continue
                appstruct[k] = self.__dict__[k]
            # Special case for the etiquetas
            appstruct['etiquetas'] = set(
                [c.id for c in self.etiquetas])
            return appstruct

        appstruct = appstruct(intervencion)

        return {
            'id': intervencion.id,
            'etiquetas': list(appstruct['etiquetas']),
        }

    @view_config(name='process_form', renderer='json')
    def process_form(self, form):

        controls = self.request.POST.items()
        for c in controls:
            print('=========================> ', c)
        try:
            captured = form.validate(controls)
            with transaction.manager:
                lista_etiquetas = captured.get('etiquetas', [])
                etiquetas = []
                for etiq in lista_etiquetas:
                    etiquetas.append(
                        self.request.dbsession.query(
                            Etiqueta).filter_by(id=etiq).one())

                intervencion_id = captured.get('id')
                if intervencion_id is not None:
                    q_intervencion = self.request.dbsession.query(
                        Intervencion).filter(
                            Intervencion.id == intervencion_id)

                intervencion = q_intervencion.one()
                intervencion.etiquetas = etiquetas

                self.request.dbsession.merge(intervencion)

            url = self.request.route_url('intervenciones')
            return HTTPFound(url)

        except ValidationFailure as e:
            return {
                'form': e.render(),
                'form_label': 'Errores'
            }


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


