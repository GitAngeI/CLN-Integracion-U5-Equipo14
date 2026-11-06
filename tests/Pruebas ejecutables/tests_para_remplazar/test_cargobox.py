from unittest.mock import Mock
import pytest

from src.domain import (
    EvidenciaObligatoriaException,
    InvalidStateTransitionError,
    Paquete,
    TercerIntentoNoAutorizadoException,
)
from src.repository import PaqueteRow, SessionLocal, make_engine
from src.application import EnvioService, NotificationGateway

# ==========================================
# REGLA BR012: Evidencia obligatoria (CP-01 a CP-03)
# ==========================================
def test_br012_exito_entrega_con_evidencia():
    """CP-01: Repartidor adjunta firma y foto digital -> Estado Entregado."""
    p = Paquete(id_paquete=1, peso=5.0, alto=10, ancho=10, largo=10, estado="EN_TRANSITO")
    p.entregar(firma="FirmaJuan", foto="foto.jpg")
    assert p.estado == "Entregado"
    assert p.evidencia_adjunta is True

def test_br012_error_falta_evidencia():
    """CP-02: Intenta finalizar sin evidencia -> EvidenciaObligatoriaException."""
    p = Paquete(id_paquete=2, peso=5.0, alto=10, ancho=10, largo=10, estado="EN_TRANSITO")
    with pytest.raises(EvidenciaObligatoriaException):
        p.entregar(firma="", foto="")

def test_br012_limite_paquete_cancelado():
    """CP-03: Intenta entregar un paquete cancelado -> InvalidStateTransitionError."""
    p = Paquete(id_paquete=3, peso=5.0, alto=10, ancho=10, largo=10, estado="CANCELADO")
    with pytest.raises(InvalidStateTransitionError):
        p.entregar(firma="Firma", foto="foto.jpg")

# ==========================================
# REGLA BR014: Límite de intentos (CP-04 a CP-06)
# ==========================================
def test_br014_exito_primer_intento_ausente():
    """CP-04: 1ra visita ausente -> Estado Segundo intento pendiente."""
    p = Paquete(id_paquete=4, peso=2.0, alto=5, ancho=5, largo=5, intentos_visita=0)
    p.registrar_visita_ausente()
    assert p.estado == "Segundo intento pendiente"
    assert p.intentos_visita == 1

def test_br014_error_tercer_intento_sin_autorizacion():
    """CP-05: 3ra visita sin autorizar -> TercerIntentoNoAutorizadoException."""
    p = Paquete(id_paquete=5, peso=2.0, alto=5, ancho=5, largo=5, intentos_visita=2)
    with pytest.raises(TercerIntentoNoAutorizadoException):
        p.registrar_visita_ausente(autorizacion_supervisor=False)

def test_br014_limite_tercer_intento_con_supervisor():
    """CP-06: 3ra visita ausente con autorización -> Retenido en sucursal."""
    p = Paquete(id_paquete=6, peso=2.0, alto=5, ancho=5, largo=5, intentos_visita=2)
    p.registrar_visita_ausente(autorizacion_supervisor=True)
    assert p.estado == "Retenido en sucursal"

# ==========================================
# REGLA BR005: Cálculo de tarifa (CP-07 a CP-09)
# ==========================================
def test_br005_exito_calculo_estandar():
    """CP-07: Paquete 5kg, 30x30x30, Estándar -> Tarifa correcta ($150)."""
    p = Paquete(id_paquete=7, peso=5.0, alto=30, ancho=30, largo=30)
    tarifa = p.calcular_tarifa(servicio="Estandar")
    assert tarifa == 150.0

def test_br005_error_peso_negativo():
    """CP-08: Peso negativo -> ValueError por Value Object inválido."""
    with pytest.raises(ValueError):
        Paquete(id_paquete=8, peso=-5.0, alto=30, ancho=30, largo=30)

def test_br005_limite_sobrepeso_exacto():
    """CP-09: Paquete exactamente en 25kg -> Aplica tarifa máxima sin error."""
    p = Paquete(id_paquete=9, peso=25.00, alto=30, ancho=30, largo=30)
    tarifa = p.calcular_tarifa(servicio="Estandar")
    assert tarifa == 350.0

# ==========================================
# PRUEBAS ADICIONALES: Persistencia y Mocks
# ==========================================
def test_persistencia_bd_en_memoria():
    """Prueba de persistencia usando SQLAlchemy y SQLite en memoria."""
    engine = make_engine()
    session = SessionLocal(engine)
    
    row = PaqueteRow(id=99, peso=10.0, estado="EN_TRANSITO", intentos=0)
    session.add(row)
    session.commit()
    
    recuperado = session.query(PaqueteRow).filter_by(id=99).first()
    assert recuperado is not None
    assert recuperado.peso == 10.0
    session.close()

def test_mock_servicio_externo_notificacion():
    """Prueba con Mock para simular pasarela/servicio de notificación externo."""
    gateway_mock = Mock(spec=NotificationGateway)
    gateway_mock.enviar_alerta_intento.return_value = True
    
    servicio = EnvioService(gateway=gateway_mock)
    paquete = Paquete(id_paquete=100, peso=3.0, alto=10, ancho=10, largo=10)
    
    estado = servicio.procesar_fallo_entrega(paquete, supervisor_auth=False)
    
    assert estado == "Segundo intento pendiente"
    gateway_mock.enviar_alerta_intento.assert_called_once_with(100, "Intento fallido #1")