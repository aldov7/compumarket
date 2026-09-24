package com.example.campusmarket.ui

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
import com.example.campusmarket.data.Producto
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
