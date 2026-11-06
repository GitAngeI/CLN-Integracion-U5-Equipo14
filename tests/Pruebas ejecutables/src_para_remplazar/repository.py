from sqlalchemy import Column, Float, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class PaqueteRow(Base):
    __tablename__ = "paquetes"
    id = Column(Integer, primary_key=True)
    peso = Column(Float)
    estado = Column(String)
    intentos = Column(Integer)

def make_engine():
    return create_engine("sqlite:///:memory:")

def SessionLocal(engine):
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()