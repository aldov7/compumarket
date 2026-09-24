package com.example.campusmarket.ui

import android.graphics.BitmapFactory
import android.util.Log
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
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
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.util.Locale

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

// Muestra la foto del producto (si existe) o un icono representativo.
// La imagen se decodifica fuera del hilo principal para no bloquear la interfaz.
@Composable
fun ImagenProducto(
    path: String?,
    iconoVacio: ImageVector,
    descripcion: String,
    modifier: Modifier = Modifier,
    shape: Shape = CircleShape,
    tamanoIcono: Dp = 28.dp
) {
    val bitmap by produceState<ImageBitmap?>(initialValue = null, key1 = path) {
        value = if (path == null) null else withContext(Dispatchers.IO) {
            BitmapFactory.decodeFile(path)?.asImageBitmap()
        }
    }
    Surface(shape = shape, color = MaterialTheme.colorScheme.primaryContainer, modifier = modifier) {
        val imagen = bitmap
        if (imagen != null) {
            Image(
                bitmap = imagen,
                contentDescription = descripcion,
                contentScale = ContentScale.Crop,
                modifier = Modifier.fillMaxSize()
            )
        } else {
            Box(contentAlignment = Alignment.Center) {
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

// Registra en Logcat (etiqueta "CicloVida") los eventos del ciclo de vida de cada pantalla.
// Sirve para demostrar el ciclo de vida en el informe y en el video.
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
