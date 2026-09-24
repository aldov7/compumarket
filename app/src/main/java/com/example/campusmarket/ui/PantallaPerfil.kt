package com.example.campusmarket.ui

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
