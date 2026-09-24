#!/usr/bin/env python3
"""
Aplica el prototipo completo de Campus Market.

Que agrega o cambia:
  - Menu lateral (Inicio, Productos, Perfil, Configuracion, Ayuda) y barra inferior con 3 pestañas
  - Inicio: buscador con icono de filtro, lista con fotos, chevron y etiqueta de disponibilidad, boton "+" redondo
  - Productos: resumen y catalogo por categorias
  - Perfil: nombre del estudiante guardado con SharedPreferences
  - Configuracion: tema Automatico / Claro / Oscuro guardado con SharedPreferences
  - Ayuda: como usar la app y tecnologias
  - Detalle: menu de tres puntos, "Compartir producto" como fila, Editar y Eliminar
  - Formulario: Tomar foto, Elegir de galeria, Stock junto a Disponible, aviso amarillo si se rechaza el permiso
  - Fotos de ejemplo para los 5 productos (dibujos vectoriales en res/drawable)
  - Base de datos version 3 (migra sin perder datos)

USO (igual que los scripts anteriores):
  1. Copia este archivo a la carpeta RAIZ del proyecto (donde esta settings.gradle.kts).
  2. Ejecuta:   python aplicar_prototipo.py      (en Windows tambien: py aplicar_prototipo.py)
  3. En Android Studio: Sync, Build > Rebuild Project y ejecuta. No hace falta tocar Gradle.

Antes de reemplazar cada archivo, se guarda una copia en la carpeta _respaldo_prototipo/
(si algo falla, copia esos archivos de vuelta a su lugar y todo queda como antes).
"""
import os
import re
import shutil
import sys

RAIZ = os.getcwd()
gradle_path = None
for nombre in ("build.gradle.kts", "build.gradle"):
    ruta = os.path.join(RAIZ, "app", nombre)
    if os.path.exists(ruta):
        gradle_path = ruta
        break
if gradle_path is None:
    print("ERROR: ejecuta este script dentro de la carpeta raiz del proyecto.")
    sys.exit(1)

with open(gradle_path, encoding="utf-8") as f:
    contenido_gradle = f.read()

PKG = "com.example.campusmarket"
m = re.search(r'namespace\s*=?\s*"([\w.]+)"', contenido_gradle)
if m:
    PKG = m.group(1)

RUTA_PKG = os.path.join(RAIZ, "app", "src", "main", "java", *PKG.split("."))
RUTA_RES = os.path.join(RAIZ, "app", "src", "main", "res")
RESPALDO = os.path.join(RAIZ, "_respaldo_prototipo")
print(f"Paquete detectado: {PKG}\n")

ARCHIVOS = {}

# ===========================================================================
# DATA
# ===========================================================================
ARCHIVOS["data/Producto.kt"] = r'''package __PKG__.data

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "productos")
data class Producto(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val nombre: String,
    val descripcion: String,
    val categoria: String,
    val precio: Double,
    val stock: Int,
    val disponible: Boolean,
    // Foto del producto: ruta de un archivo interno, o "res:nombre" para las imagenes de ejemplo
    val imagenPath: String? = null
)
'''

ARCHIVOS["data/ProductoDao.kt"] = r'''package __PKG__.data

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import kotlinx.coroutines.flow.Flow

@Dao
interface ProductoDao {
    // Flow: la interfaz se actualiza sola cada vez que cambia la tabla
    @Query("SELECT * FROM productos ORDER BY nombre")
    fun obtenerTodos(): Flow<List<Producto>>

    @Query("SELECT * FROM productos WHERE id = :id")
    fun obtenerPorId(id: Int): Flow<Producto?>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertar(producto: Producto)

    @Update
    suspend fun actualizar(producto: Producto)

    @Delete
    suspend fun eliminar(producto: Producto)
}
'''

ARCHIVOS["data/Preferencias.kt"] = r'''package __PKG__.data

import android.content.Context

// Preferencias sencillas del usuario guardadas con SharedPreferences
class Preferencias(context: Context) {

    private val prefs = context.applicationContext
        .getSharedPreferences("campus_market_prefs", Context.MODE_PRIVATE)

    fun leerNombre(): String = prefs.getString(CLAVE_NOMBRE, "") ?: ""

    fun guardarNombre(nombre: String) {
        prefs.edit().putString(CLAVE_NOMBRE, nombre).apply()
    }

    fun leerTema(): Int = prefs.getInt(CLAVE_TEMA, TEMA_SISTEMA)

    fun guardarTema(tema: Int) {
        prefs.edit().putInt(CLAVE_TEMA, tema).apply()
    }

    companion object {
        const val TEMA_SISTEMA = 0
        const val TEMA_CLARO = 1
        const val TEMA_OSCURO = 2
        private const val CLAVE_NOMBRE = "nombre_usuario"
        private const val CLAVE_TEMA = "tema"
    }
}
'''

ARCHIVOS["data/AppDatabase.kt"] = r'''package __PKG__.data

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase

@Database(entities = [Producto::class], version = 3, exportSchema = false)
abstract class AppDatabase : RoomDatabase() {
    abstract fun productoDao(): ProductoDao

    companion object {
        @Volatile private var INSTANCE: AppDatabase? = null

        // Productos de ejemplo (nombre, descripcion, categoria, precio, stock, disponible, imagen)
        private val PRODUCTOS_INICIALES = listOf(
            "('Cuaderno A4', 'Libreta de 100 hojas, tamaño A4.', 'Útiles', 12.50, 20, 1, 'res:prod_cuaderno')",
            "('Lapicero azul', 'Lapicero de tinta azul.', 'Útiles', 2.50, 50, 1, 'res:prod_lapicero')",
            "('Botella reutilizable', 'Botella de acero inoxidable, 500 ml.', 'Accesorios', 18.00, 12, 1, 'res:prod_botella')",
            "('Mochila', 'Mochila resistente para laptop.', 'Accesorios', 65.00, 8, 1, 'res:prod_mochila')",
            "('Memoria USB', 'Memoria USB de 64 GB.', 'Tecnología', 25.00, 10, 1, 'res:prod_usb')"
        )

        private val IMAGENES_INICIALES = mapOf(
            "Cuaderno A4" to "prod_cuaderno",
            "Lapicero azul" to "prod_lapicero",
            "Botella reutilizable" to "prod_botella",
            "Mochila" to "prod_mochila",
            "Memoria USB" to "prod_usb"
        )

        // Migracion 1 a 2: agrega la columna de la foto sin perder los datos existentes
        private val MIGRACION_1_2 = object : Migration(1, 2) {
            override fun migrate(db: SupportSQLiteDatabase) {
                db.execSQL("ALTER TABLE productos ADD COLUMN imagenPath TEXT")
            }
        }

        // Migracion 2 a 3: asigna las imagenes de ejemplo a los productos iniciales
        private val MIGRACION_2_3 = object : Migration(2, 3) {
            override fun migrate(db: SupportSQLiteDatabase) {
                IMAGENES_INICIALES.forEach { (nombre, recurso) ->
                    db.execSQL(
                        "UPDATE productos SET imagenPath = 'res:$recurso' WHERE nombre = '$nombre' AND imagenPath IS NULL"
                    )
                }
            }
        }

        fun getDatabase(context: Context): AppDatabase {
            val appContext = context.applicationContext
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: Room.databaseBuilder(appContext, AppDatabase::class.java, "campus_market.db")
                    .addMigrations(MIGRACION_1_2, MIGRACION_2_3)
                    .addCallback(object : RoomDatabase.Callback() {
                        // Se ejecuta solo la primera vez que se crea la base de datos
                        override fun onCreate(db: SupportSQLiteDatabase) {
                            super.onCreate(db)
                            PRODUCTOS_INICIALES.forEach { valores ->
                                db.execSQL(
                                    "INSERT INTO productos (nombre, descripcion, categoria, precio, stock, disponible, imagenPath) VALUES $valores"
                                )
                            }
                        }
                    })
                    .build()
                    .also { INSTANCE = it }
            }
        }
    }
}
'''

# ===========================================================================
# TEMA
# ===========================================================================
ARCHIVOS["ui/theme/Theme.kt"] = r'''package __PKG__.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

// Paleta verde con buen contraste. El color terciario (ambar) se usa en los avisos.
private val EsquemaClaro = lightColorScheme(
    primary = Color(0xFF00695C),
    onPrimary = Color.White,
    primaryContainer = Color(0xFFB2DFDB),
    onPrimaryContainer = Color(0xFF00201C),
    secondary = Color(0xFF4A635F),
    secondaryContainer = Color(0xFFCCE8E3),
    onSecondaryContainer = Color(0xFF05201D),
    tertiary = Color(0xFF8A5A00),
    onTertiary = Color.White,
    tertiaryContainer = Color(0xFFFFE9B0),
    onTertiaryContainer = Color(0xFF3E2A00),
    error = Color(0xFFB3261E),
    onError = Color.White,
    errorContainer = Color(0xFFF9DEDC),
    onErrorContainer = Color(0xFF410E0B),
    background = Color(0xFFF6FBF9),
    surface = Color(0xFFF6FBF9)
)

private val EsquemaOscuro = darkColorScheme(
    primary = Color(0xFF4DB6AC),
    onPrimary = Color(0xFF003731),
    primaryContainer = Color(0xFF005048),
    onPrimaryContainer = Color(0xFFB2DFDB),
    secondary = Color(0xFFB0CCC7),
    secondaryContainer = Color(0xFF334B47),
    onSecondaryContainer = Color(0xFFCCE8E3),
    tertiary = Color(0xFFFFC857),
    onTertiary = Color(0xFF432C00),
    tertiaryContainer = Color(0xFF5F4100),
    onTertiaryContainer = Color(0xFFFFE9B0),
    error = Color(0xFFF2B8B5),
    onError = Color(0xFF601410),
    errorContainer = Color(0xFF8C1D18),
    onErrorContainer = Color(0xFFF9DEDC),
    background = Color(0xFF0F1614),
    surface = Color(0xFF0F1614)
)

@Composable
fun CampusMarketTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    MaterialTheme(
        colorScheme = if (darkTheme) EsquemaOscuro else EsquemaClaro,
        content = content
    )
}
'''

