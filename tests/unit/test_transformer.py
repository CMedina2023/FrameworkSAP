"""Pruebas unitarias del transformador de grabaciones SAP GUI (sin conexión a SAP)."""
import unittest
import tempfile
from pathlib import Path

from tools.sap_transformer.vbs_parser import parse_vbs
from tools.sap_transformer.service import TransformationService

EXAMPLE_VBS = """
If Not IsObject(application) Then
   Set SapGuiAuto  = GetObject("SAPGUI")
   Set application = SapGuiAuto.GetScriptingEngine
End If
session.findById("wnd[0]").maximize
session.findById("wnd[0]/tbar[0]/okcd").text = "/n/scwm/tu"
session.findById("wnd[0]").sendVKey 0
session.findById("wnd[0]/usr/ctxt/SCWM/S_TU_SR_NO-LOW").text = "{{TU}}"
session.findById("wnd[0]/tbar[1]/btn[8]").press
"""


class TestTransformer(unittest.TestCase):
    def test_parse_vbs_actions(self):
        actions = parse_vbs(EXAMPLE_VBS)
        self.assertTrue(len(actions) >= 4)
        members = [a.member for a in actions if a.member]
        self.assertIn("sendVKey", members)
        self.assertIn("press", members)

    def test_transformation_generates_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vbs_file = root / "flujo_prueba.vbs"
            vbs_file.write_text(EXAMPLE_VBS, encoding="utf-8")

            service = TransformationService(
                project_root=root,
                locators_dir=root / "locators",
                modules_dir=root / "modules",
                features_dir=root / "features",
            )
            result = service.transform_paths([vbs_file], force=True)
            self.assertEqual(len(result.written), 1)
            self.assertTrue((root / "locators" / "flujo_prueba_locators.py").exists())
            self.assertTrue((root / "modules" / "flujo_prueba_module.py").exists())
            self.assertTrue((root / "features" / "flujo_prueba.feature").exists())


if __name__ == "__main__":
    unittest.main()
