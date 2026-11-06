class EvidenciaObligatoriaException(Exception):
    pass

class InvalidStateTransitionError(Exception):
    pass

class TercerIntentoNoAutorizadoException(Exception):
    pass

class Paquete:
    def __init__(self, id_paquete: int, peso: float, alto: float, ancho: float, largo: float, estado: str = "EN_TRANSITO", intentos_visita: int = 0):
        if peso < 0 or alto <= 0 or ancho <= 0 or largo <= 0:
            raise ValueError("Peso negativo o dimensiones inválidas (Value Object inválido)")
        self.id_paquete = id_paquete
        self.peso = peso
        self.dimensiones = (alto, ancho, largo)
        self.estado = estado
        self.intentos_visita = intentos_visita
        self.evidencia_adjunta = False
        self.autorizacion_supervisor = False

    # --- BR012: Evidencia obligatoria ---
    def entregar(self, firma: str, foto: str):
        if self.estado == "CANCELADO":
            raise InvalidStateTransitionError("No se puede entregar un paquete cancelado")
        if not firma or not foto:
            raise EvidenciaObligatoriaException("Falta firma o foto digital obligatoria")
        self.evidencia_adjunta = True
        self.estado = "Entregado"

    # --- BR014: Límite de intentos de entrega ---
    def registrar_visita_ausente(self, autorizacion_supervisor: bool = False):
        self.intentos_visita += 1
        self.autorizacion_supervisor = autorizacion_supervisor

        if self.intentos_visita == 1:
            self.estado = "Segundo intento pendiente"
        elif self.intentos_visita >= 3:
            if self.autorizacion_supervisor:
                self.estado = "Retenido en sucursal"
            else:
                raise TercerIntentoNoAutorizadoException("Tercer intento sin autorización previa")

    # --- BR005: Cálculo estricto de tarifa ---
    def calcular_tarifa(self, servicio: str = "Estandar") -> float:
        # Límite de sobrepeso exacto (ej. 25.00 kg)
        if self.peso > 25.00:
            raise ValueError("Peso excede el límite máximo permitido para carga normal")
        
        volumen = self.dimensiones[0] * self.dimensiones[1] * self.dimensiones[2]
        tarifa_base = 100.0 if servicio == "Estandar" else 150.0
        
        # Caso especial para límite exacto de 25kg (CP-09)
        if self.peso == 25.00:
            return tarifa_base + 250.0 # Tarifa máxima sin error
            
        return tarifa_base + (self.peso * 10.0)