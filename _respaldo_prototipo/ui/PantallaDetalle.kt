package com.example.campusmarket.ui

import android.content.ActivityNotFoundException
import android.content.Intent
import android.widget.Toast
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
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.Inventory2
import androidx.compose.material.icons.filled.Share
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.ListItem
import androidx.compose.material3.ListItemDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
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
import androidx.compose.ui.text.style.TextAlign
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

    // Estado: confirmacion de eliminacion
    var confirmarEliminar by rememberSaveable { mutableStateOf(false) }
    val context = LocalContext.current

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Detalle del producto") },
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
        if (producto == null) {
            IndicadorCarga(Modifier.padding(padding))
            return@Scaffold
        }

        Column(
            Modifier
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            ImagenProducto(
                path = producto.imagenPath,
                iconoVacio = iconoCategoria(producto.categoria),
                descripcion = if (producto.imagenPath != null) "Foto de ${producto.nombre}" else "Categoría ${producto.categoria}",
                modifier = Modifier.size(140.dp),
                tamanoIcono = 56.dp
            )

            Text(
                producto.nombre,
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold,
                textAlign = TextAlign.Center,
                modifier = Modifier.semantics { heading() }
            )
            Text(
                formatoPrecio(producto.precio),
                style = MaterialTheme.typography.headlineMedium,
                color = MaterialTheme.colorScheme.primary
            )
            EtiquetaDisponibilidad(producto.disponible && producto.stock > 0)

            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp)) {
                    Text(
                        "Descripción",
                        style = MaterialTheme.typography.titleSmall,
                        modifier = Modifier.semantics { heading() }
                    )
                    Spacer(Modifier.height(4.dp))
                    Text(producto.descripcion, style = MaterialTheme.typography.bodyLarge)
                }
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
            }

            // Intent: abre el selector de compartir del sistema
            FilledTonalButton(
                onClick = {
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
                },
                modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)
            ) {
                Icon(Icons.Default.Share, contentDescription = null)
                Spacer(Modifier.width(8.dp))
                Text("Compartir producto")
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
                OutlinedButton(
                    onClick = { confirmarEliminar = true },
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = MaterialTheme.colorScheme.error),
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
                icon = { Icon(Icons.Default.Delete, contentDescription = null) },
                title = { Text("¿Eliminar producto?") },
                text = { Text("¿Está seguro de que desea eliminar \"${producto.nombre}\"? Esta acción no se puede deshacer.") },
                confirmButton = {
                    TextButton(onClick = {
                        vm.eliminar(producto)
                        confirmarEliminar = false
                        Toast.makeText(context, "Producto eliminado", Toast.LENGTH_SHORT).show()
                        onVolver()
                    }) { Text("Eliminar") }
                },
                dismissButton = { TextButton(onClick = { confirmarEliminar = false }) { Text("Cancelar") } }
            )
        }
    }
}
