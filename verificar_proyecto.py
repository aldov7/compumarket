#!/usr/bin/env python3
"""
Verifica el proyecto Campus Market y prepara la entrega.

USO (desde la carpeta RAIZ del proyecto, donde esta settings.gradle.kts):
    python verificar_proyecto.py                    -> solo revisa y muestra que falta
    python verificar_proyecto.py --limpiar          -> ademas borra archivos .bak y carpetas de respaldo
    python verificar_proyecto.py --zip Apellido     -> ademas crea Apellido_T1_proyecto.zip (limpio)
                                                       en la carpeta superior al proyecto

Resultados:
    [OK]     correcto
    [AVISO]  conviene revisarlo (no rompe la app)
    [FALTA]  hay que corregirlo
"""
import argparse
import os
import re
import shutil
import sys
import zipfile

parser = argparse.ArgumentParser()
parser.add_argument("--limpiar", action="store_true", help="borra .bak y carpetas de respaldo")
parser.add_argument("--zip", metavar="APELLIDO", help="crea el ZIP limpio del proyecto")
args = parser.parse_args()

RAIZ = os.getcwd()
if not (os.path.isdir(os.path.join(RAIZ, "app")) and
        any(os.path.exists(os.path.join(RAIZ, n)) for n in ("settings.gradle.kts", "settings.gradle"))):
    print("ERROR: ejecuta este script en la carpeta raiz del proyecto (donde esta settings.gradle.kts).")
    sys.exit(1)


def leer(*partes):
    ruta = os.path.join(RAIZ, *partes)
    if not os.path.exists(ruta):
        return None
    with open(ruta, encoding="utf-8", errors="ignore") as f:
        return f.read()


def bloque(texto, nombre):
    """Devuelve el contenido del primer bloque 'nombre { ... }'."""
    m = re.search(r"\b" + nombre + r"\s*\{", texto)
    if not m:
        return None
    i, nivel = m.end(), 1
    while i < len(texto) and nivel:
        nivel += {"{": 1, "}": -1}.get(texto[i], 0)
        i += 1
    return texto[m.end():i - 1]


resultados = {"OK": 0, "AVISO": 0, "FALTA": 0}


def marcar(nivel, texto, solucion=""):
    resultados[nivel] += 1
    print(f"[{nivel}]".ljust(9) + texto)
    if solucion and nivel != "OK":
        print("         -> " + solucion)


def chequear(condicion, texto, solucion="", nivel_si_falla="FALTA"):
    marcar("OK" if condicion else nivel_si_falla, texto, solucion)


def titulo(t):
    print("\n=== " + t + " ===")


# ---------------------------------------------------------------------------
# Datos base
# ---------------------------------------------------------------------------
gradle_app = leer("app", "build.gradle.kts") or leer("app", "build.gradle") or ""
m = re.search(r'namespace\s*=?\s*"([\w.]+)"', gradle_app)
PKG = m.group(1) if m else "com.example.campusmarket"
CODIGO = os.path.join(RAIZ, "app", "src", "main", "java", *PKG.split("."))
print(f"Proyecto: {RAIZ}\nPaquete:  {PKG}")

# ---------------------------------------------------------------------------
titulo("1. Gradle")
raiz_gradle = leer("build.gradle.kts") or ""
plugins_raiz = bloque(raiz_gradle, "plugins") or ""
lineas_raiz = [l.strip() for l in plugins_raiz.splitlines() if l.strip() and not l.strip().startswith("//")]
chequear(bool(lineas_raiz) and all("apply false" in l for l in lineas_raiz),
         "build.gradle.kts (raiz): todos los plugins llevan 'apply false'",
         "En el archivo de la RAIZ cada plugin debe terminar en 'apply false'.")
chequear("android {" not in raiz_gradle and "dependencies {" not in raiz_gradle,
         "build.gradle.kts (raiz): no contiene android { } ni dependencies { }",
         "Borra esos bloques de la raiz; van solo en el build.gradle.kts del modulo app.")

plugins_app = bloque(gradle_app, "plugins") or ""
chequear("apply false" not in plugins_app,
         "build.gradle.kts (app): los plugins NO llevan 'apply false'",
         "En el archivo del modulo app quita 'apply false'.")
chequear("ksp" in plugins_app, "build.gradle.kts (app): plugin KSP aplicado",
         "Agrega alias(libs.plugins.ksp) en plugins { } del modulo app.")
chequear("compose" in plugins_app, "build.gradle.kts (app): plugin del compilador de Compose aplicado",
         "Agrega alias(libs.plugins.kotlin.compose) en plugins { } del modulo app.")
chequear("kotlin.android" not in plugins_app and 'kotlin("android")' not in plugins_app,
         "build.gradle.kts (app): sin plugin kotlin-android (AGP 9 ya trae Kotlin)",
         "Quita el plugin kotlin-android del modulo app.", "AVISO")
chequear(re.search(r"compose\s*=\s*true", gradle_app) is not None,
         "build.gradle.kts (app): buildFeatures { compose = true }",
         "Agrega buildFeatures { compose = true } dentro de android { }.")

