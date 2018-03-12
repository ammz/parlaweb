from sqlalchemy import (
    Column,
    Integer,
    Text,
    ForeignKey,
    Table,
    String,
    Date,
)
from sqlalchemy.orm import relationship
from .meta import Base


etiquetas_intervenciones = Table(
    'etiquetas_intervenciones', Base.metadata,
    Column('etiquetas_id', ForeignKey('etiquetas.id'), primary_key=True),
    Column('intervenciones_id',
           ForeignKey('intervenciones.id'),
           primary_key=True),
)


class Legislatura(Base):
    __tablename__ = 'legislaturas'
    cod = Column(Integer, primary_key=True)
    periodo = Column(Text)


class Consejeria(Base):
    __tablename__ = 'consejerias'
    id = Column(Integer, primary_key=True)
    nombre = Column(Text)

    legislatura_id = Column(ForeignKey('legislaturas.cod'), nullable=False)
    legislatura = relationship('Legislatura', backref='consejerias_de_legislatura')


class Intervencion(Base):
    __tablename__ = 'intervenciones'
    id = Column(Integer, primary_key=True)
    nombre = Column(Text, nullable=False)
    fecha = Column(Date)
    pagina = Column(Integer)
    referencia = Column(Integer)
    comision_pleno = Column(Text)
    nombre_comision = Column(Text)
    sesion = Column(Integer)
    tipo = Column(Text)
    interviniente = Column(Text)

    consejeria_id = Column(Integer, ForeignKey('consejerias.id'), nullable=True)
    consejeria = relationship('Consejeria', backref='intervenciones_de_consejeria')

    etiquetas = relationship(
        'Etiqueta',
        secondary=etiquetas_intervenciones,
        back_populates='intervenciones',
    )


class Etiqueta(Base):
    __tablename__ = 'etiquetas'
    id = Column(Integer, primary_key=True)
    nombre = Column(String(60), nullable=False, unique=True)

    intervenciones = relationship(
        'Intervencion',
        secondary=etiquetas_intervenciones,
        back_populates='etiquetas',
    )
