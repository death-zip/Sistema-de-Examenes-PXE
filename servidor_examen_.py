from flask import Flask, request, jsonify, session, redirect, url_for, send_file, render_template
from flask_cors import CORS
import json, os, socket, base64, io
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))
CORS(app, supports_credentials=True)

# ── Carpetas ──────────────────────────────────────────────────
for d in ['respuestas', 'imagenes']:
    os.makedirs(d, exist_ok=True)

# ── Configuración por defecto ─────────────────────────────────

# Estado de edicion - bloquea el examen mientras el docente edita
import threading
_estado_edicion = {'editando': False, 'version': 0}
_estado_lock = threading.Lock()

# Registro de alumnos que ya enviaron (nombre normalizado -> archivo)
_alumnos_enviaron = {}
_envios_lock = threading.Lock()

def _normalizar_nombre(nombre):
    """Normaliza el nombre para comparacion: minusculas, sin espacios extra."""
    return ' '.join(nombre.lower().strip().split())

def _cargar_envios_previos():
    """Carga los envios existentes en la carpeta respuestas/ al iniciar."""
    if not os.path.exists('respuestas'):
        return
    for archivo in os.listdir('respuestas'):
        if not archivo.endswith('.json'):
            continue
        try:
            with open(f'respuestas/{archivo}', 'r', encoding='utf-8') as f:
                d = json.load(f)
            nombre = d.get('nombre', '')
            if nombre:
                clave = _normalizar_nombre(nombre)
                _alumnos_enviaron[clave] = archivo
        except:
            continue

_cargar_envios_previos()

@app.route('/estado_examen')
def estado_examen():
    return jsonify(_estado_edicion)

CONFIG_FILE  = 'config_examen.json'
ADMIN_PASS   = os.environ.get('ADMIN_PASS', 'admin123')

