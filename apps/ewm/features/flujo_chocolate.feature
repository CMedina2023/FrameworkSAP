# language: es
Característica: Flujo E2E de Recibo Chocolate en SAP EWM
  Como supervisor de logística
  Quiero ejecutar el flujo continuo de recibo
  Para registrar el arribo, asignar cortina y procesar las unidades de manipulación

  @PC-535 @bdd @regression @chocolate @ICD_104
  Escenario: Ejecución de flujo completo Recibo Chocolate
    Dado que la sesión SAP está abierta y lista para operar
    Cuando registro el arribo para la TU "TU123" y cita "MES0000009660"
    Y asigno la cortina para la unidad de transporte "TU123"
    Y proceso el recibo de las HUs "Q76890456"
    Entonces el flujo completo de recibo chocolate debe finalizar sin errores
