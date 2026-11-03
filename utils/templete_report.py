import os
import base64
import re
import json
from datetime import datetime
from config.settings import Config
from utils.logger import get_logger

logger = get_logger("TempleteReport")


def _format_seconds(seconds: float) -> str:
    try:
        if seconds >= 1:
            return f"{seconds:.1f}s"
        return f"{seconds:.2f}s"
    except Exception:
        return "0s"


def get_base64_logos():
    utils_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(utils_dir)
    logo_path = os.path.join(project_root, "reports", "Logo")

    logos = {"liverpool": "", "coe": ""}

    try:
        liverpool_file = os.path.join(logo_path, "Logoliver.png")
        if os.path.exists(liverpool_file):
            with open(liverpool_file, "rb") as f:
                logos["liverpool"] = base64.b64encode(f.read()).decode()

        coe_file = os.path.join(logo_path, "centro_excelencia.png")
        if os.path.exists(coe_file):
            with open(coe_file, "rb") as f:
                logos["coe"] = base64.b64encode(f.read()).decode()
    except Exception as e:
        logger.error(f"Error cargando logos en base64: {e}")

    return logos


_ELITE_CASES = []
_CURRENT_STEPS = []
_BUSINESS_MODE = False


def set_business_mode(enabled: bool = True):
    global _BUSINESS_MODE
    _BUSINESS_MODE = bool(enabled)


def is_business_mode() -> bool:
    return _BUSINESS_MODE


def add_step(message, status="passed", level="technical"):
    if _BUSINESS_MODE and level == "technical" and status != "failed":
        return

    _CURRENT_STEPS.append({
        "message": message,
        "status": status,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    })
    logger.info(f"STEP: {message}")


def clear_results():
    global _BUSINESS_MODE
    _BUSINESS_MODE = False
    _ELITE_CASES.clear()
    _CURRENT_STEPS.clear()



def add_test_result(item, report, driver):
    screenshot_b64 = None
    if report.when == 'call':
        if driver:
            try:
                screenshot_b64 = driver.get_screenshot_as_base64()
            except Exception as e:
                logger.error(f"Error capturando pantalla: {e}")

        log_content = ""
        if report.failed:
            log_content = report.longreprtext
            match = re.search(r"AssertionError:\s*(.*)", log_content)
            if match:
                log_content = match.group(1).strip()

        steps = list(_CURRENT_STEPS)
        if not any(s["message"] == "Inicio" for s in steps):
            steps.insert(0, {"message": "Inicio", "status": "passed", "timestamp": datetime.now().strftime("%H:%M:%S")})

        outcome_label = "Finalizado" if report.passed else "Error Detectado"
        steps.append({"message": outcome_label, "status": report.outcome, "timestamp": datetime.now().strftime("%H:%M:%S")})

        display_name = getattr(item, "_bdd_scenario_title", item.name)

        # Buscar el resultado esperado en el CSV de forma dinámica
        expected_result_text = None
        try:
            from utils.csv_reader import find_expected_result
            expected_result_text = find_expected_result(item.name)
            if not expected_result_text and hasattr(item, "_bdd_scenario_title"):
                expected_result_text = find_expected_result(item._bdd_scenario_title)
            if not expected_result_text and hasattr(item, "_bdd_tags"):
                for tag in item._bdd_tags:
                    expected_result_text = find_expected_result(tag)
                    if expected_result_text:
                        break
        except Exception as e_csv:
            logger.warning(f"[-] No se pudo leer expected_result.csv para reporte HTML: {e_csv}")

        _ELITE_CASES.append({
            "nodeid": report.nodeid,
            "test_name": display_name,
            "outcome": report.outcome,
            "duration": report.duration,
            "screenshot_b64": screenshot_b64,
            "log": log_content,
            "steps": steps,
            "expected_result": expected_result_text
        })
        _CURRENT_STEPS.clear()

    return screenshot_b64