dependencias = [
    ("compose-bom", 'implementation(platform("androidx.compose:compose-bom:2025.06.00"))'),
    ("activity-compose", 'implementation("androidx.activity:activity-compose:1.10.1")'),
    ("androidx.compose.material3:material3", 'implementation("androidx.compose.material3:material3")'),
    ("material-icons-extended", 'implementation("androidx.compose.material:material-icons-extended")'),
    ("navigation-compose", 'implementation("androidx.navigation:navigation-compose:2.9.0")'),
    ("lifecycle-viewmodel-compose", 'implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.9.0")'),
    ("lifecycle-runtime-compose", 'implementation("androidx.lifecycle:lifecycle-runtime-compose:2.9.0")'),
    ("room-runtime", 'implementation("androidx.room:room-runtime:2.8.4")'),
    ("room-ktx", 'implementation("androidx.room:room-ktx:2.8.4")'),
    ("room-compiler", 'ksp("androidx.room:room-compiler:2.8.4")'),
]
for clave, linea in dependencias:
    chequear(clave in gradle_app, f"Dependencia {clave}", f"Agrega dentro de dependencies {{ }}:  {linea}")

catalogo = leer("gradle", "libs.versions.toml") or ""
chequear("ksp" in catalogo and "kotlin-compose" in catalogo,
         "libs.versions.toml: define ksp y kotlin-compose",
         "Revisa las secciones [versions] y [plugins] del catalogo.")

# ---------------------------------------------------------------------------
titulo("2. AndroidManifest y recursos")
manifest = leer("app", "src", "main", "AndroidManifest.xml") or ""
chequear("android.permission.CAMERA" in manifest, "Manifest: permiso CAMERA declarado",
         'Agrega <uses-permission android:name="android.permission.CAMERA" /> antes de <application>.')
chequear(".MainActivity" in manifest and "android.intent.category.LAUNCHER" in manifest,
         "Manifest: MainActivity registrada como pantalla de inicio",
         "Registra <activity android:name=\".MainActivity\"> con el intent-filter MAIN/LAUNCHER.")
strings = leer("app", "src", "main", "res", "values", "strings.xml") or ""
nombre_app = re.search(r'name="app_name">([^<]*)<', strings)
chequear(bool(nombre_app) and nombre_app.group(1).strip() == "Campus Market",
         "strings.xml: app_name = 'Campus Market'",
         'Cambia app_name a "Campus Market" (con espacio) para que el nombre coincida en el celular.', "AVISO")

# ---------------------------------------------------------------------------
titulo("3. Archivos Kotlin")
esperados = {
    "MainActivity.kt": PKG,
    "data/Producto.kt": PKG + ".data",
    "data/ProductoDao.kt": PKG + ".data",
    "data/AppDatabase.kt": PKG + ".data",
    "navegacion/AppNavegacion.kt": PKG + ".navegacion",
    "ui/ProductoViewModel.kt": PKG + ".ui",
    "ui/PantallaPrincipal.kt": PKG + ".ui",
    "ui/PantallaFormulario.kt": PKG + ".ui",
    "ui/PantallaDetalle.kt": PKG + ".ui",
    "ui/Componentes.kt": PKG + ".ui",
    "ui/theme/Theme.kt": PKG + ".ui.theme",
}
archivos = {}
for rel, paquete in esperados.items():
    ruta = os.path.join(CODIGO, *rel.split("/"))
    if not os.path.exists(ruta):
        marcar("FALTA", f"No existe {rel}", "Ejecuta los scripts de generacion en orden (ver mas abajo).")
        continue
    texto = open(ruta, encoding="utf-8", errors="ignore").read()
    archivos[rel] = texto
    primera = next((l for l in texto.splitlines() if l.startswith("package ")), "")
    chequear(primera.strip() == "package " + paquete, f"{rel}: package correcto",
             f"La linea package debe ser 'package {paquete}'.")

opcionales = ["ui/PantallaInicio.kt", "ui/PantallaAcerca.kt"]
faltan_pestanas = [o for o in opcionales if not os.path.exists(os.path.join(CODIGO, *o.split("/")))]
chequear(not faltan_pestanas, "Pestañas (Inicio, Acerca de) presentes",
         "Ejecuta agregar_pestanas.py (despues de mejorar_codigo_rubrica.py).", "AVISO")

# ---------------------------------------------------------------------------
titulo("4. Coherencia del codigo con el enunciado y la rubrica")
db = archivos.get("data/AppDatabase.kt", "")
prod = archivos.get("data/Producto.kt", "")
vm = archivos.get("ui/ProductoViewModel.kt", "")
princ = archivos.get("ui/PantallaPrincipal.kt", "")
form = archivos.get("ui/PantallaFormulario.kt", "")
det = archivos.get("ui/PantallaDetalle.kt", "")
main = archivos.get("MainActivity.kt", "")

chequear("@Entity" in prod and "@Dao" in archivos.get("data/ProductoDao.kt", "") and "@Database" in db,
         "Room: Entity + DAO + Database")