CONFIG_DEFAULT = {
    "titulo": "Examen de Pensamiento Crítico",
    "materia": "Gestión de Redes",
    "tiempo_minutos": 0,   # 0 = sin límite
    "preguntas": [
        {
            "id": 1,
            "tipo": "opcion_multiple",
            "texto": "¿Cuál de las siguientes afirmaciones refleja mejor la idea de que el trabajo puede ser creativo o alienante según su contexto?",
            "imagen": "",
            "opciones": [
                {"id": "a", "texto": "El trabajo siempre es productivo si genera dinero"},
                {"id": "b", "texto": "El trabajo tiene valor cuando quien lo realiza comprende y controla el proceso"},
                {"id": "c", "texto": "Todo trabajo es igualmente valioso sin importar las condiciones"},
                {"id": "d", "texto": "El trabajo solo es alienante en fábricas"}
            ],
            "respuesta_correcta": "b",
            "puntos": 1
        },
        {
            "id": 2,
            "tipo": "opcion_multiple",
            "texto": "En una sociedad donde muchas personas realizan tareas repetitivas sin entender su propósito final, ¿qué consecuencia es más probable?",
            "imagen": "",
            "opciones": [
                {"id": "a", "texto": "Mayor eficiencia económica en todos los sectores"},
                {"id": "b", "texto": "Pérdida de sentido y desconexión de las personas con su trabajo"},
                {"id": "c", "texto": "Aumento automático de la satisfacción laboral"},
                {"id": "d", "texto": "Eliminación de todas las jerarquías organizacionales"}
            ],
            "respuesta_correcta": "b",
            "puntos": 1
        },
        {
            "id": 3,
            "tipo": "opcion_multiple",
            "texto": "¿Qué característica distingue a un \"trabajo sin sentido\" de uno significativo?",
            "imagen": "",
            "opciones": [
                {"id": "a", "texto": "El salario que se recibe"},
                {"id": "b", "texto": "Si la persona misma cree que su trabajo contribuye a algo valioso"},
                {"id": "c", "texto": "La cantidad de horas trabajadas"},
                {"id": "d", "texto": "El nivel educativo requerido"}
            ],
            "respuesta_correcta": "b",
            "puntos": 1
        },
        {
            "id": 4,
            "tipo": "opcion_multiple",
            "texto": "Si en una empresa las decisiones las toman solo los altos ejecutivos sin consultar a quienes realizan el trabajo directo, ¿qué tipo de relación laboral se establece?",
            "imagen": "",
            "opciones": [
                {"id": "a", "texto": "Una relación de colaboración horizontal"},
                {"id": "b", "texto": "Una relación jerárquica donde los trabajadores están alienados del proceso de decisión"},
                {"id": "c", "texto": "Una organización perfectamente democrática"},
                {"id": "d", "texto": "Un modelo donde todos tienen igual poder"}
            ],
            "respuesta_correcta": "b",
            "puntos": 1
        },
        {
            "id": 5,
            "tipo": "opcion_multiple",
            "texto": "¿Cuál de estos ejemplos ilustra mejor un trabajo que genera \"valor social\" más allá del valor económico?",
            "imagen": "",
            "opciones": [
                {"id": "a", "texto": "Un trader que genera millones en la bolsa de valores"},
                {"id": "b", "texto": "Una enfermera que cuida pacientes en una comunidad rural"},
                {"id": "c", "texto": "Un consultor que optimiza despidos corporativos"},
                {"id": "d", "texto": "Un especulador inmobiliario que infla precios"}
            ],
            "respuesta_correcta": "b",
            "puntos": 1
        },
        {
            "id": 6,
            "tipo": "opcion_multiple",
            "texto": "En antropología, cuando estudiamos diferentes culturas, ¿qué enfoque es más ético y científico?",
            "imagen": "",
            "opciones": [
                {"id": "a", "texto": "Juzgar todas las prácticas según los estándares de nuestra propia cultura"},
                {"id": "b", "texto": "Intentar comprender cada práctica dentro de su propio contexto cultural"},
                {"id": "c", "texto": "Asumir que la cultura occidental es superior a todas las demás"},
                {"id": "d", "texto": "Ignorar las diferencias culturales y tratarlas como irrelevantes"}
            ],
            "respuesta_correcta": "b",
            "puntos": 1
        },
        {
            "id": 7,
            "tipo": "opcion_multiple",
            "texto": "¿Qué demuestra el hecho de que diferentes sociedades organizan el intercambio de bienes de formas muy distintas (trueque, regalo, mercado, etc.)?",
            "imagen": "",
            "opciones": [
                {"id": "a", "texto": "Que solo el capitalismo moderno es eficiente"},
                {"id": "b", "texto": "Que las formas de organización económica son construcciones culturales, no leyes naturales"},
                {"id": "c", "texto": "Que las sociedades primitivas no entienden la economía"},
                {"id": "d", "texto": "Que el dinero siempre ha existido en todas las culturas"}
            ],
            "respuesta_correcta": "b",
            "puntos": 1
        },
        {
            "id": 8,
            "tipo": "opcion_multiple",
            "texto": "Si una persona siente que su trabajo es inútil pero lo mantiene por necesidad económica, esto refleja principalmente:",
            "imagen": "",
            "opciones": [
                {"id": "a", "texto": "Falta de ética laboral de esa persona"},
                {"id": "b", "texto": "Una contradicción entre supervivencia económica y realización personal"},
                {"id": "c", "texto": "Que todos los trabajos son igualmente satisfactorios"},
                {"id": "d", "texto": "Que el sistema laboral actual es perfecto"}
            ],
            "respuesta_correcta": "b",
            "puntos": 1
        },
        {
            "id": 9,
            "tipo": "opcion_multiple",
            "texto": "¿Qué revela el concepto de \"deuda\" cuando se estudia históricamente en diferentes culturas?",
            "imagen": "",
            "opciones": [
                {"id": "a", "texto": "Que siempre ha sido una relación puramente económica"},
                {"id": "b", "texto": "Que ha tenido significados morales, sociales y políticos variables según el contexto"},
                {"id": "c", "texto": "Que los bancos son una invención reciente sin precedentes históricos"},
                {"id": "d", "texto": "Que todas las culturas han tratado la deuda exactamente igual"}
            ],
            "respuesta_correcta": "b",
            "puntos": 1
        },
        {
            "id": 10,
            "tipo": "opcion_multiple",
            "texto": "En el contexto de las redes informáticas, ¿qué principio organizativo se asemeja más a las formas cooperativas de organización social?",
            "imagen": "",
            "opciones": [
                {"id": "a", "texto": "Un sistema completamente centralizado donde un servidor controla todo"},
                {"id": "b", "texto": "Una red distribuida donde múltiples nodos comparten responsabilidades"},
                {"id": "c", "texto": "Un modelo donde solo una computadora puede tomar decisiones"},
                {"id": "d", "texto": "Una estructura jerárquica rígida sin redundancia"}
            ],
            "respuesta_correcta": "b",
            "puntos": 1
        }
    ]
}

