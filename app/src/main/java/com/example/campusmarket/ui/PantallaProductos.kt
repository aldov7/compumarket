package com.example.campusmarket.ui

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
import com.example.campusmarket.data.Producto

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
