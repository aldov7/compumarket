package com.example.campusmarket.ui

import android.Manifest
import android.content.ActivityNotFoundException
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.net.Uri
import android.provider.Settings
import android.widget.Toast
import androidx.activity.compose.BackHandler
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.toggleable
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.CameraAlt
import androidx.compose.material.icons.filled.Info
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
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardCapitalization
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.example.campusmarket.data.Producto

private val FORMATO_PRECIO = Regex("^\\d+([.,]\\d{1,2})?\$")

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PantallaFormulario(vm: ProductoViewModel, productoId: Int, onVolver: () -> Unit) {
    RegistrarCicloDeVida("PantallaFormulario")

    val esEdicion = productoId != 0
    val context = LocalContext.current

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
    var nuevaFoto by rememberSaveable { mutableStateOf<Bitmap?>(null) }
    var expandido by remember { mutableStateOf(false) }

    // Si es edicion, los datos se cargan una sola vez cuando Room los entrega
    var cargado by rememberSaveable { mutableStateOf(!esEdicion) }
    LaunchedEffect(existente) {
        if (!cargado && existente != null) {
            nombre = existente.nombre
            descripcion = existente.descripcion
            categoria = existente.categoria
            precio = existente.precio.toString()
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
                categoria != existente.categoria || precio != existente.precio.toString() ||
                stock != existente.stock.toString() || disponible != existente.disponible ||
                nuevaFoto != null
        else ->
            nombre.isNotBlank() || descripcion.isNotBlank() || categoria.isNotBlank() ||
                precio.isNotBlank() || stock.isNotBlank() || nuevaFoto != null
    }
    var mostrarDescartar by rememberSaveable { mutableStateOf(false) }
    val salir: () -> Unit = { if (hayCambios) mostrarDescartar = true else onVolver() }
    BackHandler(enabled = hayCambios) { mostrarDescartar = true }

    // Estado: camara y permiso
    var mostrarExplicacion by rememberSaveable { mutableStateOf(false) }
    var mensajePermiso by rememberSaveable { mutableStateOf<String?>(null) }
    var permisoDenegado by rememberSaveable { mutableStateOf(false) }

    val camaraLauncher = rememberLauncherForActivityResult(ActivityResultContracts.TakePicturePreview()) { resultado ->
        if (resultado != null) nuevaFoto = resultado
    }
    val lanzarCamara: () -> Unit = {
        try {
            camaraLauncher.launch(null)
        } catch (e: ActivityNotFoundException) {
            mensajePermiso = "No se encontró una aplicación de cámara. Puedes continuar sin foto."
        }
    }
    val permisoLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { concedido ->
        if (concedido) {
            mensajePermiso = null
            permisoDenegado = false
            lanzarCamara()
        } else {
            // Permiso denegado: la app sigue funcionando sin foto
            permisoDenegado = true
            mensajePermiso = "El permiso de cámara fue denegado. Puedes continuar sin agregar una foto."
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
            mensajePermiso?.let { texto ->
                Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondaryContainer)) {
                    Column(Modifier.padding(12.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                if (permisoDenegado) Icons.Default.Warning else Icons.Default.Info,
                                contentDescription = null
                            )
                            Spacer(Modifier.width(8.dp))
                            Text(texto, style = MaterialTheme.typography.bodyMedium)
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

            // Zona de la foto
            Column(Modifier.fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally) {
                val fotoTomada = nuevaFoto
                if (fotoTomada != null) {
                    Image(
                        bitmap = fotoTomada.asImageBitmap(),
                        contentDescription = "Foto del producto",
                        contentScale = ContentScale.Crop,
                        modifier = Modifier.size(120.dp).then(Modifier)
                    )
                } else {
                    ImagenProducto(
                        path = existente?.imagenPath,
                        iconoVacio = Icons.Default.CameraAlt,
                        descripcion = if (existente?.imagenPath != null) "Foto del producto" else "Sin foto",
                        modifier = Modifier.size(120.dp),
                        shape = RoundedCornerShape(16.dp),
                        tamanoIcono = 40.dp
                    )
                }
                Spacer(Modifier.height(8.dp))
                OutlinedButton(
                    onClick = {
                        val ok = ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) ==
                            PackageManager.PERMISSION_GRANTED
                        if (ok) lanzarCamara() else mostrarExplicacion = true
                    },
                    modifier = Modifier.heightIn(min = 48.dp)
                ) {
                    Icon(Icons.Default.CameraAlt, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text(if (nuevaFoto != null || existente?.imagenPath != null) "Cambiar foto" else "Tomar foto")
                }
            }

            CampoTexto(
                "Nombre *", nombre, { nombre = it },
                if (intentoGuardar) errNombre else null,
                capitalizacion = KeyboardCapitalization.Sentences,
                maxCaracteres = 60, contador = true
            )
            CampoTexto(
                "Descripción *", descripcion, { descripcion = it },
                if (intentoGuardar) errDescripcion else null,
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
                "Precio (S/) *", precio, { precio = it },
                if (verPrecio) errPrecio else null,
                teclado = KeyboardType.Decimal, maxCaracteres = 10
            )
            CampoTexto(
                "Stock *", stock, { stock = it },
                if (verStock) errStock else null,
                teclado = KeyboardType.Number, maxCaracteres = 6
            )

            // Fila completa tocable para cambiar Disponible Si/No
            Row(
                Modifier
                    .fillMaxWidth()
                    .heightIn(min = 48.dp)
                    .toggleable(value = disponible, role = Role.Switch, onValueChange = { disponible = it }),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text("Disponible", Modifier.weight(1f), style = MaterialTheme.typography.bodyLarge)
                Text(if (disponible) "Sí" else "No", style = MaterialTheme.typography.bodyLarge)
                Spacer(Modifier.width(8.dp))
                Switch(checked = disponible, onCheckedChange = null)
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
                            nuevaFoto
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
                    mensajePermiso = "Continuarás sin foto."
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
        isError = error != null,
        supportingText = {
            if (error != null) Text(error)
            else if (contador) Text("${valor.length}/$maxCaracteres")
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
