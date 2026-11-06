from src.domain import Paquete

class NotificationGateway:
    def enviar_alerta_intento(self, id_paquete: int, mensaje: str) -> bool:
        pass

class EnvioService:
    def __init__(self, gateway: NotificationGateway):
        self.gateway = gateway

    def procesar_fallo_entrega(self, paquete: Paquete, supervisor_auth: bool = False):
        paquete.registrar_visita_ausente(autorizacion_supervisor=supervisor_auth)
        self.gateway.enviar_alerta_intento(paquete.id_paquete, f"Intento fallido #{paquete.intentos_visita}")
        return paquete.estado