from colander import Schema
from colander import SchemaNode
from colander import Integer
from colander import deferred
from colander import Set
from colander import drop

from deform.widget import HiddenWidget
from deform.widget import Select2Widget


@deferred
def deferred_etiquetas_widget(node, kw):
    lista_etiquetas = kw.get('lista_etiquetas', [])
    return Select2Widget(values=lista_etiquetas, multiple=True)


class IntervencionSchema(Schema):
    """Este es el esquema del formulario para editar las intervenciones
    """
    id = SchemaNode(
        Integer(),
        missing=drop,
        widget=HiddenWidget(),
    )
    etiquetas = SchemaNode(
        Set(),
        widget=deferred_etiquetas_widget,
    )
