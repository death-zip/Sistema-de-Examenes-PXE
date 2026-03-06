# Sistema de Examenes PXE - Tecmilenio

## Tabla de Contenidos

1. [Descripcion General](#1-descripcion-general)
2. [Arquitectura del Sistema](#2-arquitectura-del-sistema)
3. [Estructura del Proyecto](#3-estructura-del-proyecto)
4. [Tecnologias y Dependencias](#4-tecnologias-y-dependencias)
5. [Instalacion y Configuracion](#5-instalacion-y-configuracion)
6. [Endpoints de la API REST](#6-endpoints-de-la-api-rest)
7. [Flujo de Funcionamiento End-to-End](#7-flujo-de-funcionamiento-end-to-end)
8. [Interfaz del Estudiante (examen.html)](#8-interfaz-del-estudiante-examenhtml)
9. [Panel de Administracion (Profesor)](#9-panel-de-administracion-profesor)
10. [Modelo de Datos](#10-modelo-de-datos)
11. [Sistema de Calificacion](#11-sistema-de-calificacion)
12. [Descubrimiento Automatico de Servidor](#12-descubrimiento-automatico-de-servidor)
13. [Sincronizacion de Estado en Tiempo Real](#13-sincronizacion-de-estado-en-tiempo-real)
14. [Exportacion de Resultados a Excel](#14-exportacion-de-resultados-a-excel)
15. [Componentes de Interfaz de Usuario](#15-componentes-de-interfaz-de-usuario)
16. [Seguridad](#16-seguridad)
17. [Patrones de Comunicacion de Red](#17-patrones-de-comunicacion-de-red)
18. [Limitaciones Conocidas](#18-limitaciones-conocidas)

---

## 1. Descripcion General

**Sistema de Examenes PXE** es una aplicacion web cliente-servidor disenada para administrar examenes en entornos de aula (especificamente para la Universidad Tecmilenio). Permite a un profesor crear, editar y administrar examenes, mientras los estudiantes los resuelven desde sus navegadores con calificacion automatica e inmediata.

### Caracteristicas Principales

- Creacion y edicion de examenes con interfaz visual
- Tres tipos de preguntas: opcion multiple, seleccion multiple y respuesta abierta
- Calificacion automatica en el servidor
- Descubrimiento automatico del servidor en la red local (sin configuracion manual)
- Temporizador configurable con auto-envio al expirar
- Resultados en tiempo real con estadisticas
- Exportacion de resultados a Excel (.xlsx)
- Bloqueo de examenes durante edicion del profesor
- Soporte para imagenes en preguntas
- Interfaz responsive (escritorio y movil)

---

## 2. Arquitectura del Sistema

### Diagrama General

```
+──────────────────────────────────+       HTTP/REST        +────────────────────────────────────+
|     Navegador del Estudiante     |  <─────────────────>   |        Servidor Flask (Python)      |
|     (examen.html - Vanilla JS)   |                        |      (servidor_examen_.py:5000)     |
|                                  |                        |                                    |
|  1. Detectar IP local (WebRTC)   |   GET /ping            |  Rutas Publicas:                   |
|  2. Escanear red buscando server |   GET /config_examen   |    /ping, /config_examen,           |
|  3. Cargar configuracion examen  |   POST /guardar        |    /guardar, /respuestas_correctas, |
|  4. Renderizar preguntas         |   GET /estado_examen   |    /imagen/<nombre>, /, /ver        |
|  5. Polling cada 3s              |   GET /respuestas_     |                                    |
|  6. Enviar respuestas            |       correctas        |  Rutas Admin (Sesion):              |
|  7. Mostrar calificacion         |                        |    /admin/login, /admin,            |
+──────────────────────────────────+                        |    /admin/examen, /admin/descargar, |
                                                            |    /admin/guardar_config,           |
+──────────────────────────────────+                        |    /admin/set_editando              |
|     Navegador del Profesor       |  <─────────────────>   |                                    |
|     (Paginas admin generadas     |   GET/POST /admin/*    |  Almacenamiento:                   |
|      por el servidor Flask)      |                        |    config_examen.json               |
+──────────────────────────────────+                        |    respuestas/*.json                |
                                                            |    imagenes/*                       |
                                                            +────────────────────────────────────+
```

### Modelo de Comunicacion

| Aspecto | Detalle |
|---------|---------|
| Protocolo | HTTP/REST |
| Formato de datos | JSON |
| Autenticacion admin | Cookies de sesion Flask |
| Sincronizacion estudiantes | Polling cada 3 segundos a `/estado_examen` |
| Descubrimiento de servidor | Escaneo de subred via WebRTC + IPs hardcodeadas |

---

## 3. Estructura del Proyecto

```
Sistema-de-Examenes-PXE/
|-- examen.html              # Frontend completo del estudiante (HTML + CSS + JS)
|-- servidor_examen_.py      # Servidor backend Flask (API + admin + paginas)
|-- README.md                # Esta documentacion
|
|-- config_examen.json       # (generado) Configuracion del examen actual
|-- respuestas/              # (generado) Respuestas de estudiantes en JSON
|   |-- examen_Juan_20260305_143045_123456.json
|   |-- examen_Maria_20260305_143112_654321.json
|   +-- ...
|-- imagenes/                # (generado) Imagenes de preguntas
|   |-- pregunta1.png
|   +-- ...
```

> Las carpetas `respuestas/` e `imagenes/` se crean automaticamente al iniciar el servidor.

---

## 4. Tecnologias y Dependencias

### Backend (Python)

| Paquete | Proposito | Requerido |
|---------|-----------|-----------|
| `Flask` | Framework web, rutas, sesiones, templates | Si |
| `flask-cors` | Soporte Cross-Origin Resource Sharing | Si |
| `openpyxl` | Generacion de archivos Excel (.xlsx) | Opcional* |

> *`openpyxl` solo es necesario para la funcion de descarga de resultados en Excel. El sistema funciona sin el.

**Libreria estandar de Python utilizada:** `json`, `os`, `socket`, `base64`, `io`, `threading`, `datetime`, `functools`

### Frontend

| Tecnologia | Uso |
|------------|-----|
| HTML5 | Estructura del documento |
| CSS3 | Estilos responsive, animaciones, flexbox, media queries |
| JavaScript ES6+ (Vanilla) | Logica de cliente sin frameworks |
| WebRTC API | Deteccion de IP local del estudiante |
| Fetch API | Comunicacion HTTP con el servidor |

### Instalacion de Dependencias

```bash
pip install flask flask-cors openpyxl
```

---

## 5. Instalacion y Configuracion

### Requisitos Previos

- Python 3.6 o superior
- pip (gestor de paquetes de Python)
- Red local (LAN) compartida entre servidor y estudiantes

### Pasos de Instalacion

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/Sistema-de-Examenes-PXE.git
cd Sistema-de-Examenes-PXE

# 2. Instalar dependencias
pip install flask flask-cors openpyxl

# 3. Iniciar el servidor
python servidor_examen_.py
```

### Salida Esperada al Iniciar

```
============================================================
  SERVIDOR DE EXAMENES - TECMILENIO
============================================================
  Accede desde cualquier navegador en la red:

    > http://192.168.1.100:5000

  Panel de administracion:
    > http://192.168.1.100:5000/admin/login

  Examen para alumnos:
    > Abrir 'examen.html' en el navegador

============================================================
```

### Configuracion Hardcodeada

| Parametro | Valor | Ubicacion | Descripcion |
|-----------|-------|-----------|-------------|
| Puerto | `5000` | `servidor_examen_.py:978` | Puerto del servidor Flask |
| Password admin | `admin123` | `servidor_examen_.py:288` | Contrasena del panel admin |
| Secret key | `tecmilenio_examenes_2026` | `servidor_examen_.py:14` | Clave de sesion Flask |
| IPs candidatas | Multiples subredes | `examen.html:135-155` | IPs para descubrimiento |
| Intervalo polling | `3000ms` | `examen.html:402` | Frecuencia de verificacion de estado |
| Timeout de ping | `1500ms` | `examen.html:158` | Timeout por intento de conexion |
| Timeout de envio | `8000ms` | `examen.html:345` | Timeout al enviar respuestas |

---

## 6. Endpoints de la API REST

### Rutas Publicas (Sin Autenticacion)

#### `GET /ping`
Verificacion de disponibilidad del servidor. Usado por el cliente para descubrimiento automatico.

```
Respuesta: {"status": "ok", "servidor": "Tecmilenio Examenes"}
```

#### `GET /config_examen`
Retorna la configuracion del examen **sin las respuestas correctas**.

```json
{
  "titulo": "Examen de Pensamiento Critico",
  "materia": "Pensamiento Critico",
  "tiempo_minutos": 60,
  "preguntas": [
    {
      "id": 1,
      "tipo": "opcion_multiple",
      "texto": "Segun Marx...",
      "puntos": 1,
      "opciones": [
        {"id": "a", "texto": "Opcion A"},
        {"id": "b", "texto": "Opcion B"}
      ]
    }
  ]
}
```

> El campo `respuesta_correcta` se elimina antes de enviarlo al cliente.

#### `POST /guardar`
Recibe y califica las respuestas de un estudiante.

**Request Body:**
```json
{
  "nombre": "Juan Garcia",
  "timestamp": "5/3/2026, 14:30:45",
  "respuestas": {
    "pregunta_1": "b",
    "pregunta_2": ["a", "c"],
    "pregunta_3": "Respuesta escrita del alumno"
  }
}
```

**Respuesta Exitosa:**
```json
{
  "status": "ok",
  "mensaje": "Examen enviado correctamente",
  "calificacion": 8.0,
  "correctas": 8,
  "total": 10
}
```

#### `GET /respuestas_correctas`
Retorna las respuestas correctas (se llama despues del envio para mostrar retroalimentacion).

```json
{
  "pregunta_1": "b",
  "pregunta_2": ["a", "c"],
  "pregunta_3": ""
}
```

> Las preguntas abiertas retornan cadena vacia.

#### `GET /estado_examen`
Retorna el estado actual del examen (usado por polling).

```json
{
  "editando": false,
  "version": 3
}
```

#### `GET /imagen/<nombre>`
Sirve imagenes almacenadas en la carpeta `imagenes/`. Retorna 404 si no existe.

#### `GET /`
Pagina de inicio del servidor con estado general y enlaces a resultados y administracion.

#### `GET /ver`
Pagina publica de resultados con auto-refresco cada 15 segundos. Muestra:
- Total de estudiantes que han enviado
- Calificacion promedio
- Cantidad de aprobados/reprobados
- Porcentaje de aprobacion
- Tabla detallada con cada estudiante
- Boton de descarga Excel

---

### Rutas de Administracion (Requieren Sesion)

Todas las rutas `/admin/*` (excepto `/admin/login`) requieren autenticacion previa. Se usa el decorador `admin_required` que verifica `session['admin'] == True`.

#### `GET|POST /admin/login`
Formulario de inicio de sesion. Acepta password via formulario HTML o JSON.

- **Exito:** Redirige a `/admin`
- **Error:** Muestra mensaje de error

#### `GET /admin`
Dashboard de administracion con tarjetas de estadisticas:
- Numero de preguntas del examen actual
- Respuestas recibidas
- Enlace al editor de examen
- Enlace a resultados
- Boton de descarga Excel

#### `GET /admin/examen`
Editor completo de examenes con interfaz visual. Permite:
- Editar titulo, materia, tiempo limite
- Agregar preguntas de cualquier tipo
- Editar/eliminar preguntas existentes
- Reordenar preguntas (flechas arriba/abajo)
- Subir imagenes por pregunta
- Administrar opciones de respuesta multiple
- Marcar respuestas correctas
- Configurar puntos por pregunta

#### `POST /admin/set_editando`
Notifica al servidor que el profesor esta editando el examen.

**Request Body:**
```json
{"editando": true}
```

Al activarse, los estudiantes conectados ven un overlay bloqueante con el mensaje "El profesor esta editando el examen".

#### `POST /admin/guardar_config`
Guarda la configuracion del examen editada.

**Request Body:** Objeto JSON completo de configuracion del examen.

**Efectos:**
- Guarda en `config_examen.json`
- Incrementa el numero de version
- Desactiva flag de edicion
- Los estudiantes detectan el cambio de version y recargan la pagina

#### `GET /admin/descargar`
Genera y descarga un archivo Excel (.xlsx) con todos los resultados.

#### `GET /admin/logout`
Cierra la sesion de administrador y redirige al login.

---

## 7. Flujo de Funcionamiento End-to-End

### Fase 1: Inicio del Servidor

1. El profesor ejecuta `python servidor_examen_.py`
2. Se crean las carpetas `respuestas/` e `imagenes/` si no existen
3. Se carga `config_examen.json` (o se usa la configuracion por defecto)
4. El servidor Flask inicia en el puerto 5000
5. Se muestran las IPs disponibles para conexion

### Fase 2: Conexion del Estudiante

1. El estudiante abre `examen.html` en su navegador
2. JavaScript detecta la IP local del estudiante usando WebRTC
3. Se genera una lista de URLs candidatas del servidor (subred local + IPs conocidas)
4. Se intenta `GET /ping` a cada candidata con timeout de 1.5s
5. La primera respuesta exitosa establece la conexion
6. Se muestra el indicador de conexion en verde

### Fase 3: Carga del Examen

1. Se llama a `GET /config_examen`
2. Se recibe la configuracion sin respuestas correctas
3. Se renderiza el formulario con todas las preguntas
4. Si hay tiempo limite > 0, se inicia el temporizador
5. Se inicia el polling a `/estado_examen` cada 3 segundos

### Fase 4: Resolucion del Examen

1. El estudiante escribe su nombre
2. Responde cada pregunta segun su tipo
3. La barra de progreso se actualiza con el scroll
4. Si el profesor edita el examen, aparece un overlay bloqueante
5. Si el tiempo se agota, se auto-envia el examen

### Fase 5: Envio y Calificacion

1. El estudiante presiona "Enviar Examen"
2. Se valida: nombre no vacio + todas las preguntas respondidas
3. Se envian las respuestas via `POST /guardar`
4. El servidor califica automaticamente (solo preguntas no abiertas)
5. Se guarda el resultado en `respuestas/examen_{nombre}_{timestamp}.json`
6. Se retorna la calificacion al cliente
7. El cliente muestra el resultado con color (verde >= 8, naranja >= 6, rojo < 6)
8. Se solicitan las respuestas correctas y se muestran al estudiante

### Fase 6: Consulta de Resultados

1. El profesor accede a `/ver` para ver resultados en tiempo real (auto-refresco 15s)
2. O accede a `/admin` para el dashboard completo
3. Puede descargar los resultados en Excel via `/admin/descargar`

---

## 8. Interfaz del Estudiante (examen.html)

### Estructura Visual

```
+─────────────────────────────────────────────+
|  [Logo Tecmilenio]  Titulo del Examen       |  <- Header
|  Materia: Pensamiento Critico               |
+─────────────────────────────────────────────+
|  [========= Barra de Tiempo 45:30 ========] |  <- Timer (si aplica)
+─────────────────────────────────────────────+
|  [===========] Progreso de scroll           |  <- Progress bar
+─────────────────────────────────────────────+
|  Conectado al servidor                      |  <- Status
+─────────────────────────────────────────────+
|                                             |
|  Nombre del estudiante: [______________]    |
|                                             |
|  +─────────────────────────────────────+    |
|  | 1. Pregunta de opcion multiple      |    |
|  |    Tipo: Opcion Multiple | 1 punto  |    |
|  |    [imagen opcional]                |    |
|  |    ( ) Opcion A                     |    |
|  |    (x) Opcion B                     |    |
|  |    ( ) Opcion C                     |    |
|  |    ( ) Opcion D                     |    |
|  +─────────────────────────────────────+    |
|                                             |
|  +─────────────────────────────────────+    |
|  | 2. Pregunta de seleccion multiple   |    |
|  |    Tipo: Seleccion Multiple | 2 pts |    |
|  |    [x] Opcion A                     |    |
|  |    [ ] Opcion B                     |    |
|  |    [x] Opcion C                     |    |
|  +─────────────────────────────────────+    |
|                                             |
|  +─────────────────────────────────────+    |
|  | 3. Pregunta abierta                 |    |
|  |    Tipo: Respuesta Abierta | 3 pts  |    |
|  |    [                               ]|    |
|  |    [   Textarea para respuesta     ]|    |
|  |    [                               ]|    |
|  +─────────────────────────────────────+    |
|                                             |
|         [ Enviar Examen ]                   |
|                                             |
+─────────────────────────────────────────────+
```

### Tipos de Pregunta Soportados

| Tipo | Elemento HTML | Seleccion | Uso |
|------|---------------|-----------|-----|
| `opcion_multiple` | Radio buttons | Una sola respuesta | Preguntas con una unica respuesta correcta |
| `seleccion_multiple` | Checkboxes | Multiples respuestas | Preguntas con varias respuestas correctas |
| `abierta` | Textarea | Texto libre | Preguntas de desarrollo (no calificadas automaticamente) |

### Temporizador

- Se activa cuando `tiempo_minutos > 0`
- Formato: `MM:SS`
- Cambio de color progresivo:
  - **Blanco:** Tiempo normal
  - **Amarillo:** Menos de 5 minutos restantes
  - **Rojo:** Menos de 1 minuto restante
- Al llegar a `00:00`: se auto-envia el examen automaticamente

### Presentacion de Resultados

Despues del envio, se muestra una tarjeta de resultado:

- **Calificacion >= 8.0:** Fondo verde
- **Calificacion >= 6.0:** Fondo naranja
- **Calificacion < 6.0:** Fondo rojo
- Se indican las respuestas correctas (fondo verde) y las erroneas del alumno (fondo rojo) para preguntas de opcion multiple y seleccion multiple
- Las preguntas abiertas no se marcan como correctas/incorrectas

### Proteccion Contra Cierre Accidental

El navegador muestra un dialogo de confirmacion (`beforeunload`) si el estudiante intenta cerrar la pagina despues de haber respondido al menos una pregunta.

---

## 9. Panel de Administracion (Profesor)

### Acceso

- **URL:** `http://<ip-servidor>:5000/admin/login`
- **Contrasena:** `admin123`

### Dashboard (`/admin`)

Muestra tarjetas con:
- Numero total de preguntas del examen actual
- Numero de respuestas recibidas
- Boton para acceder al editor de examen
- Boton para ver resultados
- Boton para descargar Excel

### Editor de Examen (`/admin/examen`)

Interfaz visual completa para crear y editar examenes:

**Configuracion General:**
- Titulo del examen
- Materia
- Tiempo limite en minutos (0 = sin limite)

**Gestion de Preguntas:**
- Agregar pregunta de opcion multiple, seleccion multiple o respuesta abierta
- Editar el texto de cada pregunta
- Subir/eliminar imagen por pregunta
- Reordenar preguntas con flechas arriba/abajo
- Eliminar preguntas individuales
- Configurar puntos por pregunta

**Gestion de Opciones (para preguntas de opcion/seleccion multiple):**
- Agregar/eliminar opciones de respuesta
- Editar texto de cada opcion
- Marcar opcion(es) correcta(s) con checkbox

**Sincronizacion:**
- Al abrir el editor, se notifica al servidor (`editando: true`)
- Los estudiantes conectados ven un overlay bloqueante
- Al guardar, se incrementa la version y los estudiantes recargan automaticamente

### Visualizacion de Resultados (`/ver`)

Pagina publica (no requiere autenticacion) con:
- Auto-refresco cada 15 segundos
- Estadisticas: total estudiantes, promedio, aprobados/reprobados, porcentaje aprobacion
- Tabla con columnas: Nombre, Calificacion, Correctas/Total, Estado, Fecha/Hora
- Calificaciones coloreadas segun rango
- Boton de descarga Excel

---

## 10. Modelo de Datos

### Configuracion del Examen (`config_examen.json`)

```json
{
  "titulo": "string - Titulo del examen",
  "materia": "string - Nombre de la materia",
  "tiempo_minutos": "number - Minutos (0 = sin limite)",
  "preguntas": [
    {
      "id": "number - Identificador unico",
      "tipo": "string - 'opcion_multiple' | 'seleccion_multiple' | 'abierta'",
      "texto": "string - Texto de la pregunta",
      "imagen": "string | null - Nombre de archivo o base64",
      "puntos": "number - Puntos que vale la pregunta",
      "opciones": [
        {
          "id": "string - Identificador ('a', 'b', 'c', ...)",
          "texto": "string - Texto de la opcion"
        }
      ],
      "respuesta_correcta": "string | array - 'b' o ['a', 'c']"
    }
  ]
}
```

### Respuesta del Estudiante (`respuestas/examen_{nombre}_{timestamp}.json`)

```json
{
  "nombre": "string - Nombre del estudiante",
  "timestamp": "string - Fecha/hora de envio",
  "respuestas": {
    "pregunta_1": "string | array - Respuesta(s) del alumno",
    "pregunta_2": ["a", "c"],
    "pregunta_3": "Texto de respuesta abierta"
  },
  "calificacion": "number - Calificacion en escala 0-10",
  "correctas": "number - Cantidad de respuestas correctas",
  "total_puntos": "number - Total de puntos posibles (sin preguntas abiertas)"
}
```

### Estado de Edicion (En memoria)

```python
_estado_edicion = {
    "editando": False,    # bool - Si el profesor esta editando
    "version": 0          # int  - Numero de version del examen
}
```

> Este estado se maneja con un `threading.Lock` para seguridad entre hilos.

---

## 11. Sistema de Calificacion

### Algoritmo (`calcular_calificacion`)

```
ENTRADA: respuestas del alumno + configuracion del examen

PARA cada pregunta en el examen:
    SI tipo == "abierta":
        SALTAR (no se califica automaticamente)

    SI tipo == "seleccion_multiple":
        Convertir respuesta del alumno a conjunto (set)
        Convertir respuesta correcta a conjunto (set)
        SI conjuntos son iguales:
            puntos_obtenidos += puntos de la pregunta
            correctas += 1

    SI tipo == "opcion_multiple":
        SI respuesta_alumno.lower() == respuesta_correcta.lower():
            puntos_obtenidos += puntos de la pregunta
            correctas += 1

calificacion = (puntos_obtenidos / puntos_totales) * 10

SALIDA: {calificacion, correctas, total_puntos}
```

### Escala de Calificacion

| Rango | Color | Estado |
|-------|-------|--------|
| 8.0 - 10.0 | Verde | Aprobado (excelente) |
| 6.0 - 7.9 | Naranja | Aprobado |
| 0.0 - 5.9 | Rojo | Reprobado |

### Notas Importantes

- Las preguntas abiertas **no se califican automaticamente** y no cuentan para el total de puntos
- Para `seleccion_multiple`, el alumno debe marcar **exactamente** las mismas opciones que la respuesta correcta (ni mas, ni menos)
- La calificacion es sobre una escala de **0 a 10**

---

## 12. Descubrimiento Automatico de Servidor

El sistema implementa un mecanismo para que los estudiantes no necesiten conocer la IP del servidor.

### Proceso

1. **Deteccion de IP Local (WebRTC):**
   ```
   Se crea un RTCPeerConnection con servidor STUN
   Se genera una oferta SDP
   Se extraen candidatos ICE para obtener la IP local
   ```

2. **Generacion de Candidatos:**
   - Se toma la subred de la IP detectada (ej: `192.168.1.X`)
   - Se generan URLs para todas las IPs de la subred (1-255)
   - Se agregan IPs hardcodeadas de laboratorios conocidos:
     - `10.73.120.233`, `10.74.178.27`
     - Rango `192.168.x.x`
     - `127.0.0.1` (localhost)
   - Puerto fijo: `5000`

3. **Escaneo Paralelo:**
   - Se intenta `GET /ping` a cada candidata
   - Timeout de 1.5 segundos por intento
   - La primera respuesta exitosa establece la conexion
   - Se detiene el escaneo al encontrar el servidor

4. **Fallback:**
   - Si no se encuentra servidor, se muestra un mensaje de error
   - Se sugiere contactar al profesor

---

## 13. Sincronizacion de Estado en Tiempo Real

### Mecanismo de Polling

El cliente consulta `/estado_examen` cada 3 segundos para detectar cambios:

```javascript
// Cada 3 segundos:
GET /estado_examen -> { editando: bool, version: number }
```

### Escenarios de Sincronizacion

| Evento | Accion del Servidor | Accion del Cliente |
|--------|--------------------|--------------------|
| Profesor abre editor | `editando = true` | Muestra overlay bloqueante |
| Profesor cierra editor | `editando = false` | Oculta overlay |
| Profesor guarda examen | `version++`, `editando = false` | Detecta cambio de version, recarga pagina |

### Overlay de Edicion

Cuando el profesor esta editando, los estudiantes ven un overlay con:
- Fondo semitransparente que bloquea toda interaccion
- Icono de edicion animado
- Mensaje: "El profesor esta editando el examen"
- Submensaje: "Espera un momento, la pagina se actualizara automaticamente"

---

## 14. Exportacion de Resultados a Excel

### Ruta: `GET /admin/descargar`

Genera un archivo `.xlsx` utilizando la libreria `openpyxl`.

### Estructura del Excel

| Columna | Contenido |
|---------|-----------|
| A | Nombre del estudiante |
| B | Calificacion (0-10) |
| C | Correctas / Total |
| D | Estado (Aprobado/Reprobado) |
| E | Fecha y Hora |

### Formato Visual

- **Encabezado:** Fondo verde (#00A859), texto blanco, negrita
- **Filas calificacion >= 8:** Fondo verde claro (#E8F5E9)
- **Filas calificacion >= 6:** Fondo naranja claro (#FFF3E0)
- **Filas calificacion < 6:** Fondo rojo claro (#FFEBEE)
- Bordes delgados en todas las celdas
- Texto centrado
- Anchos de columna optimizados

### Nombre del Archivo

```
resultados_examen_YYYYMMDD_HHMM.xlsx
```

> Si `openpyxl` no esta instalado, el servidor muestra una pagina HTML con instrucciones para instalarlo (`pip install openpyxl`).

---

## 15. Componentes de Interfaz de Usuario

### Estudiante (examen.html)

| Componente | Clase CSS | Funcion |
|------------|-----------|---------|
| Header | `.header` | Logo Tecmilenio, titulo y materia del examen |
| Barra de tiempo | `.timer-bar`, `.timer-display` | Cuenta regresiva con cambio de color |
| Barra de progreso | `.progress-bar`, `.progress-fill` | Indica progreso de scroll en la pagina |
| Estado de conexion | `.status-conexion` | Muestra si esta conectado al servidor |
| Contenedor de alertas | `.alert` | Mensajes de validacion y errores |
| Tarjeta de resultado | `.resultado-card` | Calificacion final con color |
| Input de nombre | `.info-section` | Campo para nombre del estudiante |
| Tarjeta de pregunta | `.question` | Contenedor de cada pregunta |
| Header de pregunta | `.question-header`, `.q-num` | Numero, tipo y puntos |
| Texto de pregunta | `.q-texto` | Contenido de la pregunta |
| Imagen de pregunta | `.q-imagen` | Imagen opcional |
| Opcion de respuesta | `.option` | Radio button o checkbox |
| Textarea | `.resp-abierta` | Respuesta abierta |
| Boton de envio | `.submit-btn` | Envia el examen |
| Overlay de edicion | `#overlayEditando` | Bloquea UI durante edicion |

### Esquema de Colores

| Color | Hex | Uso |
|-------|-----|-----|
| Verde primario | `#00A859` | Headers, botones, acentos |
| Verde oscuro | `#007A3D` | Hover, fondos oscuros |
| Verde claro | `#E8F5E9` | Fondo calificacion alta |
| Naranja | `#FF9800`, `#FFF3E0` | Calificacion media |
| Rojo | `#F44336`, `#FFEBEE` | Calificacion baja |
| Gris claro | `#F5F5F5` | Fondo de pagina |
| Gris medio | `#E0E0E0` | Bordes |

---

## 16. Seguridad

### Mecanismos Implementados

1. **Ocultacion de Respuestas:** El endpoint `/config_examen` elimina el campo `respuesta_correcta` antes de enviarlo al cliente, evitando que el alumno vea las respuestas en la inspeccion de red.

2. **Autenticacion de Admin:** Las rutas `/admin/*` estan protegidas con un decorador `admin_required` que verifica la sesion de Flask.

3. **CORS con Credenciales:** Se habilita `supports_credentials=True` para manejar cookies de sesion en solicitudes cross-origin.

4. **Thread Lock para Estado:** El estado de edicion usa `threading.Lock` para prevenir condiciones de carrera.

5. **Proteccion contra cierre:** `beforeunload` en el navegador previene cierre accidental.

### Vulnerabilidades Conocidas

| Vulnerabilidad | Severidad | Descripcion |
|---------------|-----------|-------------|
| Contrasena hardcodeada | CRITICA | `admin123` en codigo fuente |
| Secret key predecible | ALTA | `tecmilenio_examenes_2026` permite forjar sesiones |
| Sin HTTPS | ALTA | Credenciales y datos viajan en texto plano |
| Sin limite de intentos | MEDIA | No hay rate limiting ni CAPTCHA |
| Sin autenticacion de alumnos | MEDIA | Cualquiera con el enlace puede tomar el examen |
| Envios multiples | MEDIA | Un alumno puede enviar el examen multiples veces |
| Sin sanitizacion de entrada | MEDIA | Nombres de estudiante no se sanitizan |
| Path traversal potencial | BAJA | Endpoint `/imagen/<nombre>` podria ser vulnerable |

> **Nota:** Este sistema esta disenado para uso en entornos de aula controlados, no para produccion en internet abierto.

---

## 17. Patrones de Comunicacion de Red

### Resumen de Todas las Peticiones HTTP

```
ESTUDIANTE -> SERVIDOR:

  [Descubrimiento]
  GET  /ping                    (timeout: 1500ms, multiples intentos)

  [Carga]
  GET  /config_examen           (una vez al conectar)

  [Polling]
  GET  /estado_examen           (cada 3000ms, timeout: 2000ms)

  [Envio]
  POST /guardar                 (una vez, timeout: 8000ms)
  GET  /respuestas_correctas   (una vez, despues del envio)

  [Recursos]
  GET  /imagen/<nombre>         (por cada pregunta con imagen)

PROFESOR -> SERVIDOR:

  [Autenticacion]
  POST /admin/login             (una vez)
  GET  /admin/logout            (una vez)

  [Administracion]
  GET  /admin                   (dashboard)
  GET  /admin/examen            (editor)
  POST /admin/set_editando      (al abrir/cerrar editor)
  POST /admin/guardar_config    (al guardar examen)
  GET  /admin/descargar         (descarga Excel)

  [Resultados]
  GET  /ver                     (auto-refresco cada 15s)
```

---

## 18. Limitaciones Conocidas

| Limitacion | Descripcion | Impacto |
|------------|-------------|---------|
| Sin base de datos | Almacenamiento basado en archivos JSON | No escala para gran cantidad de alumnos simultaneos |
| Servidor de desarrollo | Usa el servidor WSGI integrado de Flask | No apto para produccion de alto trafico |
| Sin HTTPS | Comunicacion sin cifrar | Datos visibles en la red |
| Sin autenticacion de alumnos | Solo se pide nombre, sin verificacion | Un alumno podria usar otro nombre |
| Calificacion parcial | Preguntas abiertas no se califican | El profesor debe revisarlas manualmente |
| IP hardcodeadas | Las IPs de laboratorios estan fijas en el codigo | Requiere modificacion si cambia la red |
| Dependencia de WebRTC | Deteccion de IP puede fallar en algunos navegadores | Algunos entornos bloquean WebRTC |
| Sin persistencia de sesion | Las sesiones se pierden al reiniciar el servidor | El profesor debe volver a autenticarse |
| Un solo examen a la vez | Solo se puede tener un examen activo | No soporta multiples examenes simultaneos |
| Sin respaldo automatico | No hay backups de respuestas ni configuracion | Riesgo de perdida de datos |

---

## Licencia

Proyecto academico de la Universidad Tecmilenio.

---

*Documentacion generada para el proyecto Sistema de Examenes PXE.*