# ===========================================================================
# VIEWMODEL
# ===========================================================================
ARCHIVOS["ui/ProductoViewModel.kt"] = r'''package __PKG__.ui

import android.app.Application
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import __PKG__.data.AppDatabase
import __PKG__.data.Preferencias
import __PKG__.data.Producto
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File

// Estado de la lista: evita mostrar "no hay productos" mientras Room todavia esta cargando
sealed interface ListaUiState {
    data object Cargando : ListaUiState
    data class Datos(val productos: List<Producto>) : ListaUiState
}

@OptIn(ExperimentalCoroutinesApi::class)
class ProductoViewModel(app: Application) : AndroidViewModel(app) {

    private val dao = AppDatabase.getDatabase(app).productoDao()
    private val preferencias = Preferencias(app)

    // ESTADO 1: lista de productos (viene de Room)
    val listaState: StateFlow<ListaUiState> = dao.obtenerTodos()
        .map<List<Producto>, ListaUiState> { ListaUiState.Datos(it) }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), ListaUiState.Cargando)

    // ESTADO 2: producto seleccionado (detalle y edicion)
    private val idSeleccionado = MutableStateFlow<Int?>(null)
    val productoSeleccionado: StateFlow<Producto?> = idSeleccionado
        .flatMapLatest { id -> if (id == null) flowOf<Producto?>(null) else dao.obtenerPorId(id) }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), null)

    fun seleccionar(id: Int?) {
        idSeleccionado.value = id
    }

    // ESTADO 3 y 4: preferencias del usuario (nombre y tema)
    private val _nombreUsuario = MutableStateFlow(preferencias.leerNombre())
    val nombreUsuario: StateFlow<String> = _nombreUsuario.asStateFlow()

    private val _tema = MutableStateFlow(preferencias.leerTema())
    val tema: StateFlow<Int> = _tema.asStateFlow()

    fun guardarNombre(nombre: String) {
        val limpio = nombre.trim()
        preferencias.guardarNombre(limpio)
        _nombreUsuario.value = limpio
    }

    fun cambiarTema(tema: Int) {
        preferencias.guardarTema(tema)
        _tema.value = tema
    }

    // CREATE y UPDATE: si hay una foto nueva se mueve a su carpeta definitiva y se borra la anterior
    fun guardar(producto: Producto, rutaFotoNueva: String? = null) = viewModelScope.launch {
        var ruta = producto.imagenPath
        if (rutaFotoNueva != null) {
            val anterior = ruta
            ruta = withContext(Dispatchers.IO) {
                val definitiva = moverFotoADefinitiva(rutaFotoNueva)
                borrarArchivo(anterior)
                definitiva
            }
        }
        val guardado = producto.copy(imagenPath = ruta)
        if (guardado.id == 0) dao.insertar(guardado) else dao.actualizar(guardado)
    }

    // DELETE: tambien borra el archivo de la foto
    fun eliminar(producto: Producto) = viewModelScope.launch {
        dao.eliminar(producto)
        withContext(Dispatchers.IO) { borrarArchivo(producto.imagenPath) }
    }

    // Fotos temporales: se guardan en la cache mientras el formulario esta abierto
    suspend fun guardarFotoTemporal(bitmap: Bitmap): String = withContext(Dispatchers.IO) {
        escribirTemporal(bitmap)
    }

    suspend fun guardarFotoTemporalDesdeUri(uri: Uri): String? = withContext(Dispatchers.IO) {
        try {
            val resolver = getApplication<Application>().contentResolver
            val limites = BitmapFactory.Options().apply { inJustDecodeBounds = true }
            resolver.openInputStream(uri)?.use { BitmapFactory.decodeStream(it, null, limites) }
            var muestra = 1
            while (limites.outWidth / muestra > 1024 || limites.outHeight / muestra > 1024) {
                muestra *= 2
            }
            val opciones = BitmapFactory.Options().apply { inSampleSize = muestra }
            val bitmap = resolver.openInputStream(uri)?.use { BitmapFactory.decodeStream(it, null, opciones) }
            if (bitmap != null) escribirTemporal(bitmap) else null
        } catch (e: Exception) {
            null
        }
    }

    private fun escribirTemporal(bitmap: Bitmap): String {
        val archivo = File(getApplication<Application>().cacheDir, "foto_tmp_${System.currentTimeMillis()}.jpg")
        archivo.outputStream().use { salida ->
            bitmap.compress(Bitmap.CompressFormat.JPEG, 90, salida)
        }
        return archivo.absolutePath
    }

    private fun moverFotoADefinitiva(rutaTemporal: String): String {
        val carpeta = File(getApplication<Application>().filesDir, "fotos").apply { mkdirs() }
        val destino = File(carpeta, "foto_${System.currentTimeMillis()}.jpg")
        File(rutaTemporal).copyTo(destino, overwrite = true)
        File(rutaTemporal).delete()
        return destino.absolutePath
    }

    // Las imagenes de ejemplo ("res:...") viven en la app y no se borran
    private fun borrarArchivo(ruta: String?) {
        if (ruta != null && !ruta.startsWith(PREFIJO_RECURSO)) {
            File(ruta).delete()
        }
    }
}
'''

# ===========================================================================
# NAVEGACION Y ACTIVITY
# ===========================================================================
ARCHIVOS["navegacion/AppNavegacion.kt"] = r'''package __PKG__.navegacion

import androidx.compose.runtime.Composable
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import __PKG__.ui.PantallaAyuda
import __PKG__.ui.PantallaConfiguracion
import __PKG__.ui.PantallaDetalle
import __PKG__.ui.PantallaFormulario
import __PKG__.ui.PantallaPrincipal
import __PKG__.ui.ProductoViewModel

// Rutas centralizadas: evita errores de escritura en los textos de navegacion
object Rutas {
    const val ARG_ID = "id"
    const val PRINCIPAL = "principal"
    const val FORMULARIO = "formulario/{$ARG_ID}"
    const val DETALLE = "detalle/{$ARG_ID}"
    const val CONFIGURACION = "configuracion"
    const val AYUDA = "ayuda"

    fun formulario(id: Int = 0) = "formulario/$id"   // id = 0 significa "producto nuevo"
    fun detalle(id: Int) = "detalle/$id"
}

@Composable
fun AppNavegacion(vm: ProductoViewModel = viewModel()) {
    val nav = rememberNavController()

    NavHost(navController = nav, startDestination = Rutas.PRINCIPAL) {

        composable(Rutas.PRINCIPAL) {
            PantallaPrincipal(
                vm = vm,
                onAgregar = { nav.navigate(Rutas.formulario()) { launchSingleTop = true } },
                onDetalle = { id -> nav.navigate(Rutas.detalle(id)) { launchSingleTop = true } },
                onConfiguracion = { nav.navigate(Rutas.CONFIGURACION) { launchSingleTop = true } },
                onAyuda = { nav.navigate(Rutas.AYUDA) { launchSingleTop = true } }
            )
        }

        composable(
            route = Rutas.FORMULARIO,
            arguments = listOf(navArgument(Rutas.ARG_ID) { type = NavType.IntType })
        ) { entry ->
            PantallaFormulario(
                vm = vm,
                productoId = entry.arguments?.getInt(Rutas.ARG_ID) ?: 0,
                onVolver = { nav.popBackStack() }
            )
        }

        composable(
            route = Rutas.DETALLE,
            arguments = listOf(navArgument(Rutas.ARG_ID) { type = NavType.IntType })
        ) { entry ->
            PantallaDetalle(
                vm = vm,
                productoId = entry.arguments?.getInt(Rutas.ARG_ID) ?: 0,
                onEditar = { id -> nav.navigate(Rutas.formulario(id)) { launchSingleTop = true } },
                onVolver = { nav.popBackStack() }
            )
        }

        composable(Rutas.CONFIGURACION) {
            PantallaConfiguracion(vm = vm, onVolver = { nav.popBackStack() })
        }

        composable(Rutas.AYUDA) {
            PantallaAyuda(onVolver = { nav.popBackStack() })
        }
    }
}
'''

ARCHIVOS["MainActivity.kt"] = r'''package __PKG__

import android.os.Bundle
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import __PKG__.data.Preferencias
import __PKG__.navegacion.AppNavegacion
import __PKG__.ui.ProductoViewModel
import __PKG__.ui.theme.CampusMarketTheme

class MainActivity : ComponentActivity() {

    private val etiqueta = "CicloVida"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        Log.d(etiqueta, "onCreate (estado guardado: ${savedInstanceState != null})")
        setContent {
            val vm: ProductoViewModel = viewModel()
            // El tema elegido en Configuracion se guarda en SharedPreferences
            val tema by vm.tema.collectAsStateWithLifecycle()
            val oscuro = when (tema) {
                Preferencias.TEMA_CLARO -> false
                Preferencias.TEMA_OSCURO -> true
                else -> isSystemInDarkTheme()
            }
            CampusMarketTheme(darkTheme = oscuro) {
                Surface(modifier = Modifier.fillMaxSize()) { AppNavegacion(vm) }
            }
        }
    }

    override fun onStart() { super.onStart(); Log.d(etiqueta, "onStart: la pantalla es visible") }
    override fun onResume() { super.onResume(); Log.d(etiqueta, "onResume: la app esta en primer plano") }
    override fun onPause() { super.onPause(); Log.d(etiqueta, "onPause: la app pierde el foco") }
    override fun onStop() { super.onStop(); Log.d(etiqueta, "onStop: la app ya no es visible") }
    override fun onDestroy() {
        super.onDestroy()
        Log.d(etiqueta, "onDestroy (por rotacion: $isChangingConfigurations)")
    }
}
'''