def generate_html_summary(prefix, config):
    utils_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(utils_dir)
    template_path = os.path.join(project_root, "templates", "mock_report.html")

    try:
        with open(template_path, "r", encoding="utf-8") as template_file:
            mock_html = template_file.read()
    except Exception as e:
        logger.error(f"No se pudo leer la plantilla mock_report.html: {e}")
        return

    logos = get_base64_logos()
    session_date = datetime.now().strftime("%Y-%m-%d")

    passed = sum(1 for c in _ELITE_CASES if c["outcome"] == "passed")
    failed = sum(1 for c in _ELITE_CASES if c["outcome"] in ["failed", "error"])
    total = passed + failed
    total_duration = sum(c["duration"] for c in _ELITE_CASES)
    percent = int(round((passed / total) * 100)) if total > 0 else 0
    dash_offset = 440 - (440 * percent / 100)
    duration_text = f"{total_duration:.1f}s" if total_duration >= 1 else f"{total_duration:.2f}s"

    elite_data_json = json.dumps(_ELITE_CASES)

    nexus_project = getattr(Config, "NEXUS_PROJECT", "SAP-EWM")
    app_label = getattr(Config, "APP_LABEL", "SAP GUI")

    mock_html = (
        mock_html
        .replace('src="Logo/Logoliver.png"', f'src="data:image/png;base64,{logos["liverpool"]}"')
        .replace('src="Logo/centro_excelencia.png"', f'src="data:image/png;base64,{logos["coe"]}"')
        .replace("Sesión: 2026-03-25 • Chrome 122 • QA", f"Sesión: {session_date} • {app_label} • QA")
        .replace('<span class="value">0 / 0</span>', f'<span class="value">{passed} / {total}</span>', 1)
        .replace('<span class="value">0 / 0</span>', f'<span class="value">{failed} / {total}</span>', 1)
        .replace('<span class="value">0s</span>', f'<span class="value">{duration_text}</span>')
        .replace('<div class="donut-text">0%', f'<div class="donut-text">{percent}%')
        .replace('<circle class="donut-fill" cx="75" cy="75" r="70"></circle>',
                 f'<circle class="donut-fill" cx="75" cy="75" r="70" style="stroke-dasharray: 440; stroke-dashoffset: {dash_offset};"></circle>')
    )

    dynamic_layer = _get_dynamic_js_layer(elite_data_json)

    style_match = re.search(r"<style>(.*?)</style>", mock_html, flags=re.DOTALL)
    script_match = re.search(r"<script>(.*?)</script>", mock_html, flags=re.DOTALL)
    container_match = re.search(r'(<div class="container">.*?</div>\s*)<script>', mock_html, flags=re.DOTALL)

    if not (style_match and script_match and container_match):
        logger.error("No se pudo extraer CSS/HTML/script desde mock_report.html.")
        return

    injected = (
        f'<meta name="nexus-project" content="{nexus_project}">\n'
        f"<style>{style_match.group(1)}</style>\n"
        f'<div class="elite-overlay">{container_match.group(1)}</div>\n'
        f"<script>{script_match.group(1)}</script>\n"
        f"{dynamic_layer}"
    )
    prefix.extend([injected])


