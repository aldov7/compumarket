package com.example.campusmarket.ui

import android.app.Application
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.example.campusmarket.data.AppDatabase
import com.example.campusmarket.data.Preferencias
import com.example.campusmarket.data.Producto
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
