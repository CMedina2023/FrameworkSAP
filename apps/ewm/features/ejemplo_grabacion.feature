# language: es
Característica: Automatización de Grabación Ejemplo Grabacion
  Como tester de SAP
  Quiero ejecutar la grabación convertida
  Para reproducir el flujo dentro del framework estandarizado

  @bdd @grabacion @ejemplo_grabacion
  Escenario: Ejecución de grabación ejemplo_grabacion
    Dado que la sesión SAP está abierta y lista para operar
    Cuando ejecuto el módulo de la grabación "ejemplo_grabacion"
    Entonces el módulo debe finalizar con éxito