def _get_dynamic_js_layer(elite_data_json):
    js_content = """
    <style>
      .elite-overlay {
          position: fixed;
          inset: 0;
          z-index: 999999;
          overflow: auto;
          background: var(--bg-color);
      }
      #results-table, #results-table-head, #environment, #summary-container, #summary { display: none !important; }
      .summary__data > h2 { display: none !important; }
      .step-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.5rem 0;
      }
      .step-time {
          font-size: 0.7rem;
          color: var(--text-secondary);
          font-family: 'JetBrains Mono', monospace;
      }
    </style>
    <script>
      function syncEliteReport() {
        const eliteData = [[ELITE_DATA_JSON]];
        const listContainer = document.querySelector('.test-list');
        if (!listContainer) return;

        listContainer.innerHTML = '';
        let passed = 0;
        let failed = 0;
        let totalTime = 0;

        eliteData.forEach((test) => {
          const status = test.outcome === 'passed' ? 'passed' : (['failed', 'error'].includes(test.outcome) ? 'failed' : 'other');
          if (status === 'passed') passed++;
          if (status === 'failed') failed++;
          totalTime += test.duration;

          const testName = test.test_name;
          const duration = test.duration.toFixed(2) + 's';
          const logText = test.log || '';
          const screenshot = test.screenshot_b64;
          const steps = test.steps || [];
          const internalId = 'log-' + Math.random().toString(36).slice(2, 11);

          let stepsHtml = '';
          if (steps.length > 0) {
              stepsHtml = steps.map(step => `
                  <div class="step-item step-${step.status}">
                      <span>${step.message}</span>
                      <span class="step-time">${step.timestamp}</span>
                  </div>
              `).join('');
          } else {
              stepsHtml = `
                <div class="step-item step-passed">Inicio de Prueba</div>
                <div class="step-item step-${status}">${status === 'passed' ? 'Finalizado' : 'Error Detectado'}</div>
              `;
          }

          let expectedHtml = test.expected_result ? `
            <div class="expected-box-report" style="background: rgba(120, 37, 111, 0.05); border: 1px dashed rgba(120, 37, 111, 0.3); border-radius: 8px; padding: 12px 16px; margin-bottom: 1rem; width: 100%; box-sizing: border-box;">
              <div style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: #78256f; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
                <span>📋</span> Resultado Esperado
              </div>
              <div style="font-size: 0.85rem; color: var(--text-primary); line-height: 1.4;">${test.expected_result}</div>
            </div>
          ` : '';

          let evidenceHtml = `
            ${expectedHtml}
            <div class="step-timeline">
                ${stepsHtml}
            </div>
            <div style="width: 100%; display: flex; flex-direction: column; gap: 1rem; align-items: flex-start; margin-bottom: 1rem;">
              ${screenshot ? `<div style="max-width: 100%; border-radius: 8px; border: 1px solid var(--border); overflow: hidden;">
                <img src="data:image/png;base64,${screenshot}" style="max-width:100%; display:block; cursor:pointer;" onclick="window.open(this.src)"/>
              </div>` : ''}
            </div>
            ${logText ? `<div id="${internalId}" style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; background: #020617; color: #f43f5e; padding: 1rem; border-radius: 8px; overflow-x: auto; max-height: 400px; white-space: pre-wrap; font-weight: 500;">${logText}</div>` : ''}
          `;

          const details = document.createElement('details');
          details.className = 'test-item';
          details.setAttribute('data-status', status);
          if (status === 'failed') details.setAttribute('open', '');
          details.innerHTML = `
            <summary>
              <div class="test-info">
                <div class="status-dot dot-${status}"></div>
                <p style="font-weight: 600; color: var(--text-primary);">${testName}</p>
              </div>
              <div style="display: flex; align-items: center; gap: 2rem;">
                ${status === 'failed' ? '<span style="color: var(--accent-danger); font-size: 0.75rem; font-weight: 700;">FALLO</span>' : `<span class="test-meta">${duration}</span>`}
                <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
              </div>
            </summary>
            <div class="evidence-body">${evidenceHtml}</div>
          `;
          listContainer.appendChild(details);
        });

        const total = passed + failed;
        const successValue = document.querySelector('.card.success .value');
        const dangerValue = document.querySelector('.card.danger .value');
        const durationValue = document.querySelector('.stats-grid .card:not(.success):not(.danger) .value');

        if (successValue) successValue.innerText = `${passed} / ${total}`;
        if (dangerValue) dangerValue.innerText = `${failed} / ${total}`;
        if (durationValue) durationValue.innerText = totalTime.toFixed(1) + 's';

        const percent = total > 0 ? Math.round((passed / total) * 100) : 0;
        const donutFill = document.querySelector('.donut-fill');
        if (donutFill) {
          const dashoffset = 440 - (440 * percent / 100);
          donutFill.style.strokeDasharray = '440';
          donutFill.style.strokeDashoffset = dashoffset;
        }
        const donutText = document.querySelector('.donut-text');
        if (donutText) {
          donutText.innerHTML = `${percent}%<br><span style="font-size: 0.65rem; color: var(--text-secondary); font-weight: 500;">SUCCESS</span>`;
        }
      }

      window.addEventListener('load', function () {
        document.body.setAttribute('data-theme', 'light');
        document.documentElement.setAttribute('data-theme', 'light');
        syncEliteReport();
      });
    </script>
    """
    return js_content.replace("[[ELITE_DATA_JSON]]", elite_data_json)