# ===========================================================================
# COMPONENTES COMPARTIDOS
# ===========================================================================
ARCHIVOS["ui/Componentes.kt"] = r'''package __PKG__.ui

import android.graphics.BitmapFactory
import android.util.Log
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Cancel
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Computer
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.Inventory2
import androidx.compose.material.icons.filled.Restaurant
import androidx.compose.material.icons.filled.ShoppingBag
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.produceState
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.util.Locale

// Las imagenes de ejemplo se guardan en la base de datos como "res:nombre_del_drawable"
const val PREFIJO_RECURSO = "res:"

// Categorias disponibles en el formulario y en los filtros
val CATEGORIAS = listOf("Útiles", "Accesorios", "Tecnología", "Alimentos")

// Icono representativo segun la categoria
fun iconoCategoria(categoria: String): ImageVector = when (categoria) {
    "Útiles" -> Icons.Default.Edit
    "Accesorios" -> Icons.Default.ShoppingBag
    "Tecnología" -> Icons.Default.Computer
    "Alimentos" -> Icons.Default.Restaurant
    else -> Icons.Default.Inventory2
}

fun formatoPrecio(precio: Double): String = "S/ " + String.format(Locale.US, "%.2f", precio)

// El estado se comunica con icono + texto + color (no depende solo del color)
@Composable
fun EtiquetaDisponibilidad(disponible: Boolean) {
    val fondo = if (disponible) MaterialTheme.colorScheme.primaryContainer
    else MaterialTheme.colorScheme.errorContainer
    val texto = if (disponible) MaterialTheme.colorScheme.onPrimaryContainer
    else MaterialTheme.colorScheme.onErrorContainer

    Surface(color = fondo, contentColor = texto, shape = RoundedCornerShape(50)) {
        Row(
            Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.Center
        ) {
            Icon(
                if (disponible) Icons.Default.CheckCircle else Icons.Default.Cancel,
                contentDescription = null,
                modifier = Modifier.size(16.dp)
            )
            Spacer(Modifier.width(4.dp))
            Text(
                if (disponible) "Disponible" else "No disponible",
                style = MaterialTheme.typography.labelMedium
            )
        }
    }
}

// Etiqueta con la categoria del producto (icono + texto)
@Composable
fun EtiquetaCategoria(categoria: String) {
    Surface(
        color = MaterialTheme.colorScheme.secondaryContainer,
        contentColor = MaterialTheme.colorScheme.onSecondaryContainer,
        shape = RoundedCornerShape(50)
    ) {
        Row(
            Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(iconoCategoria(categoria), contentDescription = null, modifier = Modifier.size(16.dp))
            Spacer(Modifier.width(4.dp))
            Text(categoria, style = MaterialTheme.typography.labelMedium)
        }
    }
}

// Muestra la imagen del producto: un recurso de ejemplo ("res:..."), una foto guardada
// o, si no hay imagen, un icono. La foto se decodifica fuera del hilo principal.
@Composable
fun ImagenProducto(
    path: String?,
    iconoVacio: ImageVector,
    descripcion: String,
    modifier: Modifier = Modifier,
    shape: Shape = RoundedCornerShape(12.dp),
    tamanoIcono: Dp = 28.dp
) {
    val context = LocalContext.current
    val idRecurso = remember(path) {
        if (path != null && path.startsWith(PREFIJO_RECURSO)) {
            context.resources.getIdentifier(path.removePrefix(PREFIJO_RECURSO), "drawable", context.packageName)
        } else {
            0
        }
    }
    val bitmap by produceState<ImageBitmap?>(initialValue = null, key1 = path) {
        value = if (path == null || path.startsWith(PREFIJO_RECURSO)) {
            null
        } else {
            withContext(Dispatchers.IO) { BitmapFactory.decodeFile(path)?.asImageBitmap() }
        }
    }
    val foto = bitmap
    val hayImagen = idRecurso != 0 || foto != null

    Surface(
        shape = shape,
        color = if (hayImagen) Color.White else MaterialTheme.colorScheme.primaryContainer,
        modifier = modifier
    ) {
        when {
            idRecurso != 0 -> Image(
                painter = painterResource(idRecurso),
                contentDescription = descripcion,
                contentScale = ContentScale.Fit,
                modifier = Modifier.fillMaxSize().padding(4.dp)
            )
            foto != null -> Image(
                bitmap = foto,
                contentDescription = descripcion,
                contentScale = ContentScale.Crop,
                modifier = Modifier.fillMaxSize()
            )
            else -> Box(contentAlignment = Alignment.Center) {
                Icon(
                    iconoVacio,
                    contentDescription = descripcion,
                    modifier = Modifier.size(tamanoIcono),
                    tint = MaterialTheme.colorScheme.onPrimaryContainer
                )
            }
        }
    }
}

@Composable
fun IndicadorCarga(modifier: Modifier = Modifier) {
    Box(modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        CircularProgressIndicator(modifier = Modifier.semantics { contentDescription = "Cargando" })
    }
}

// Mensaje central reutilizable (lista vacia, sin resultados)
@Composable
fun EstadoMensaje(
    titulo: String,
    detalle: String,
    modifier: Modifier = Modifier,
    accion: @Composable () -> Unit
) {
    Column(
        modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Icon(
            Icons.Default.Inventory2, contentDescription = null,
            modifier = Modifier.size(96.dp),
            tint = MaterialTheme.colorScheme.primary
        )
        Spacer(Modifier.height(12.dp))
        Text(titulo, style = MaterialTheme.typography.titleMedium, textAlign = TextAlign.Center)
        Text(detalle, style = MaterialTheme.typography.bodyMedium, textAlign = TextAlign.Center)
        Spacer(Modifier.height(16.dp))
        accion()
    }
}

// Registra en Logcat (etiqueta "CicloVida") los eventos del ciclo de vida de cada pantalla.
@Composable
fun RegistrarCicloDeVida(pantalla: String) {
    val propietario = LocalLifecycleOwner.current
    DisposableEffect(propietario) {
        val observador = LifecycleEventObserver { _, evento ->
            Log.d("CicloVida", "$pantalla -> ${evento.name}")
        }
        propietario.lifecycle.addObserver(observador)
        onDispose { propietario.lifecycle.removeObserver(observador) }
    }
}
'''

