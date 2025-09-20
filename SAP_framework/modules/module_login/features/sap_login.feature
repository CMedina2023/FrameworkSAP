Feature: Login a SAP
  Como usuario autorizado
  Quiero poder iniciar sesión en SAP
  Para realizar mis operaciones diarias

  Scenario: Login exitoso a SAP
    Given que tengo las credenciales válidas
    When inicio sesión en SAP
    Then debo tener acceso al sistema
