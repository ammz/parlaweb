from pyramid.view import view_config

from ..models import Legislatura, Consejeria, Intervencion, Etiqueta

from pyramid.renderers import get_renderer
from pyramid.interfaces import IBeforeRender
from pyramid.events import subscriber

from sqlalchemy import func


@subscriber(IBeforeRender)
def globals_factory(event):
    master = get_renderer('../templates/master.pt').implementation()
    event['master'] = master


provincias = ['Almería', 'Cádiz', 'Córdoba', 'Granada', 'Huelva', 'Jaén',
              'Málaga', 'Sevilla']

link = "http://www.parlamentodeandalucia.es/" +\
       "webdinamica/portal-web-parlamento/pdf.do?tipodoc=diario&id="


@view_config(route_name='home', renderer='../templates/principal.pt')
def selector_view(request):
    return {
        'section': 'home',
        'project': 'parlaweb'}


@view_config(route_name='intervenciones', renderer='../templates/intervenciones.pt')
def intervenciones_view(request):
    """Presenta la lista de intervenciones.
    """
    datos_intervenciones = request.dbsession.query(
        Intervencion,
        func.string_agg(Etiqueta.nombre,';')
        ).outerjoin(
            Intervencion.etiquetas
        ).order_by(Intervencion.id.desc()).group_by(Intervencion.id).all()

    build_cadena = lambda s: '' if s is None else str(s)

    intervenciones_todas = [dict(
        id=intervencion.id,
        fecha=intervencion.fecha.strftime('%d/%m/%Y'),
        nombre=intervencion.nombre,
        lista_etiquetas=set(build_cadena(etiquetas).split(";"))-set(provincias),
        lista_provincias=set(build_cadena(etiquetas).split(";")).intersection(set(provincias)),
        enlace="%s%s#page=%s" % (link, intervencion.referencia, intervencion.pagina),
    ) for intervencion, etiquetas in datos_intervenciones]

    return {
        'intervenciones': intervenciones_todas,
        'section': 'intervenciones',
    }


@view_config(route_name='etiquetas', renderer='../templates/etiquetas.pt')
def etiquetas_view(request):
    return {
        'section': 'etiquetas',
        'project': 'parlaweb'}