n_semillas = len(re.findall(r"\('[^']+',", db)) + len(re.findall(r"insertar\(Producto\(", db))
chequear(n_semillas >= 5, f"Datos iniciales: {n_semillas} productos precargados (minimo 5)",
         "AppDatabase debe insertar al menos 5 productos al crearse.")
chequear("imagenPath" in prod and "version = 2" in db and "Migration" in db,
         "Foto persistente: campo imagenPath + base de datos v2 con migracion",
         "Ejecuta mejorar_codigo_rubrica.py.", "AVISO")
chequear("ListaUiState" in vm and "productoSeleccionado" in vm,
         "ViewModel: estados de lista y de producto seleccionado",
         "Ejecuta mejorar_codigo_rubrica.py.", "AVISO")
chequear("NavigationBar" in princ, "Navegacion por pestañas (barra inferior)",
         "Ejecuta agregar_pestanas.py.", "AVISO")
chequear("CicloVida" in main and "RegistrarCicloDeVida" in princ,
         "Ciclo de vida: logs en la Activity y en las pantallas (etiqueta CicloVida)",
         "Ejecuta mejorar_interfaz.py y mejorar_codigo_rubrica.py.", "AVISO")
chequear("ACTION_SEND" in det, "Intent de compartir en el detalle")
chequear("Manifest.permission.CAMERA" in form and "Abrir ajustes" in form,
         "Permiso de camara: solicitud, explicacion y manejo del rechazo")
chequear("AlertDialog" in det and "vm.eliminar" in det, "Eliminar con confirmacion")
chequear("collectAsStateWithLifecycle" not in (princ + form + det) or "lifecycle-runtime-compose" in gradle_app,
         "collectAsStateWithLifecycle tiene su dependencia",
         'Agrega implementation("androidx.lifecycle:lifecycle-runtime-compose:2.9.0").')

# ---------------------------------------------------------------------------
titulo("5. Limpieza para la entrega")
basura = []
for carpeta, _, nombres in os.walk(os.path.join(RAIZ, "app", "src")):
    basura += [os.path.join(carpeta, n) for n in nombres if n.endswith(".bak")]
respaldos = [os.path.join(RAIZ, d) for d in os.listdir(RAIZ)
             if d.startswith("_respaldo") and os.path.isdir(os.path.join(RAIZ, d))]
extras = [os.path.join(RAIZ, n) for n in ("PEGAR_EN_GRADLE.txt",) if os.path.exists(os.path.join(RAIZ, n))]

chequear(not basura, "Sin archivos .bak dentro de app/src",
         f"Hay {len(basura)} archivo(s) .bak. Usa: python verificar_proyecto.py --limpiar", "AVISO")
chequear(not respaldos and not extras, "Sin carpetas de respaldo ni archivos auxiliares en la raiz",
         "Usa: python verificar_proyecto.py --limpiar", "AVISO")

if args.limpiar:
    for ruta in basura + extras:
        os.remove(ruta)
    for ruta in respaldos:
        shutil.rmtree(ruta, ignore_errors=True)
    print(f"   Limpieza hecha: {len(basura) + len(extras)} archivo(s) y {len(respaldos)} carpeta(s) borrados.")

# ---------------------------------------------------------------------------
if args.zip:
    excluir_carpetas = {".gradle", ".idea", "build", ".git", "captures", ".cxx"}
    excluir_ext = (".bak", ".iml", ".py", ".apk", ".aab")
    excluir_nombres = {"local.properties", "PEGAR_EN_GRADLE.txt", ".DS_Store"}
    destino = os.path.join(os.path.dirname(RAIZ), f"{args.zip}_T1_proyecto.zip")
    cuenta = 0
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        for carpeta, subcarpetas, nombres in os.walk(RAIZ):
            subcarpetas[:] = [d for d in subcarpetas if d not in excluir_carpetas and not d.startswith("_respaldo")]
            for n in nombres:
                if n in excluir_nombres or n.endswith(excluir_ext):
                    continue
                ruta = os.path.join(carpeta, n)
                z.write(ruta, os.path.join(os.path.basename(RAIZ), os.path.relpath(ruta, RAIZ)))
                cuenta += 1
    print(f"\nZIP creado: {destino}\n   {cuenta} archivos, {os.path.getsize(destino) / 1024 / 1024:.1f} MB "
          "(sin build, .gradle, .idea, local.properties ni .bak)")

# ---------------------------------------------------------------------------
titulo("RESUMEN")
print(f"OK: {resultados['OK']}   AVISO: {resultados['AVISO']}   FALTA: {resultados['FALTA']}")
if resultados["FALTA"]:
    print("Corrige los [FALTA] primero y vuelve a ejecutar este script.")
else:
    print("Sin faltantes criticos. Recuerda: ejecutar la app en el emulador y probar todo el flujo.")
print("\nOrden de los scripts de generacion: crear_campusmarket.py -> mejorar_interfaz.py ->"
      " mejorar_codigo_rubrica.py -> agregar_pestanas.py")
sys.exit(1 if resultados["FALTA"] else 0)
