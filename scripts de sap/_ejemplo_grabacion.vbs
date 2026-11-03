' Ejemplo de grabación de SAP Logon (Script Recording and Playback).
' La extensión de estas grabaciones es .vbs.
' Los textos {{TU}} y {{cita}} se sustituyen por datos del framework.
' Los archivos que empiezan con _ no se transforman al ejecutar el lote;
' pasa la ruta explícita si quieres generar este ejemplo.
If Not IsObject(application) Then
   Set SapGuiAuto  = GetObject("SAPGUI")
   Set application = SapGuiAuto.GetScriptingEngine
End If
If Not IsObject(connection) Then
   Set connection = application.Children(0)
End If
If Not IsObject(session) Then
   Set session    = connection.Children(0)
End If
If IsObject(WScript) Then
   WScript.ConnectObject session,     "on"
   WScript.ConnectObject application, "on"
End If
session.findById("wnd[0]").maximize
session.findById("wnd[0]/tbar[0]/okcd").text = "/n/scwm/tu"
session.findById("wnd[0]").sendVKey 0
session.findById("wnd[0]/usr/ctxt/SCWM/S_TU_SR_NO-LOW").text = "{{TU}}"
session.findById("wnd[0]/usr/ctxt/SCWM/S_CITA-LOW").text = "{{cita}}"
session.findById("wnd[0]/usr/ctxt/SCWM/S_TU_SR_NO-LOW").setFocus
session.findById("wnd[0]/usr/ctxt/SCWM/S_TU_SR_NO-LOW").caretPosition = 5
session.findById("wnd[0]/usr/chkP_CHECK").selected = true
session.findById("wnd[0]/tbar[1]/btn[8]").press
