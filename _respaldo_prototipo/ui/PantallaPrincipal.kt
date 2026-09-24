package com.example.campusmarket.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
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
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Inventory2
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Store
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CenterAlignedTopAppBar
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExtendedFloatingActionButton
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.example.campusmarket.data.Producto

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PantallaPrincipal(vm: ProductoViewModel, onAgregar: () -> Unit, onDetalle: (Int) -> Unit) {
    RegistrarCicloDeVida("PantallaPrincipal")

    // collectAsStateWithLifecycle: deja de escuchar la base de datos cuando la app no esta visible
    val estado by vm.listaState.collectAsStateWithLifecycle()

    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.Store, contentDescription = null)
                        Spacer(Modifier.width(8.dp))
                        Text("Campus Market", fontWeight = FontWeight.Bold)
                    }
                },
                colors = TopAppBarDefaults.centerAlignedTopAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    titleContentColor = MaterialTheme.colorScheme.onPrimary
                )
            )
        },
        floatingActionButton = {
            ExtendedFloatingActionButton(
                onClick = onAgregar,
                icon = { Icon(Icons.Default.Add, contentDescription = null) },
                text = { Text("Agregar producto") }
            )
        }
    ) { padding ->
        when (val e = estado) {
            is ListaUiState.Cargando -> IndicadorCarga(Modifier.padding(padding))
            is ListaUiState.Datos -> ContenidoLista(
                productos = e.productos,
                onAgregar = onAgregar,
                onDetalle = onDetalle,
                modifier = Modifier.padding(padding)
            )
        }
    }
}

@Composable
private fun ContenidoLista(
    productos: List<Producto>,
    onAgregar: () -> Unit,
    onDetalle: (Int) -> Unit,
    modifier: Modifier = Modifier
) {
    // Estados de la interfaz (sobreviven a la rotacion)
    var busqueda by rememberSaveable { mutableStateOf("") }
    var categoriaSel by rememberSaveable { mutableStateOf<String?>(null) }

    val filtrados = remember(productos, busqueda, categoriaSel) {
        productos.filter { p ->
            (categoriaSel == null || p.categoria == categoriaSel) &&
                p.nombre.contains(busqueda.trim(), ignoreCase = true)
        }
    }

    Column(modifier) {
        if (productos.isNotEmpty()) {
            OutlinedTextField(
                value = busqueda,
                onValueChange = { busqueda = it },
                singleLine = true,
                label = { Text("Buscar productos") },
                leadingIcon = { Icon(Icons.Default.Search, contentDescription = null) },
                trailingIcon = {
                    if (busqueda.isNotEmpty()) {
                        IconButton(onClick = { busqueda = "" }) {
                            Icon(Icons.Default.Close, contentDescription = "Borrar búsqueda")
                        }
                    }
                },
                modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp)
            )

            LazyRow(
                contentPadding = PaddingValues(horizontal = 16.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                item {
                    FilterChip(
                        selected = categoriaSel == null,
                        onClick = { categoriaSel = null },
                        label = { Text("Todas") },
                        leadingIcon = {
                            if (categoriaSel == null) {
                                Icon(Icons.Default.Check, contentDescription = null, modifier = Modifier.size(18.dp))
                            }
                        }
                    )
                }
                items(CATEGORIAS) { c ->
                    val seleccionada = categoriaSel == c
                    FilterChip(
                        selected = seleccionada,
                        onClick = { categoriaSel = if (seleccionada) null else c },
                        label = { Text(c) },
                        leadingIcon = {
                            // Un icono distinto cuando esta seleccionado: no depende solo del color
                            Icon(
                                if (seleccionada) Icons.Default.Check else iconoCategoria(c),
                                contentDescription = null,
                                modifier = Modifier.size(18.dp)
                            )
                        }
                    )
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
                detalle = "Prueba con otro nombre o cambia la categoría."
            ) {
                OutlinedButton(
                    onClick = { busqueda = ""; categoriaSel = null },
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
private fun EstadoMensaje(titulo: String, detalle: String, accion: @Composable () -> Unit) {
    Column(
        Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Icon(
            Icons.Default.Inventory2, contentDescription = null,
            modifier = Modifier.size(72.dp),
            tint = MaterialTheme.colorScheme.primary
        )
        Spacer(Modifier.height(12.dp))
        Text(titulo, style = MaterialTheme.typography.titleMedium, textAlign = TextAlign.Center)
        Text(detalle, style = MaterialTheme.typography.bodyMedium, textAlign = TextAlign.Center)
        Spacer(Modifier.height(16.dp))
        accion()
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
                modifier = Modifier.size(56.dp)
            )
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f)) {
                Text(
                    p.nombre, style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold, maxLines = 1, overflow = TextOverflow.Ellipsis
                )
                Text(p.categoria, style = MaterialTheme.typography.bodyMedium)
                Text(
                    formatoPrecio(p.precio),
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.primary
                )
            }
            Spacer(Modifier.width(8.dp))
            EtiquetaDisponibilidad(disponible)
        }
    }
}