# ===========================================================================
# PANTALLA PRINCIPAL: menu lateral + pestañas + lista
# ===========================================================================
ARCHIVOS["ui/PantallaPrincipal.kt"] = r'''package __PKG__.ui

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.KeyboardArrowRight
import androidx.compose.material.icons.filled.AccountCircle
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.CheckBox
import androidx.compose.material.icons.filled.CheckBoxOutlineBlank
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.FilterList
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Inventory2
import androidx.compose.material.icons.filled.Menu
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Store
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.DrawerValue
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalDrawerSheet
import androidx.compose.material3.ModalNavigationDrawer
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationDrawerItem
import androidx.compose.material3.NavigationDrawerItemDefaults
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.material3.rememberDrawerState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import __PKG__.data.Producto
import kotlinx.coroutines.launch

// Pestañas de la barra inferior (tambien aparecen en el menu lateral)
private enum class Pestana(val etiqueta: String, val icono: ImageVector) {
    INICIO("Inicio", Icons.Default.Home),
    PRODUCTOS("Productos", Icons.Default.Inventory2),
    PERFIL("Perfil", Icons.Default.Person)
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PantallaPrincipal(
    vm: ProductoViewModel,
    onAgregar: () -> Unit,
    onDetalle: (Int) -> Unit,
    onConfiguracion: () -> Unit,
    onAyuda: () -> Unit
) {
    RegistrarCicloDeVida("PantallaPrincipal")

    // collectAsStateWithLifecycle: deja de escuchar la base de datos cuando la app no esta visible
    val estado by vm.listaState.collectAsStateWithLifecycle()

    // Estado: pestaña activa (se guarda el indice para sobrevivir a la rotacion)
    var indicePestana by rememberSaveable { mutableIntStateOf(0) }
    val pestana = Pestana.entries[indicePestana]

    // Estados elevados: la busqueda y los filtros no se pierden al cambiar de pestaña
    var busqueda by rememberSaveable { mutableStateOf("") }
    var categoriaSel by rememberSaveable { mutableStateOf<String?>(null) }
    var soloDisponibles by rememberSaveable { mutableStateOf(false) }

    // Estado: menu lateral
    val drawerState = rememberDrawerState(DrawerValue.Closed)
    val alcance = rememberCoroutineScope()

    // El boton "atras" cierra el menu; desde otra pestaña vuelve a Inicio
    BackHandler(enabled = pestana != Pestana.INICIO) { indicePestana = 0 }
    BackHandler(enabled = drawerState.isOpen) { alcance.launch { drawerState.close() } }

    ModalNavigationDrawer(
        drawerState = drawerState,
        drawerContent = {
            ModalDrawerSheet {
                Row(
                    Modifier
                        .fillMaxWidth()
                        .background(MaterialTheme.colorScheme.primary)
                        .padding(24.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        Icons.Default.Store,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.onPrimary,
                        modifier = Modifier.size(32.dp)
                    )
                    Spacer(Modifier.width(12.dp))
                    Text(
                        "Campus Market",
                        style = MaterialTheme.typography.titleLarge,
                        color = MaterialTheme.colorScheme.onPrimary,
                        fontWeight = FontWeight.Bold
                    )
                }
                Spacer(Modifier.height(8.dp))
                Pestana.entries.forEachIndexed { i, p ->
                    NavigationDrawerItem(
                        label = { Text(p.etiqueta) },
                        icon = { Icon(p.icono, contentDescription = null) },
                        selected = i == indicePestana,
                        onClick = {
                            indicePestana = i
                            alcance.launch { drawerState.close() }
                        },
                        modifier = Modifier.padding(NavigationDrawerItemDefaults.ItemPadding)
                    )
                }
                HorizontalDivider(Modifier.padding(horizontal = 16.dp, vertical = 8.dp))
                NavigationDrawerItem(
                    label = { Text("Configuración") },
                    icon = { Icon(Icons.Default.Settings, contentDescription = null) },
                    selected = false,
                    onClick = {
                        alcance.launch { drawerState.close() }
                        onConfiguracion()
                    },
                    modifier = Modifier.padding(NavigationDrawerItemDefaults.ItemPadding)
                )
                NavigationDrawerItem(
                    label = { Text("Ayuda") },
                    icon = { Icon(Icons.Default.Info, contentDescription = null) },
                    selected = false,
                    onClick = {
                        alcance.launch { drawerState.close() }
                        onAyuda()
                    },
                    modifier = Modifier.padding(NavigationDrawerItemDefaults.ItemPadding)
                )
            }
        }
    ) {
        Scaffold(
            topBar = {
                TopAppBar(
                    title = { Text("Campus Market", fontWeight = FontWeight.Bold) },
                    navigationIcon = {
                        IconButton(onClick = { alcance.launch { drawerState.open() } }) {
                            Icon(Icons.Default.Menu, contentDescription = "Abrir menú")
                        }
                    },
                    actions = {
                        IconButton(onClick = { indicePestana = Pestana.PERFIL.ordinal }) {
                            Icon(Icons.Default.AccountCircle, contentDescription = "Ir al perfil")
                        }
                    },
                    colors = TopAppBarDefaults.topAppBarColors(
                        containerColor = MaterialTheme.colorScheme.primary,
                        titleContentColor = MaterialTheme.colorScheme.onPrimary,
                        navigationIconContentColor = MaterialTheme.colorScheme.onPrimary,
                        actionIconContentColor = MaterialTheme.colorScheme.onPrimary
                    )
                )
            },
            bottomBar = {
                NavigationBar {
                    Pestana.entries.forEachIndexed { i, p ->
                        NavigationBarItem(
                            selected = i == indicePestana,
                            onClick = { indicePestana = i },
                            icon = { Icon(p.icono, contentDescription = null) },
                            label = { Text(p.etiqueta) }
                        )
                    }
                }
            },
            floatingActionButton = {
                if (pestana != Pestana.PERFIL) {
                    FloatingActionButton(
                        onClick = onAgregar,
                        containerColor = MaterialTheme.colorScheme.primary,
                        contentColor = MaterialTheme.colorScheme.onPrimary
                    ) {
                        Icon(Icons.Default.Add, contentDescription = "Agregar producto")
                    }
                }
            }
        ) { padding ->
            val contenido = Modifier.padding(padding)
            val e = estado
            when {
                pestana == Pestana.PERFIL -> PestanaPerfil(
                    vm = vm,
                    totalProductos = (e as? ListaUiState.Datos)?.productos?.size ?: 0,
                    modifier = contenido
                )
                e is ListaUiState.Cargando -> IndicadorCarga(contenido)
                e is ListaUiState.Datos -> {
                    if (pestana == Pestana.INICIO) {
                        ContenidoLista(
                            productos = e.productos,
                            busqueda = busqueda,
                            onBusquedaChange = { busqueda = it },
                            categoriaSel = categoriaSel,
                            onCategoriaChange = { categoriaSel = it },
                            soloDisponibles = soloDisponibles,
                            onSoloDisponiblesChange = { soloDisponibles = it },
                            onAgregar = onAgregar,
                            onDetalle = onDetalle,
                            modifier = contenido
                        )
                    } else {
                        PestanaProductos(
                            productos = e.productos,
                            onAgregar = onAgregar,
                            onDetalle = onDetalle,
                            onCategoria = { categoria ->
                                // Al elegir una categoria se muestra la lista filtrada en Inicio
                                categoriaSel = categoria
                                indicePestana = Pestana.INICIO.ordinal
                            },
                            modifier = contenido
                        )
                    }
                }
                else -> Unit
            }
        }
    }
}

@Composable
private fun ContenidoLista(
    productos: List<Producto>,
    busqueda: String,
    onBusquedaChange: (String) -> Unit,
    categoriaSel: String?,
    onCategoriaChange: (String?) -> Unit,
    soloDisponibles: Boolean,
    onSoloDisponiblesChange: (Boolean) -> Unit,
    onAgregar: () -> Unit,
    onDetalle: (Int) -> Unit,
    modifier: Modifier = Modifier
) {
    var menuFiltro by remember { mutableStateOf(false) }
    val hayFiltros = categoriaSel != null || soloDisponibles

    val filtrados = remember(productos, busqueda, categoriaSel, soloDisponibles) {
        productos.filter { p ->
            (categoriaSel == null || p.categoria == categoriaSel) &&
                (!soloDisponibles || (p.disponible && p.stock > 0)) &&
                p.nombre.contains(busqueda.trim(), ignoreCase = true)
        }
    }

    Column(modifier) {
        if (productos.isNotEmpty()) {
            Row(
                Modifier.fillMaxWidth().padding(start = 16.dp, end = 8.dp, top = 8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                OutlinedTextField(
                    value = busqueda,
                    onValueChange = onBusquedaChange,
                    singleLine = true,
                    label = { Text("Buscar productos") },
                    leadingIcon = { Icon(Icons.Default.Search, contentDescription = null) },
                    trailingIcon = {
                        if (busqueda.isNotEmpty()) {
                            IconButton(onClick = { onBusquedaChange("") }) {
                                Icon(Icons.Default.Close, contentDescription = "Borrar búsqueda")
                            }
                        }
                    },
                    modifier = Modifier.weight(1f)
                )
                Box {
                    IconButton(onClick = { menuFiltro = true }, modifier = Modifier.size(48.dp)) {
                        Icon(
                            Icons.Default.FilterList,
                            contentDescription = "Filtrar productos",
                            tint = if (hayFiltros) MaterialTheme.colorScheme.primary
                            else MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                    DropdownMenu(expanded = menuFiltro, onDismissRequest = { menuFiltro = false }) {
                        DropdownMenuItem(
                            text = { Text("Todas las categorías") },
                            leadingIcon = {
                                if (categoriaSel == null) Icon(Icons.Default.Check, contentDescription = null)
                            },
                            onClick = { onCategoriaChange(null); menuFiltro = false }
                        )
                        CATEGORIAS.forEach { c ->
                            DropdownMenuItem(
                                text = { Text(c) },
                                leadingIcon = {
                                    Icon(
                                        if (categoriaSel == c) Icons.Default.Check else iconoCategoria(c),
                                        contentDescription = null
                                    )
                                },
                                onClick = { onCategoriaChange(c); menuFiltro = false }
                            )
                        }
                        HorizontalDivider()
                        DropdownMenuItem(
                            text = { Text("Solo disponibles") },
                            leadingIcon = {
                                Icon(
                                    if (soloDisponibles) Icons.Default.CheckBox else Icons.Default.CheckBoxOutlineBlank,
                                    contentDescription = null
                                )
                            },
                            onClick = { onSoloDisponiblesChange(!soloDisponibles) }
                        )
                    }
                }
            }

            // Filtros activos: se pueden quitar tocandolos
            if (hayFiltros) {
                Row(
                    Modifier.padding(horizontal = 16.dp, vertical = 4.dp),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    categoriaSel?.let { c ->
                        FilterChip(
                            selected = true,
                            onClick = { onCategoriaChange(null) },
                            label = { Text(c) },
                            leadingIcon = {
                                Icon(iconoCategoria(c), contentDescription = null, modifier = Modifier.size(18.dp))
                            },
                            trailingIcon = {
                                Icon(
                                    Icons.Default.Close,
                                    contentDescription = "Quitar filtro $c",
                                    modifier = Modifier.size(18.dp)
                                )
                            }
                        )
                    }
                    if (soloDisponibles) {
                        FilterChip(
                            selected = true,
                            onClick = { onSoloDisponiblesChange(false) },
                            label = { Text("Solo disponibles") },
                            trailingIcon = {
                                Icon(
                                    Icons.Default.Close,
                                    contentDescription = "Quitar filtro solo disponibles",
                                    modifier = Modifier.size(18.dp)
                                )
                            }
                        )
                    }
                }
            }
            Text(
                "${filtrados.size} producto(s)",
                style = MaterialTheme.typography.labelLarge,
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)
            )
        }

        when {
            // Estado vacio: no existen productos
            productos.isEmpty() -> EstadoMensaje(
                titulo = "No hay productos registrados.",
                detalle = "¡Comienza agregando tu primer producto!"
            ) {
                Button(onClick = onAgregar, modifier = Modifier.heightIn(min = 48.dp)) {
                    Icon(Icons.Default.Add, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text("Agregar producto")
                }
            }

            // Hay productos, pero el filtro no encontro ninguno
            filtrados.isEmpty() -> EstadoMensaje(
                titulo = "Sin resultados",
                detalle = "Prueba con otro nombre o cambia los filtros."
            ) {
                OutlinedButton(
                    onClick = {
                        onBusquedaChange("")
                        onCategoriaChange(null)
                        onSoloDisponiblesChange(false)
                    },
                    modifier = Modifier.heightIn(min = 48.dp)
                ) { Text("Limpiar filtros") }
            }

            else -> LazyColumn(
                modifier = Modifier.fillMaxSize(),
                contentPadding = PaddingValues(start = 16.dp, end = 16.dp, top = 4.dp, bottom = 96.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(filtrados, key = { it.id }) { p ->
                    ItemProducto(p) { onDetalle(p.id) }
                }
            }
        }
    }
}

@Composable
fun ItemProducto(p: Producto, onClick: () -> Unit) {
    val disponible = p.disponible && p.stock > 0
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClickLabel = "Ver detalle de ${p.nombre}", onClick = onClick)
    ) {
        Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
            ImagenProducto(
                path = p.imagenPath,
                iconoVacio = iconoCategoria(p.categoria),
                descripcion = "Imagen de ${p.nombre}",
                modifier = Modifier.size(64.dp)
            )
            Column(Modifier.weight(1f).padding(horizontal = 12.dp)) {
                Text(
                    p.nombre, style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold, maxLines = 1, overflow = TextOverflow.Ellipsis
                )
                Text(p.categoria, style = MaterialTheme.typography.bodySmall)
                Text(
                    formatoPrecio(p.precio),
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.primary
                )
            }
            Column(
                horizontalAlignment = Alignment.End,
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Icon(Icons.AutoMirrored.Filled.KeyboardArrowRight, contentDescription = null)
                EtiquetaDisponibilidad(disponible)
            }
        }
    }
}
'''

