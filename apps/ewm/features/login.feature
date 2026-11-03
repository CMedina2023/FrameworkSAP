# language: es
Característica: Autenticación y Conexión SAP GUI
  Como tester de SAP EWM
  Quiero validar que la sesión SAP esté activa
  Para asegurar la disponibilidad del sistema antes de ejecutar flujos logísticos

  @PC-531 @bdd @smoke @login @ICD_101
  Escenario: Validar sesión SAP activa y disponible
    Dado que la sesión SAP está abierta y lista para operar
    Entonces el sistema debe responder mostrando la pantalla principal de SAP
