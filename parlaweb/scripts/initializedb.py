import os
import sys
import transaction

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from pyramid.scripts.common import parse_vars

from ..models.meta import Base
from ..models import (
    get_engine,
    get_session_factory,
    get_tm_session,
    )
from ..models import Legislatura, Consejeria, Etiqueta, Intervencion


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri> [var=value]\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) < 2:
        usage(argv)
    config_uri = argv[1]
    options = parse_vars(argv[2:])
    setup_logging(config_uri)
    settings = get_appsettings(config_uri, options=options)

    engine = get_engine(settings)
    Base.metadata.create_all(engine)

    session_factory = get_session_factory(engine)

    with transaction.manager:
        dbsession = get_tm_session(session_factory, transaction.manager)

        leg = Legislatura(
            cod=10,
            periodo='2015-...')
        dbsession.add(leg)

        consej = Consejeria(
            nombre='Presidencia',
            legislatura=leg)
        dbsession.add(consej)

        etiq_sev = Etiqueta(
            nombre='Sevilla')
        dbsession.add(etiq_sev)
        
        etiq_cor = Etiqueta(
            nombre='Cordoba')
        dbsession.add(etiq_cor)

        interv = Intervencion(
            nombre='nombre de la intervención',
            fecha='1963-09-01',
            pagina=1,
            referencia=1,
            comision_pleno='C',
            nombre_comision='Comision de presidencia',
            sesion=1,
            tipo='C',
            interviniente='Consejero de Presidencia',
            consejeria=consej,
        )
        dbsession.add(interv)

        interv.etiquetas.append(Etiqueta(nombre='Malaga'))