def cargar_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return CONFIG_DEFAULT.copy()

def guardar_config(cfg):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

def calcular_calificacion(respuestas_alumno, preguntas):
    puntos_total  = sum(p.get('puntos', 1) for p in preguntas if p['tipo'] != 'abierta')
    puntos_obtenidos = 0
    correctas = 0
    for p in preguntas:
        if p['tipo'] == 'abierta':
            continue
        resp = respuestas_alumno.get(f"pregunta_{p['id']}", "")
        correcta = p.get('respuesta_correcta', '')
        if p['tipo'] == 'seleccion_multiple':
            dadas    = set(resp) if isinstance(resp, list) else set()
            esperadas = set(correcta) if isinstance(correcta, list) else set()
            if dadas == esperadas:
                puntos_obtenidos += p.get('puntos', 1)
                correctas += 1
        else:
            if str(resp).strip().lower() == str(correcta).strip().lower():
                puntos_obtenidos += p.get('puntos', 1)
                correctas += 1
    calificacion = round((puntos_obtenidos / puntos_total) * 10, 1) if puntos_total > 0 else 0
    return correctas, puntos_total, calificacion

def get_ips():
    ips = []
    try:
        hostname = socket.gethostname()
        raw = socket.getaddrinfo(hostname, None)
        ips = list(set([i[4][0] for i in raw if ':' not in i[4][0] and i[4][0] != '127.0.0.1']))
    except:
        pass
    return ips or ['(revisa ipconfig)']

# ══════════════════════════════════════════════════════════════
#  RUTAS PÚBLICAS
# ══════════════════════════════════════════════════════════════

@app.route('/ping')
def ping():
    return jsonify({'status': 'ok', 'servidor': 'Tecmilenio Examenes'})

@app.route('/config_examen')
def config_examen():
    """El HTML carga el examen desde aquí"""
    cfg = cargar_config()
    # No mandar respuestas correctas al alumno
    safe = {k: v for k, v in cfg.items() if k != 'preguntas'}
    safe['preguntas'] = []
    for p in cfg['preguntas']:
        sp = {k: v for k, v in p.items() if k not in ('respuesta_correcta',)}
        safe['preguntas'].append(sp)
    return jsonify(safe)

@app.route('/guardar', methods=['POST'])
def guardar_respuestas():
    try:
        datos = request.json
        nombre_raw = datos.get('nombre', 'anonimo')
        clave = _normalizar_nombre(nombre_raw)

        # Verificar si el alumno ya envió el examen
        with _envios_lock:
            if clave in _alumnos_enviaron:
                print(f'[DUPLICADO] {nombre_raw} ya envió el examen')
                return jsonify({
                    'status': 'duplicado',
                    'mensaje': f'Ya se registró un envío a nombre de "{nombre_raw}". Solo se permite un envío por alumno.'
                }), 409

        cfg   = cargar_config()
        ts    = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        nombre = nombre_raw.replace(' ', '_')
        correctas, total, calificacion = calcular_calificacion(
            datos.get('respuestas', {}), cfg['preguntas'])
        datos['calificacion'] = calificacion
        datos['correctas']    = correctas
        datos['total_puntos'] = total
        fname = f'respuestas/examen_{nombre}_{ts}.json'
        with open(fname, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)

        # Registrar el envío para bloquear duplicados
        with _envios_lock:
            _alumnos_enviaron[clave] = fname

        print(f'[OK] {nombre} | Cal: {calificacion} ({correctas}/{total})')
        return jsonify({'status': 'ok', 'mensaje': 'Examen enviado correctamente',
                        'calificacion': calificacion, 'correctas': correctas, 'total': total})
    except Exception as e:
        print(f'[ERROR] {e}')
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500

