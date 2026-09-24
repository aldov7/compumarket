package com.example.campusmarket.ui

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
