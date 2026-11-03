"""Orquesta la lectura de grabaciones .vbs y la generación en apps/ewm/."""
from __future__ import annotations

import ast
from pathlib import Path

from tools.sap_transformer.generators import count_actions, render_feature, render_locators, render_module
from tools.sap_transformer.models import BatchResult, RecordingError, TransformResult
from tools.sap_transformer.naming import locators_class_name, module_function_name, recording_key
from tools.sap_transformer.vbs_parser import parse_vbs, read_recording

SCRIPTS_DIRNAME = "scripts de sap"


class TransformationService:
    def __init__(
        self,
        project_root: Path,
        scripts_dir: Path | None = None,
        locators_dir: Path | None = None,
        modules_dir: Path | None = None,
        features_dir: Path | None = None,
        steps_dir: Path | None = None,
    ):
        self.project_root = Path(project_root)
        self.scripts_dir = scripts_dir or (self.project_root / SCRIPTS_DIRNAME)
        self.locators_dir = locators_dir or (self.project_root / "apps" / "ewm" / "locators")
        self.modules_dir = modules_dir or (self.project_root / "apps" / "ewm" / "modules")
        self.features_dir = features_dir or (self.project_root / "apps" / "ewm" / "features")
        self.steps_dir = steps_dir or (self.project_root / "tests" / "bdd" / "step_defs")

    def transform_paths(self, paths: list[Path] | None = None, force: bool = False) -> BatchResult:
        files = self.expand(paths or [])
        if not files:
            raise RecordingError(
                f"No hay grabaciones .vbs. Guarda el script de SAP Logon en '{SCRIPTS_DIRNAME}'."
            )

        written: list[TransformResult] = []
        skipped: list[TransformResult] = []
        errors: list[str] = []
        seen: dict[str, str] = {}

        for path in files:
            try:
                key = recording_key(path.stem)
            except RecordingError as exc:
                errors.append(f"{path.name}: {exc}")
                continue

            if key in seen:
                errors.append(f"{path.name}: genera el mismo nombre '{key}' que {seen[key]}.")
                continue
            seen[key] = path.name

            try:
                res = self._transform_one(path, key, force=force)
            except RecordingError as exc:
                errors.append(str(exc))
                continue

            if res.skipped:
                skipped.append(res)
            else:
                written.append(res)

        return BatchResult(written=written, skipped=skipped, errors=errors)

    def expand(self, paths: list[Path]) -> list[Path]:
        if not paths:
            return self._discover(self.scripts_dir, skip_private=True)

        files: list[Path] = []
        for raw in paths:
            raw_path = Path(raw)
            p = raw_path if raw_path.is_absolute() else self.project_root / raw_path
            if p.is_dir():
                files.extend(self._discover(p, skip_private=True))
            elif p.suffix.lower() == ".vbs":
                files.append(p)
            else:
                raise RecordingError(f"{p.name} no es una grabación .vbs.")
        return sorted(list(set(files)), key=lambda x: x.name.lower())

    def _discover(self, folder: Path, skip_private: bool) -> list[Path]:
        if not folder.exists():
            return []
        found = [p for p in folder.glob("*.vbs") if p.is_file()]
        if skip_private:
            found = [p for p in found if not p.name.startswith("_")]
        return sorted(found, key=lambda x: x.name.lower())

    def _transform_one(self, path: Path, key: str, force: bool) -> TransformResult:
        loc_class = locators_class_name(key)
        func_name = module_function_name(key)

        loc_path = self.locators_dir / f"{key}_locators.py"
        mod_path = self.modules_dir / f"{key}_module.py"
        feat_path = self.features_dir / f"{key}.feature"
        step_path = self.steps_dir / f"test_{key}_steps.py"

        if mod_path.exists() and not force:
            return TransformResult(
                source=path,
                key=key,
                function_name=func_name,
                module_path=mod_path,
                locators_path=loc_path,
                feature_path=feat_path,
                steps_path=step_path,
                actions=0,
                skipped=True,
            )

        actions = parse_vbs(read_recording(path))
        total = count_actions(actions)
        if total == 0:
            raise RecordingError(f"{path.name}: no contiene acciones session.findById.")

        loc_source = render_locators(key, loc_class, actions)
        mod_source = render_module(key, loc_class, actions)
        feat_source = render_feature(key)

        ast.parse(loc_source)
        ast.parse(mod_source)

        self.locators_dir.mkdir(parents=True, exist_ok=True)
        self.modules_dir.mkdir(parents=True, exist_ok=True)
        self.features_dir.mkdir(parents=True, exist_ok=True)

        loc_path.write_text(loc_source, encoding="utf-8")
        mod_path.write_text(mod_source, encoding="utf-8")
        feat_path.write_text(feat_source, encoding="utf-8")

        return TransformResult(
            source=path,
            key=key,
            function_name=func_name,
            module_path=mod_path,
            locators_path=loc_path,
            feature_path=feat_path,
            steps_path=step_path,
            actions=total,
            skipped=False,
        )