@app.route('/respuestas_correctas')
def respuestas_correctas():
    """Manda las respuestas correctas al alumno después de enviar"""
    cfg = cargar_config()
    correctas = {}
    for p in cfg['preguntas']:
        if p['tipo'] != 'abierta':
            correctas['pregunta_' + str(p['id'])] = p.get('respuesta_correcta', '')
    return jsonify(correctas)

@app.route('/examen')
def examen_alumno():
    server_url = request.host_url.rstrip('/')
    return render_template('examen.html', server_url=server_url)

@app.route('/imagen/<nombre>')
def servir_imagen(nombre):
    path = os.path.join('imagenes', nombre)
    if os.path.exists(path):
        return send_file(path)
    return '', 404

# ══════════════════════════════════════════════════════════════
#  AUTENTICACIÓN ADMIN
# ══════════════════════════════════════════════════════════════

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = ''
    if request.method == 'POST':
        is_json = 'application/json' in (request.content_type or '')
        pwd = (request.get_json(silent=True) or {}).get('password', '') if is_json else request.form.get('password', '')
        if pwd == ADMIN_PASS:
            session['admin'] = True
            return jsonify({'ok': True}) if is_json else redirect('/admin')
        error = 'Contraseña incorrecta'
        if is_json:
            return jsonify({'ok': False, 'error': error}), 401
    return render_template('login.html', error=error)

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            return redirect('/admin/login')
        return f(*args, **kwargs)
    return decorated

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect('/admin/login')

# ══════════════════════════════════════════════════════════════
#  PANEL ADMIN
# ══════════════════════════════════════════════════════════════

@app.route('/admin')
@admin_required
def admin_home():
    cfg   = cargar_config()
    total = len(os.listdir('respuestas'))
    npregs = len(cfg['preguntas'])
    return render_template('admin.html', npregs=npregs, total=total)

# ── Editor de examen ──────────────────────────────────────────

@app.route('/admin/examen', methods=['GET'])
@admin_required
def admin_examen():
    cfg = cargar_config()
    pregs_json = json.dumps(cfg['preguntas'], ensure_ascii=False)
    return render_template('editor.html', cfg=cfg, pregs_json=pregs_json)

@app.route('/admin/set_editando', methods=['POST'])
@admin_required
def set_editando():
    data = request.get_json(silent=True) or {}
    with _estado_lock:
        _estado_edicion['editando'] = data.get('editando', False)
    return jsonify({'ok': True})

@app.route('/admin/guardar_config', methods=['POST'])
@admin_required
def admin_guardar_config():
    try:
        cfg = request.json
        guardar_config(cfg)
        with _estado_lock:
            _estado_edicion['editando'] = False
            _estado_edicion['version'] += 1
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

# ── Descarga Excel ────────────────────────────────────────────