# ===========================================================================
# PESTAÑA PRODUCTOS (resumen + categorias)
# ===========================================================================
ARCHIVOS["ui/PantallaProductos.kt"] = r'''package __PKG__.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Cancel
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Inventory2
import androidx.compose.material.icons.filled.Payments
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.Icon
import androidx.compose.material3.ListItem
import androidx.compose.material3.ListItemDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import __PKG__.data.Producto

// Pestaña "Productos": resumen de la tienda y catalogo por categorias
@Composable
fun PestanaProductos(
    productos: List<Producto>,
    onAgregar: () -> Unit,
    onDetalle: (Int) -> Unit,
    onCategoria: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    if (productos.isEmpty()) {
        EstadoMensaje(
            titulo = "No hay productos registrados.",
            detalle = "¡Comienza agregando tu primer producto!",
            modifier = modifier
        ) {
            Button(onClick = onAgregar, modifier = Modifier.heightIn(min = 48.dp)) {
                Icon(Icons.Default.Add, contentDescription = null)
                Spacer(Modifier.width(8.dp))
                Text("Agregar producto")
            }
        }
        return
    }

    val total = productos.size
    val disponibles = productos.count { it.disponible && it.stock > 0 }
    val noDisponibles = total - disponibles
    val valorInventario = productos.sumOf { it.precio * it.stock }
    val stockBajo = productos.filter { it.stock <= 10 }.sortedBy { it.stock }.take(3)

    Column(
        modifier
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            TarjetaDato("Productos", total.toString(), Icons.Default.Inventory2, Modifier.weight(1f))
            TarjetaDato("Disponibles", disponibles.toString(), Icons.Default.CheckCircle, Modifier.weight(1f))
            TarjetaDato("No disponibles", noDisponibles.toString(), Icons.Default.Cancel, Modifier.weight(1f))
        }

        Card(Modifier.fillMaxWidth()) {
            ListItem(
                colors = ListItemDefaults.colors(containerColor = Color.Transparent),
                leadingContent = { Icon(Icons.Default.Payments, contentDescription = null) },
                headlineContent = { Text("Valor del inventario") },
                supportingContent = { Text(formatoPrecio(valorInventario)) }
            )
        }

        Text(
            "Categorías",
            style = MaterialTheme.typography.titleMedium,
            modifier = Modifier.semantics { heading() }
        )
        CATEGORIAS.chunked(2).forEach { fila ->
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                fila.forEach { c ->
                    TarjetaCategoria(
                        categoria = c,
                        cantidad = productos.count { it.categoria == c },
                        onClick = { onCategoria(c) },
                        modifier = Modifier.weight(1f)
                    )
                }
                if (fila.size == 1) Spacer(Modifier.weight(1f))
            }
        }

        Text(
            "Stock bajo (10 unidades o menos)",
            style = MaterialTheme.typography.titleMedium,
            modifier = Modifier.semantics { heading() }
        )
        if (stockBajo.isEmpty()) {
            Text("No hay productos con stock bajo.", style = MaterialTheme.typography.bodyMedium)
        } else {
            stockBajo.forEach { p ->
                ItemProducto(p) { onDetalle(p.id) }
            }
        }

        // Espacio para que el boton flotante no tape el ultimo elemento
        Spacer(Modifier.height(72.dp))
    }
}

@Composable
private fun TarjetaDato(etiqueta: String, valor: String, icono: ImageVector, modifier: Modifier = Modifier) {
    Card(modifier) {
        Column(
            Modifier.fillMaxWidth().padding(12.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Icon(icono, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
            Spacer(Modifier.height(4.dp))
            Text(valor, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
            Text(etiqueta, style = MaterialTheme.typography.labelMedium, textAlign = TextAlign.Center)
        }
    }
}

@Composable
private fun TarjetaCategoria(
    categoria: String,
    cantidad: Int,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier.clickable(onClickLabel = "Ver productos de $categoria", onClick = onClick)
    ) {
        Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
            Icon(
                iconoCategoria(categoria),
                contentDescription = null,
                modifier = Modifier.size(32.dp),
                tint = MaterialTheme.colorScheme.primary
            )
            Spacer(Modifier.width(12.dp))
            Column {
                Text(categoria, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                Text("$cantidad producto(s)", style = MaterialTheme.typography.bodySmall)
            }
        }
    }
}
'''

# ===========================================================================
# PESTAÑA PERFIL
# ===========================================================================
ARCHIVOS["ui/PantallaPerfil.kt"] = r'''package __PKG__.ui

import android.widget.Toast
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Inventory2
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.Save
import androidx.compose.material.icons.filled.Storage
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.Icon
import androidx.compose.material3.ListItem
import androidx.compose.material3.ListItemDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle

// Pestaña "Perfil": el nombre del estudiante se guarda con SharedPreferences
@Composable
fun PestanaPerfil(vm: ProductoViewModel, totalProductos: Int, modifier: Modifier = Modifier) {
    val nombre by vm.nombreUsuario.collectAsStateWithLifecycle()
    var texto by rememberSaveable(nombre) { mutableStateOf(nombre) }
    val context = LocalContext.current

    Column(
        modifier
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        Surface(
            shape = CircleShape,
            color = MaterialTheme.colorScheme.primaryContainer,
            modifier = Modifier.size(96.dp)
        ) {
            Box(contentAlignment = Alignment.Center) {
                Icon(
                    Icons.Default.Person,
                    contentDescription = "Imagen de perfil",
                    modifier = Modifier.size(56.dp),
                    tint = MaterialTheme.colorScheme.onPrimaryContainer
                )
            }
        }
        Text(
            if (nombre.isBlank()) "Estudiante" else "Hola, $nombre",
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.semantics { heading() }
        )
        Text("Personaliza tu perfil de Campus Market.", style = MaterialTheme.typography.bodyMedium)

        OutlinedTextField(
            value = texto,
            onValueChange = { if (it.length <= 40) texto = it },
            label = { Text("Tu nombre") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth()
        )
        Button(
            onClick = {
                vm.guardarNombre(texto)
                Toast.makeText(context, "Nombre guardado", Toast.LENGTH_SHORT).show()
            },
            modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)
        ) {
            Icon(Icons.Default.Save, contentDescription = null)
            Spacer(Modifier.width(8.dp))
            Text("Guardar nombre")
        }

        Card(Modifier.fillMaxWidth()) {
            val transparente = ListItemDefaults.colors(containerColor = Color.Transparent)
            ListItem(
                colors = transparente,
                leadingContent = { Icon(Icons.Default.Inventory2, contentDescription = null) },
                headlineContent = { Text("Productos en la tienda") },
                supportingContent = { Text("$totalProductos producto(s) registrados") }
            )
            ListItem(
                colors = transparente,
                leadingContent = { Icon(Icons.Default.Storage, contentDescription = null) },
                headlineContent = { Text("Almacenamiento") },
                supportingContent = { Text("Tus datos se guardan solo en este dispositivo.") }
            )
        }
    }
}
'''

# ===========================================================================
# CONFIGURACION
# ===========================================================================
ARCHIVOS["ui/PantallaConfiguracion.kt"] = r'''package __PKG__.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import __PKG__.data.Preferencias

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PantallaConfiguracion(vm: ProductoViewModel, onVolver: () -> Unit) {
    RegistrarCicloDeVida("PantallaConfiguracion")
    val tema by vm.tema.collectAsStateWithLifecycle()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Configuración") },
                navigationIcon = {
                    IconButton(onClick = onVolver) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Volver")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    titleContentColor = MaterialTheme.colorScheme.onPrimary,
                    navigationIconContentColor = MaterialTheme.colorScheme.onPrimary
                )
            )
        }
    ) { padding ->
        Column(
            Modifier
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text(
                "Apariencia",
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.semantics { heading() }
            )
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.selectableGroup().padding(vertical = 8.dp)) {
                    OpcionTema("Automático (según el sistema)", Preferencias.TEMA_SISTEMA, tema) { vm.cambiarTema(it) }
                    OpcionTema("Claro", Preferencias.TEMA_CLARO, tema) { vm.cambiarTema(it) }
                    OpcionTema("Oscuro", Preferencias.TEMA_OSCURO, tema) { vm.cambiarTema(it) }
                }
            }
            Text(
                "La opción elegida se guarda en el dispositivo y se mantiene al cerrar la app.",
                style = MaterialTheme.typography.bodyMedium
            )
        }
    }
}

@Composable
private fun OpcionTema(texto: String, valor: Int, actual: Int, onSeleccion: (Int) -> Unit) {
    Row(
        Modifier
            .fillMaxWidth()
            .heightIn(min = 48.dp)
            .selectable(
                selected = actual == valor,
                onClick = { onSeleccion(valor) },
                role = Role.RadioButton
            )
            .padding(horizontal = 16.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        RadioButton(selected = actual == valor, onClick = null)
        Spacer(Modifier.width(12.dp))
        Text(texto, style = MaterialTheme.typography.bodyLarge)
    }
}
'''

# ===========================================================================
# AYUDA
# ===========================================================================
ARCHIVOS["ui/PantallaAyuda.kt"] = r'''package __PKG__.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.CameraAlt
import androidx.compose.material.icons.filled.Code
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Share
import androidx.compose.material.icons.filled.Storage
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.ListItem
import androidx.compose.material3.ListItemDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PantallaAyuda(onVolver: () -> Unit) {
    RegistrarCicloDeVida("PantallaAyuda")

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Ayuda") },
                navigationIcon = {
                    IconButton(onClick = onVolver) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Volver")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    titleContentColor = MaterialTheme.colorScheme.onPrimary,
                    navigationIconContentColor = MaterialTheme.colorScheme.onPrimary
                )
            )
        }
    ) { padding ->
        Column(
            Modifier
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Text(
                "Campus Market - Versión 1.0. Funciona sin conexión a Internet.",
                style = MaterialTheme.typography.bodyLarge
            )

            Bloque("¿Cómo usar la app?") {
                Fila(Icons.Default.Search, "Buscar y filtrar", "Escribe el nombre o usa el icono de filtro para elegir categoría.")
                Fila(Icons.Default.Add, "Agregar un producto", "Toca el botón + y completa el formulario.")
                Fila(Icons.Default.Edit, "Editar o eliminar", "Abre el producto y usa los botones Editar o Eliminar.")
                Fila(Icons.Default.Share, "Compartir", "Desde el detalle, toca Compartir producto.")
                Fila(Icons.Default.CameraAlt, "Agregar una foto", "Toma una foto o elige una de la galería.")
            }

            Bloque("Tecnología") {
                Fila(Icons.Default.Code, "Kotlin y Jetpack Compose", "Interfaz moderna con Material Design 3.")
                Fila(Icons.Default.Storage, "Room sobre SQLite", "Tus productos se guardan en el dispositivo.")
            }
        }
    }
}

@Composable
private fun Bloque(titulo: String, contenido: @Composable () -> Unit) {
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(vertical = 8.dp)) {
            Text(
                titulo,
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier
                    .padding(horizontal = 16.dp, vertical = 8.dp)
                    .semantics { heading() }
            )
            contenido()
        }
    }
}

@Composable
private fun Fila(icono: ImageVector, titulo: String, detalle: String) {
    ListItem(
        colors = ListItemDefaults.colors(containerColor = Color.Transparent),
        leadingContent = { Icon(icono, contentDescription = null) },
        headlineContent = { Text(titulo) },
        supportingContent = { Text(detalle) }
    )
}
'''

