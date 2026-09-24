package com.example.campusmarket.ui

import android.app.Application
import android.graphics.Bitmap
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.example.campusmarket.data.AppDatabase
import com.example.campusmarket.data.Producto
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
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

    // CREATE y UPDATE: si hay una foto nueva, se guarda en disco y se reemplaza la anterior
    fun guardar(producto: Producto, foto: Bitmap? = null) = viewModelScope.launch {
        var ruta = producto.imagenPath
        if (foto != null) {
            val anterior = ruta
            ruta = withContext(Dispatchers.IO) {
                anterior?.let { File(it).delete() }
                guardarFotoEnDisco(foto)
            }
        }
        val guardado = producto.copy(imagenPath = ruta)
        if (guardado.id == 0) dao.insertar(guardado) else dao.actualizar(guardado)
    }

    // DELETE: tambien borra el archivo de la foto
    fun eliminar(producto: Producto) = viewModelScope.launch {
        dao.eliminar(producto)
        producto.imagenPath?.let { ruta ->
            withContext(Dispatchers.IO) { File(ruta).delete() }
        }
    }

    private fun guardarFotoEnDisco(foto: Bitmap): String {
        val carpeta = File(getApplication<Application>().filesDir, "fotos").apply { mkdirs() }
        val archivo = File(carpeta, "foto_${System.currentTimeMillis()}.jpg")
        archivo.outputStream().use { salida ->
            foto.compress(Bitmap.CompressFormat.JPEG, 90, salida)
        }
        return archivo.absolutePath
    }
}