@app.route('/admin/descargar')
@admin_required
def admin_descargar():
    try:
        import openpyxl
        from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
    except ImportError:
        return '<h2>Instala openpyxl: pip install openpyxl</h2>', 500

    archivos = sorted(os.listdir('respuestas'))
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Resultados'

    verde   = PatternFill('solid', fgColor='D4EDDA')
    naranja = PatternFill('solid', fgColor='FFE8C8')
    rojo    = PatternFill('solid', fgColor='F8D7DA')
    header_fill = PatternFill('solid', fgColor='00A859')
    header_font = Font(color='FFFFFF', bold=True)
    bold = Font(bold=True)
    center = Alignment(horizontal='center', vertical='center')
    thin = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )

    headers = ['Nombre', 'Calificación', 'Correctas', 'Total Puntos', 'Estado', 'Fecha y Hora']
    for ci, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=ci, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center
        cell.border = thin

    for ri, archivo in enumerate(archivos, 2):
        try:
            with open(f'respuestas/{archivo}', 'r', encoding='utf-8') as f:
                d = json.load(f)
        except:
            continue
        cal   = float(d.get('calificacion', 0))
        estado = 'Aprobado' if cal >= 6 else 'Reprobado'
        fill   = verde if cal >= 8 else (naranja if cal >= 6 else rojo)
        row    = [d.get('nombre',''), cal, d.get('correctas','?'),
                  d.get('total_puntos','?'), estado, d.get('timestamp','')]
        for ci, val in enumerate(row, 1):
            cell = ws.cell(row=ri, column=ci, value=val)
            cell.alignment = center
            cell.border = thin
            if ci in (2, 5):
                cell.fill = fill
                if ci == 2:
                    cell.font = Font(bold=True)

    ws.column_dimensions['A'].width = 30
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 12
    ws.column_dimensions['D'].width = 14
    ws.column_dimensions['E'].width = 14
    ws.column_dimensions['F'].width = 22

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    fname = f'resultados_examen_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
    return send_file(buf, as_attachment=True, download_name=fname,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# ══════════════════════════════════════════════════════════════
#  PÁGINA PÚBLICA DE RESULTADOS
# ══════════════════════════════════════════════════════════════

@app.route('/')
def home():
    total    = len(os.listdir('respuestas'))
    logo_svg = 'https://upload.wikimedia.org/wikipedia/commons/6/65/Universidad_Tecmilenio.png'
    return render_template('home.html', total=total, logo_svg=logo_svg)

@app.route('/ver')
def ver_respuestas():
    archivos = sorted(os.listdir('respuestas'))
    logo_svg = 'https://upload.wikimedia.org/wikipedia/commons/6/65/Universidad_Tecmilenio.png'

    if not archivos:
        return render_template('resultados_vacio.html', logo_svg=logo_svg)

    calificaciones = []
    alumnos = []
    for archivo in archivos:
        try:
            with open(f'respuestas/{archivo}', 'r', encoding='utf-8') as f:
                d = json.load(f)
        except:
            continue
        nombre    = d.get('nombre', 'Sin nombre')
        fecha     = d.get('timestamp', 'Sin fecha')
        cal       = d.get('calificacion', None)
        correctas = d.get('correctas', '?')
        total     = d.get('total_puntos', 10)
        alumno = {'nombre': nombre, 'fecha': fecha, 'cal': cal, 'correctas': correctas, 'total': total}
        if cal is not None:
            cal = float(cal)
            alumno['cal'] = cal
            calificaciones.append(cal)
            if cal >= 8:
                alumno['color'], alumno['estado'], alumno['bg'] = '#28a745', 'Aprobado', '#d4edda'
            elif cal >= 6:
                alumno['color'], alumno['estado'], alumno['bg'] = '#fd7e14', 'Regular', '#fff3cd'
            else:
                alumno['color'], alumno['estado'], alumno['bg'] = '#dc3545', 'Reprobado', '#f8d7da'
        alumnos.append(alumno)

    promedio   = round(sum(calificaciones)/len(calificaciones), 1) if calificaciones else 0
    cp         = '#28a745' if promedio >= 8 else ('#fd7e14' if promedio >= 6 else '#dc3545')
    aprobados  = sum(1 for c in calificaciones if c >= 6)
    reprobados = len(calificaciones) - aprobados
    pct        = round(aprobados/len(calificaciones)*100) if calificaciones else 0

    return render_template('resultados.html',
        logo_svg=logo_svg, alumnos=alumnos, total_alumnos=len(archivos),
        promedio=promedio, cp=cp, aprobados=aprobados, reprobados=reprobados, pct=pct)

# ══════════════════════════════════════════════════════════════
#  ARRANQUE
# ══════════════════════════════════════════════════════════════

LOGO_TEC = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║         TECMILENIO — SISTEMA DE EXÁMENES v2.0                ║
║         Gestión de Redes | 2026                              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""

if __name__ == '__main__':
    ips = get_ips()
    print('\033[92m' + LOGO_TEC + '\033[0m')
    print('Servidor iniciado correctamente\n')
    print('Direcciones disponibles:\n')
    for ip in ips:
        print(f'   -- http://{ip}:5000         \033[90m← Página principal\033[0m')
        print(f'   -- http://{ip}:5000/examen  \033[90m← Examen para alumnos\033[0m')
        print(f'   -- http://{ip}:5000/ver     \033[90m← Resultados públicos\033[0m')
        admin_hint = ADMIN_PASS if ADMIN_PASS == 'admin123' else '(definida en variable de entorno)'
        print(f'   -- http://{ip}:5000/admin   \033[90m← Panel docente (contraseña: {admin_hint})\033[0m')
        print()
    print('INFO: Instala openpyxl para descarga Excel:  pip install openpyxl')
    print('Presiona Ctrl+C para detener\n')
    app.run(host='0.0.0.0', port=5000, debug=False)
