def includeme(config):
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_static_view('deform_static', 'deform:static/')

    config.add_route('home', '/')
    config.add_route('intervenciones', '/intervenciones')
    config.add_route('etiquetas', '/etiquetas')