# ===========================================================================
# FORMULARIO
# ===========================================================================
ARCHIVOS["ui/PantallaFormulario.kt"] = r'''package __PKG__.ui

import android.Manifest
import android.content.ActivityNotFoundException
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.provider.Settings
import android.widget.Toast
import androidx.activity.compose.BackHandler
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.toggleable
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.CameraAlt
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.PhotoLibrary
import androidx.compose.material.icons.filled.Save
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardCapitalization
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import __PKG__.data.Producto
import kotlinx.coroutines.launch
import java.util.Locale

private val FORMATO_PRECIO = Regex("^\\d+([.,]\\d{1,2})?\$")

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PantallaFormulario(vm: ProductoViewModel, productoId: Int, onVolver: () -> Unit) {
    RegistrarCicloDeVida("PantallaFormulario")

    val esEdicion = productoId != 0
    val context = LocalContext.current
    val alcance = rememberCoroutineScope()

    // Estado: producto seleccionado (solo cuando se edita)
    LaunchedEffect(productoId) { vm.seleccionar(if (esEdicion) productoId else null) }
    val seleccionado by vm.productoSeleccionado.collectAsStateWithLifecycle()
    val existente = seleccionado?.takeIf { esEdicion && it.id == productoId }

    // Estado: campos del formulario (rememberSaveable: no se pierden al rotar)
    var nombre by rememberSaveable { mutableStateOf("") }
    var descripcion by rememberSaveable { mutableStateOf("") }
    var categoria by rememberSaveable { mutableStateOf("") }
    var precio by rememberSaveable { mutableStateOf("") }
    var stock by rememberSaveable { mutableStateOf("") }
    var disponible by rememberSaveable { mutableStateOf(true) }
    var fotoTemporal by rememberSaveable { mutableStateOf<String?>(null) }
    var expandido by remember { mutableStateOf(false) }

    // Si es edicion, los datos se cargan una sola vez cuando Room los entrega
    var cargado by rememberSaveable { mutableStateOf(!esEdicion) }
    LaunchedEffect(existente) {
        if (!cargado && existente != null) {
            nombre = existente.nombre
            descripcion = existente.descripcion
            categoria = existente.categoria
            precio = String.format(Locale.US, "%.2f", existente.precio)
            stock = existente.stock.toString()
            disponible = existente.disponible
            cargado = true
        }
    }

    // Estado: validacion
    var intentoGuardar by rememberSaveable { mutableStateOf(false) }
    val precioNum = precio.replace(',', '.').toDoubleOrNull()
    val stockNum = stock.toIntOrNull()

    val errNombre = if (nombre.isBlank()) "El nombre es obligatorio." else null
    val errDescripcion = if (descripcion.isBlank()) "La descripción es obligatoria." else null
    val errCategoria = if (categoria.isBlank()) "Selecciona una categoría." else null
    val errPrecio = when {
        precio.isBlank() -> "El precio es obligatorio."
        precioNum == null -> "Ingresa un precio válido, por ejemplo 12.50."
        precioNum <= 0.0 -> "El precio debe ser mayor que 0."
        !FORMATO_PRECIO.matches(precio.trim()) -> "Usa el formato 12.50 (máximo 2 decimales)."
        else -> null
    }
    val errStock = when {
        stock.isBlank() -> "El stock es obligatorio."
        stockNum == null -> "El stock debe ser un número entero."
        stockNum < 0 -> "El stock debe ser 0 o mayor."
        else -> null
    }
    val esValido = listOf(errNombre, errDescripcion, errCategoria, errPrecio, errStock).all { it == null }

    // Los campos numericos avisan apenas se escribe algo; los de texto, al intentar guardar
    val verPrecio = intentoGuardar || precio.isNotEmpty()
    val verStock = intentoGuardar || stock.isNotEmpty()

    // Estado: cambios sin guardar (para avisar antes de salir)
    val hayCambios = when {
        esEdicion && existente == null -> false
        existente != null ->
            nombre != existente.nombre || descripcion != existente.descripcion ||
                categoria != existente.categoria ||
                precio != String.format(Locale.US, "%.2f", existente.precio) ||
                stock != existente.stock.toString() || disponible != existente.disponible ||
                fotoTemporal != null
        else ->
            nombre.isNotBlank() || descripcion.isNotBlank() || categoria.isNotBlank() ||
                precio.isNotBlank() || stock.isNotBlank() || fotoTemporal != null
    }
    var mostrarDescartar by rememberSaveable { mutableStateOf(false) }
    val salir: () -> Unit = {
        if (hayCambios) {
            mostrarDescartar = true
        } else {
            onVolver()
        }
    }
    BackHandler(enabled = hayCambios) { mostrarDescartar = true }

    // Estado: camara, galeria y permiso
    var mostrarExplicacion by rememberSaveable { mutableStateOf(false) }
    var mensajeAviso by rememberSaveable { mutableStateOf<String?>(null) }
    var permisoDenegado by rememberSaveable { mutableStateOf(false) }

    val camaraLauncher = rememberLauncherForActivityResult(ActivityResultContracts.TakePicturePreview()) { bitmap ->
        if (bitmap != null) {
            alcance.launch { fotoTemporal = vm.guardarFotoTemporal(bitmap) }
        }
    }
    // La galeria no necesita permiso: usa el selector de fotos del sistema
    val galeriaLauncher = rememberLauncherForActivityResult(ActivityResultContracts.PickVisualMedia()) { uri ->
        if (uri != null) {
            alcance.launch {
                val ruta = vm.guardarFotoTemporalDesdeUri(uri)
                if (ruta != null) {
                    fotoTemporal = ruta
                } else {
                    permisoDenegado = false
                    mensajeAviso = "No se pudo cargar la imagen. Intenta con otra foto."
                }
            }
        }
    }
    val lanzarCamara: () -> Unit = {
        try {
            camaraLauncher.launch(null)
        } catch (e: ActivityNotFoundException) {
            permisoDenegado = false
            mensajeAviso = "No se encontró una aplicación de cámara. Puedes continuar sin foto."
        }
    }
    val permisoLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { concedido ->
        if (concedido) {
            mensajeAviso = null
            permisoDenegado = false
            lanzarCamara()
        } else {
            // Permiso denegado: la app sigue funcionando sin foto
            permisoDenegado = true
            mensajeAviso = "El permiso de cámara fue denegado. Puedes continuar sin agregar una foto."
        }
    }
    val tomarFoto: () -> Unit = {
        val concedido = ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) ==
            PackageManager.PERMISSION_GRANTED
        if (concedido) {
            lanzarCamara()
        } else {
            mostrarExplicacion = true
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(if (esEdicion) "Editar producto" else "Agregar producto") },
                navigationIcon = {
                    IconButton(onClick = salir) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Volver")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    titleContentColor = MaterialTheme.colorScheme.onPrimary,
                    navigationIconContentColor = MaterialTheme.colorScheme.onPrimary
                )
            )
        }
    ) { padding ->
        Column(
            Modifier
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // Aviso amarillo (permiso denegado u otros avisos de la foto)
            mensajeAviso?.let { texto ->
                Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.tertiaryContainer)) {
                    Column(Modifier.padding(12.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                if (permisoDenegado) Icons.Default.Warning else Icons.Default.Info,
                                contentDescription = null,
                                tint = MaterialTheme.colorScheme.onTertiaryContainer
                            )
                            Spacer(Modifier.width(8.dp))
                            Text(
                                texto,
                                style = MaterialTheme.typography.bodyMedium,
                                color = MaterialTheme.colorScheme.onTertiaryContainer
                            )
                        }
                        if (permisoDenegado) {
                            TextButton(
                                onClick = {
                                    context.startActivity(
                                        Intent(
                                            Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                                            Uri.fromParts("package", context.packageName, null)
                                        )
                                    )
                                },
                                modifier = Modifier.heightIn(min = 48.dp)
                            ) { Text("Abrir ajustes de la app") }
                        }
                    }
                }
            }

            // Zona de la foto: vista previa, tomar foto y elegir de galeria
            val tieneFoto = fotoTemporal != null || existente?.imagenPath != null
            Column(
                Modifier.fillMaxWidth(),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                ImagenProducto(
                    path = fotoTemporal ?: existente?.imagenPath,
                    iconoVacio = Icons.Default.CameraAlt,
                    descripcion = if (tieneFoto) "Foto del producto" else "Sin foto",
                    modifier = Modifier.size(112.dp),
                    shape = RoundedCornerShape(16.dp),
                    tamanoIcono = 40.dp
                )
                Text(
                    if (tieneFoto) "Cambiar foto" else "Agregar foto",
                    style = MaterialTheme.typography.labelLarge
                )
                Button(
                    onClick = tomarFoto,
                    modifier = Modifier.widthIn(max = 320.dp).fillMaxWidth().heightIn(min = 48.dp)
                ) {
                    Icon(Icons.Default.CameraAlt, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text("Tomar foto")
                }
                OutlinedButton(
                    onClick = {
                        galeriaLauncher.launch(
                            PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly)
                        )
                    },
                    modifier = Modifier.widthIn(max = 320.dp).fillMaxWidth().heightIn(min = 48.dp)
                ) {
                    Icon(Icons.Default.PhotoLibrary, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text("Elegir de galería")
                }
            }

            CampoTexto(
                "Nombre *", nombre, { nombre = it },
                if (intentoGuardar) errNombre else null,
                placeholder = "Ej. Cuaderno A4",
                capitalizacion = KeyboardCapitalization.Sentences,
                maxCaracteres = 60, contador = true
            )
            CampoTexto(
                "Descripción *", descripcion, { descripcion = it },
                if (intentoGuardar) errDescripcion else null,
                placeholder = "Ej. Libreta de 100 hojas, tamaño A4.",
                capitalizacion = KeyboardCapitalization.Sentences,
                lineas = 3, maxCaracteres = 200, contador = true
            )

            ExposedDropdownMenuBox(expanded = expandido, onExpandedChange = { expandido = it }) {
                OutlinedTextField(
                    value = categoria, onValueChange = {}, readOnly = true,
                    label = { Text("Categoría *") },
                    placeholder = { Text("Seleccionar categoría") },
                    isError = intentoGuardar && errCategoria != null,
                    supportingText = { if (intentoGuardar && errCategoria != null) Text(errCategoria) },
                    trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expandido) },
                    modifier = Modifier.menuAnchor().fillMaxWidth()
                )
                ExposedDropdownMenu(expanded = expandido, onDismissRequest = { expandido = false }) {
                    CATEGORIAS.forEach { c ->
                        DropdownMenuItem(
                            text = { Text(c) },
                            leadingIcon = { Icon(iconoCategoria(c), contentDescription = null) },
                            onClick = { categoria = c; expandido = false }
                        )
                    }
                }
            }

            CampoTexto(
                "Precio *", precio, { precio = it },
                if (verPrecio) errPrecio else null,
                placeholder = "0.00", prefijo = "S/ ",
                teclado = KeyboardType.Decimal, maxCaracteres = 10
            )

            // Stock y Disponible en la misma fila, como en el prototipo
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(16.dp),
                verticalAlignment = Alignment.Top
            ) {
                Box(Modifier.weight(1f)) {
                    CampoTexto(
                        "Stock *", stock, { stock = it },
                        if (verStock) errStock else null,
                        placeholder = "0",
                        teclado = KeyboardType.Number, maxCaracteres = 6
                    )
                }
                Column(
                    Modifier
                        .heightIn(min = 48.dp)
                        .padding(top = 4.dp)
                        .toggleable(value = disponible, role = Role.Switch, onValueChange = { disponible = it }),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text("Disponible", style = MaterialTheme.typography.labelLarge)
                    Switch(checked = disponible, onCheckedChange = null)
                    Text(if (disponible) "Sí" else "No", style = MaterialTheme.typography.labelMedium)
                }
            }

            Button(
                onClick = {
                    intentoGuardar = true
                    if (esValido && precioNum != null && stockNum != null) {
                        vm.guardar(
                            Producto(
                                id = existente?.id ?: 0,
                                nombre = nombre.trim(),
                                descripcion = descripcion.trim(),
                                categoria = categoria,
                                precio = precioNum,
                                stock = stockNum,
                                disponible = disponible,
                                imagenPath = existente?.imagenPath
                            ),
                            fotoTemporal
                        )
                        Toast.makeText(
                            context,
                            if (esEdicion) "Producto actualizado" else "Producto guardado",
                            Toast.LENGTH_SHORT
                        ).show()
                        onVolver()
                    }
                },
                // En edicion, el boton se habilita cuando los datos ya se cargaron
                enabled = !esEdicion || existente != null,
                modifier = Modifier.fillMaxWidth().heightIn(min = 52.dp)
            ) {
                Icon(Icons.Default.Save, contentDescription = null)
                Spacer(Modifier.width(8.dp))
                Text("Guardar")
            }
        }
    }

    // Se explica para que se pide el permiso ANTES de solicitarlo
    if (mostrarExplicacion) {
        AlertDialog(
            onDismissRequest = { mostrarExplicacion = false },
            icon = { Icon(Icons.Default.CameraAlt, contentDescription = null) },
            title = { Text("¿Permitir el uso de la cámara?") },
            text = { Text("Campus Market usará la cámara solo para tomar una foto del producto. Puedes continuar sin foto si lo prefieres.") },
            confirmButton = {
                TextButton(onClick = {
                    mostrarExplicacion = false
                    permisoLauncher.launch(Manifest.permission.CAMERA)
                }) { Text("Permitir") }
            },
            dismissButton = {
                TextButton(onClick = {
                    mostrarExplicacion = false
                    permisoDenegado = false
                    mensajeAviso = "Continuarás sin foto."
                }) { Text("Cancelar") }
            }
        )
    }

    // Confirmacion al salir con cambios sin guardar
    if (mostrarDescartar) {
        AlertDialog(
            onDismissRequest = { mostrarDescartar = false },
            icon = { Icon(Icons.Default.Warning, contentDescription = null) },
            title = { Text("¿Descartar cambios?") },
            text = { Text("Tienes cambios sin guardar. Si sales ahora, se perderán.") },
            confirmButton = {
                TextButton(onClick = { mostrarDescartar = false; onVolver() }) { Text("Descartar") }
            },
            dismissButton = {
                TextButton(onClick = { mostrarDescartar = false }) { Text("Seguir editando") }
            }
        )
    }
}

@Composable
private fun CampoTexto(
    etiqueta: String,
    valor: String,
    onCambio: (String) -> Unit,
    error: String?,
    placeholder: String = "",
    prefijo: String? = null,
    teclado: KeyboardType = KeyboardType.Text,
    capitalizacion: KeyboardCapitalization = KeyboardCapitalization.None,
    lineas: Int = 1,
    maxCaracteres: Int = 100,
    contador: Boolean = false
) {
    OutlinedTextField(
        value = valor,
        onValueChange = { if (it.length <= maxCaracteres) onCambio(it) },
        label = { Text(etiqueta) },
        placeholder = { if (placeholder.isNotEmpty()) Text(placeholder) },
        prefix = if (prefijo != null) ({ Text(prefijo) }) else null,
        isError = error != null,
        supportingText = {
            if (error != null) {
                Text(error)
            } else if (contador) {
                Text("${valor.length}/$maxCaracteres")
            }
        },
        singleLine = lineas == 1,
        minLines = lineas,
        keyboardOptions = KeyboardOptions(
            keyboardType = teclado,
            capitalization = capitalizacion,
            imeAction = ImeAction.Next
        ),
        modifier = Modifier.fillMaxWidth()
    )
}
'''

