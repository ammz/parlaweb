from pyramid.view import view_config

from ..models import Legislatura, Consejeria, Intervencion, Etiqueta

from pyramid.renderers import get_renderer
from pyramid.interfaces import IBeforeRender
from pyramid.events import subscriber


@subscriber(IBeforeRender)
def globals_factory(event):
    master = get_renderer('../templates/master.pt').implementation()
    event['master'] = master


@view_config(route_name='home', renderer='../templates/principal.pt')
def selector_view(request):
    return {
        'section': 'home',
        'project': 'parlaweb'}


@view_config(route_name='intervenciones', renderer='../templates/intervenciones.pt')
def intervenciones_view(request):
    return {
        'section': 'intervenciones',
        'project': 'parlaweb'}


@view_config(route_name='etiquetas', renderer='../templates/etiquetas.pt')
def etiquetas_view(request):
    return {
        'section': 'etiquetas',
        'project': 'parlaweb'}


