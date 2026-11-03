# language: es
Característica: Proceso de Arribo de Unidades de Transporte
  Como operador de patio en SAP EWM
  Quiero registrar el arribo de una unidad con su cita
  Para habilitar el ingreso al almacén y descarga

  @PC-534 @bdd @smoke @arribo @ICD_102
  Esquema del escenario: Registro de arribo de TU con cita
    Dado que la sesión SAP está abierta y lista para operar
    Cuando ejecuto el arribo para la TU "<tu>" con la cita "<cita>"
    Entonces el arribo debe quedar registrado exitosamente para la TU "<tu>"

    Ejemplos:
      | tu    | cita          |
      | TU123 | MES0000009660 |