# ===========================================================================
# DETALLE
# ===========================================================================
ARCHIVOS["ui/PantallaDetalle.kt"] = r'''package __PKG__.ui

import android.content.ActivityNotFoundException
import android.content.Intent
import android.widget.Toast
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.Inventory2
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material.icons.filled.Share
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.ListItem
import androidx.compose.material3.ListItemDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PantallaDetalle(vm: ProductoViewModel, productoId: Int, onEditar: (Int) -> Unit, onVolver: () -> Unit) {
    RegistrarCicloDeVida("PantallaDetalle")

    // Estado: producto seleccionado
    LaunchedEffect(productoId) { vm.seleccionar(productoId) }
    val seleccionado by vm.productoSeleccionado.collectAsStateWithLifecycle()
    val producto = seleccionado?.takeIf { it.id == productoId }

    // Estado: confirmacion de eliminacion y menu de tres puntos
    var confirmarEliminar by rememberSaveable { mutableStateOf(false) }
    var menuAbierto by remember { mutableStateOf(false) }
    val context = LocalContext.current

    // Intent: abre el selector de compartir del sistema
    val compartir: () -> Unit = {
        if (producto != null) {
            val texto = "Producto: ${producto.nombre}\n" +
                "Precio: ${formatoPrecio(producto.precio)}\n" +
                "Categoría: ${producto.categoria}"
            val intent = Intent(Intent.ACTION_SEND).apply {
                type = "text/plain"
                putExtra(Intent.EXTRA_SUBJECT, "Campus Market: ${producto.nombre}")
                putExtra(Intent.EXTRA_TEXT, texto)
            }
            try {
                context.startActivity(Intent.createChooser(intent, "Compartir producto"))
            } catch (e: ActivityNotFoundException) {
                Toast.makeText(context, "No hay aplicaciones para compartir", Toast.LENGTH_SHORT).show()
            }
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(if (confirmarEliminar) "Eliminar producto" else "Detalle del producto") },
                navigationIcon = {
                    IconButton(onClick = onVolver) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Volver")
                    }
                },
                actions = {
                    if (producto != null) {
                        Box {
                            IconButton(onClick = { menuAbierto = true }) {
                                Icon(Icons.Default.MoreVert, contentDescription = "Más opciones")
                            }
                            DropdownMenu(expanded = menuAbierto, onDismissRequest = { menuAbierto = false }) {
                                DropdownMenuItem(
                                    text = { Text("Compartir") },
                                    leadingIcon = { Icon(Icons.Default.Share, contentDescription = null) },
                                    onClick = { menuAbierto = false; compartir() }
                                )
                                DropdownMenuItem(
                                    text = { Text("Editar") },
                                    leadingIcon = { Icon(Icons.Default.Edit, contentDescription = null) },
                                    onClick = { menuAbierto = false; onEditar(producto.id) }
                                )
                                DropdownMenuItem(
                                    text = { Text("Eliminar") },
                                    leadingIcon = { Icon(Icons.Default.Delete, contentDescription = null) },
                                    onClick = { menuAbierto = false; confirmarEliminar = true }
                                )
                            }
                        }
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    titleContentColor = MaterialTheme.colorScheme.onPrimary,
                    navigationIconContentColor = MaterialTheme.colorScheme.onPrimary,
                    actionIconContentColor = MaterialTheme.colorScheme.onPrimary
                )
            )
        }
    ) { padding ->
        if (producto == null) {
            IndicadorCarga(Modifier.padding(padding))
            return@Scaffold
        }

        Column(
            Modifier
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            ImagenProducto(
                path = producto.imagenPath,
                iconoVacio = iconoCategoria(producto.categoria),
                descripcion = "Imagen de ${producto.nombre}",
                modifier = Modifier.fillMaxWidth().height(200.dp),
                shape = RoundedCornerShape(16.dp),
                tamanoIcono = 72.dp
            )

            Text(
                producto.nombre,
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold,
                modifier = Modifier.semantics { heading() }
            )
            EtiquetaCategoria(producto.categoria)
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Text(
                    formatoPrecio(producto.precio),
                    style = MaterialTheme.typography.headlineSmall,
                    color = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.weight(1f)
                )
                EtiquetaDisponibilidad(producto.disponible && producto.stock > 0)
            }

            Column {
                Text(
                    "Descripción",
                    style = MaterialTheme.typography.titleSmall,
                    modifier = Modifier.semantics { heading() }
                )
                Spacer(Modifier.height(4.dp))
                Text(producto.descripcion, style = MaterialTheme.typography.bodyLarge)
            }

            Card(Modifier.fillMaxWidth()) {
                val transparente = ListItemDefaults.colors(containerColor = Color.Transparent)
                ListItem(
                    colors = transparente,
                    leadingContent = { Icon(Icons.Default.Inventory2, contentDescription = null) },
                    headlineContent = { Text("Stock") },
                    supportingContent = { Text("${producto.stock} unidades") }
                )
                ListItem(
                    colors = transparente,
                    leadingContent = { Icon(iconoCategoria(producto.categoria), contentDescription = null) },
                    headlineContent = { Text("Categoría") },
                    supportingContent = { Text(producto.categoria) }
                )
                ListItem(
                    modifier = Modifier.clickable(onClickLabel = "Compartir producto", onClick = compartir),
                    colors = transparente,
                    leadingContent = { Icon(Icons.Default.Share, contentDescription = null) },
                    headlineContent = { Text("Compartir producto") }
                )
            }

            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Button(
                    onClick = { onEditar(producto.id) },
                    modifier = Modifier.weight(1f).heightIn(min = 48.dp)
                ) {
                    Icon(Icons.Default.Edit, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text("Editar")
                }
                Button(
                    onClick = { confirmarEliminar = true },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = MaterialTheme.colorScheme.error,
                        contentColor = MaterialTheme.colorScheme.onError
                    ),
                    modifier = Modifier.weight(1f).heightIn(min = 48.dp)
                ) {
                    Icon(Icons.Default.Delete, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text("Eliminar")
                }
            }
        }

        if (confirmarEliminar) {
            AlertDialog(
                onDismissRequest = { confirmarEliminar = false },
                icon = {
                    Icon(
                        Icons.Default.Delete,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.error
                    )
                },
                title = { Text("¿Eliminar producto?") },
                text = { Text("¿Está seguro de que desea eliminar el producto \"${producto.nombre}\"?") },
                confirmButton = {
                    Button(
                        onClick = {
                            vm.eliminar(producto)
                            confirmarEliminar = false
                            Toast.makeText(context, "Producto eliminado", Toast.LENGTH_SHORT).show()
                            onVolver()
                        },
                        colors = ButtonDefaults.buttonColors(
                            containerColor = MaterialTheme.colorScheme.error,
                            contentColor = MaterialTheme.colorScheme.onError
                        )
                    ) { Text("Eliminar") }
                },
                dismissButton = { TextButton(onClick = { confirmarEliminar = false }) { Text("Cancelar") } }
            )
        }
    }
}
'''

# ===========================================================================
# IMAGENES DE EJEMPLO (dibujos vectoriales)
# ===========================================================================
# Cada imagen: (angulo de rotacion, [(color, trazo), ...])  -- lienzo de 100 x 100
IMAGENES = {
    "prod_cuaderno": (0, [
        ("#1E5BB8", "M22,8 L84,8 L84,92 L22,92 Z"),
        ("#164A96", "M22,8 L32,8 L32,92 L22,92 Z"),
        ("#9E9E9E", "M12,16 L34,16 L34,21 L12,21 Z"),
        ("#9E9E9E", "M12,30 L34,30 L34,35 L12,35 Z"),
        ("#9E9E9E", "M12,44 L34,44 L34,49 L12,49 Z"),
        ("#9E9E9E", "M12,58 L34,58 L34,63 L12,63 Z"),
        ("#9E9E9E", "M12,72 L34,72 L34,77 L12,77 Z"),
        ("#FFFFFF", "M44,24 L76,24 L76,29 L44,29 Z"),
        ("#BBD3F2", "M44,36 L76,36 L76,39 L44,39 Z"),
        ("#BBD3F2", "M44,44 L70,44 L70,47 L44,47 Z"),
    ]),
    "prod_lapicero": (45, [
        ("#0D47A1", "M44,4 L56,4 L56,14 L44,14 Z"),
        ("#1565C0", "M44,14 L56,14 L56,74 L44,74 Z"),
        ("#90A4AE", "M56,18 L60,18 L60,44 L56,44 Z"),
        ("#ECEFF1", "M44,74 L56,74 L50,90 Z"),
        ("#263238", "M48,85 L52,85 L50,90 Z"),
    ]),
    "prod_botella": (0, [
        ("#B0BEC5", "M40,4 L60,4 L60,13 L40,13 Z"),
        ("#263238", "M43,13 L57,13 L57,20 L43,20 Z"),
        ("#263238", "M43,20 L57,20 L67,32 L33,32 Z"),
        ("#263238", "M33,32 L67,32 L67,92 L33,92 Z"),
        ("#455A64", "M39,38 L44,38 L44,86 L39,86 Z"),
        ("#37474F", "M33,52 L67,52 L67,66 L33,66 Z"),
    ]),
    "prod_mochila": (0, [
        ("#303030", "M14,46 L24,46 L24,82 L14,82 Z"),
        ("#303030", "M76,46 L86,46 L86,82 L76,82 Z"),
        ("#212121", "M42,10 L58,10 L58,24 L54,24 L54,15 L46,15 L46,24 L42,24 Z"),
        ("#212121", "M30,22 L70,22 L80,34 L80,92 L20,92 L20,34 Z"),
        ("#333333", "M34,34 L66,34 L66,50 L34,50 Z"),
        ("#424242", "M30,58 L70,58 L70,84 L30,84 Z"),
        ("#9E9E9E", "M30,58 L70,58 L70,61 L30,61 Z"),
    ]),
    "prod_usb": (0, [
        ("#B0BEC5", "M38,6 L62,6 L62,36 L38,36 Z"),
        ("#37474F", "M43,12 L48,12 L48,24 L43,24 Z"),
        ("#37474F", "M52,12 L57,12 L57,24 L52,24 Z"),
        ("#263238", "M32,36 L68,36 L68,92 L32,92 Z"),
        ("#455A64", "M32,60 L68,60 L68,65 L32,65 Z"),
        ("#CFD8DC", "M44,78 a6,6 0 1,0 12,0 a6,6 0 1,0 -12,0 Z"),
    ]),
}


def generar_vector(rotacion, capas):
    lineas = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<vector xmlns:android="http://schemas.android.com/apk/res/android"',
        '    android:width="96dp"',
        '    android:height="96dp"',
        '    android:viewportWidth="100"',
        '    android:viewportHeight="100">',
    ]
    sangria = "    "
    if rotacion:
        lineas.append(f'    <group android:rotation="{rotacion}" android:pivotX="50" android:pivotY="50">')
        sangria = "        "
    for color, trazo in capas:
        lineas.append(f'{sangria}<path android:fillColor="{color}" android:pathData="{trazo}" />')
    if rotacion:
        lineas.append("    </group>")
    lineas.append("</vector>")
    return "\n".join(lineas) + "\n"


# ===========================================================================
# Escritura de archivos
# ===========================================================================
def guardar_con_respaldo(destino, texto, rel):
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    if os.path.exists(destino):
        copia = os.path.join(RESPALDO, rel)
        os.makedirs(os.path.dirname(copia), exist_ok=True)
        shutil.copy2(destino, copia)
    with open(destino, "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)


print("Codigo Kotlin:")
for rel, codigo in ARCHIVOS.items():
    destino = os.path.join(RUTA_PKG, *rel.split("/"))
    guardar_con_respaldo(destino, codigo.replace("__PKG__", PKG), rel)
    print(f"  [OK] {rel}")

print("\nImagenes de ejemplo (res/drawable):")
for nombre, (rotacion, capas) in IMAGENES.items():
    destino = os.path.join(RUTA_RES, "drawable", nombre + ".xml")
    guardar_con_respaldo(destino, generar_vector(rotacion, capas), os.path.join("res", nombre + ".xml"))
    print(f"  [OK] {nombre}.xml")

# Archivos de versiones anteriores que ya no se usan (se guarda copia en el respaldo)
print("\nArchivos antiguos que se retiran:")
for rel in ("ui/PantallaInicio.kt", "ui/PantallaAcerca.kt"):
    ruta = os.path.join(RUTA_PKG, *rel.split("/"))
    if os.path.exists(ruta):
        copia = os.path.join(RESPALDO, rel)
        os.makedirs(os.path.dirname(copia), exist_ok=True)
        shutil.move(ruta, copia)
        print(f"  [OK] {rel} (copia en _respaldo_prototipo)")
    else:
        print(f"  [--] {rel} no existia")

# ===========================================================================
# Revision de requisitos
# ===========================================================================
print("\nRevision del proyecto:")
manifest_ruta = os.path.join(RAIZ, "app", "src", "main", "AndroidManifest.xml")
manifest = open(manifest_ruta, encoding="utf-8").read() if os.path.exists(manifest_ruta) else ""
if "android.permission.CAMERA" not in manifest:
    print('  [!] Falta el permiso de camara en el Manifest. Agrega antes de <application>:')
    print('      <uses-permission android:name="android.permission.CAMERA" />')
else:
    print("  [OK] Permiso de camara declarado")
if ".MainActivity" not in manifest:
    print("  [!] MainActivity no esta registrada en el Manifest (ejecuta crear_campusmarket.py).")
else:
    print("  [OK] MainActivity registrada")

faltan = []
for clave, linea in (
    ("lifecycle-runtime-compose", 'implementation("androidx.lifecycle:lifecycle-runtime-compose:2.9.0")'),
    ("material-icons-extended", 'implementation("androidx.compose.material:material-icons-extended")'),
    ("navigation-compose", 'implementation("androidx.navigation:navigation-compose:2.9.0")'),
    ("room-runtime", 'implementation("androidx.room:room-runtime:2.8.4")'),
):
    if clave not in contenido_gradle:
        faltan.append(linea)
if faltan:
    print("  [!] Agrega estas lineas en dependencies { } de app/build.gradle.kts y haz Sync:")
    for linea in faltan:
        print("      " + linea)
else:
    print("  [OK] Dependencias de Gradle completas")

print("\nListo. Sync, Build > Rebuild Project y ejecuta.")
print("Si algo falla, los archivos anteriores estan en _respaldo_prototipo/ (copialos de vuelta).")
print("Nota: si tu emulador ya tenia la app instalada, se actualiza sin perder productos.")
