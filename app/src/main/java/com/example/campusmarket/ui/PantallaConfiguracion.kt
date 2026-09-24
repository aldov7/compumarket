package com.example.campusmarket.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.example.campusmarket.data.Preferencias

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PantallaConfiguracion(vm: ProductoViewModel, onVolver: () -> Unit) {
    RegistrarCicloDeVida("PantallaConfiguracion")
    val tema by vm.tema.collectAsStateWithLifecycle()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Configuración") },
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
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text(
                "Apariencia",
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.semantics { heading() }
            )
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.selectableGroup().padding(vertical = 8.dp)) {
                    OpcionTema("Automático (según el sistema)", Preferencias.TEMA_SISTEMA, tema) { vm.cambiarTema(it) }
                    OpcionTema("Claro", Preferencias.TEMA_CLARO, tema) { vm.cambiarTema(it) }
                    OpcionTema("Oscuro", Preferencias.TEMA_OSCURO, tema) { vm.cambiarTema(it) }
                }
            }
            Text(
                "La opción elegida se guarda en el dispositivo y se mantiene al cerrar la app.",
                style = MaterialTheme.typography.bodyMedium
            )
        }
    }
}

@Composable
private fun OpcionTema(texto: String, valor: Int, actual: Int, onSeleccion: (Int) -> Unit) {
    Row(
        Modifier
            .fillMaxWidth()
            .heightIn(min = 48.dp)
            .selectable(
                selected = actual == valor,
                onClick = { onSeleccion(valor) },
                role = Role.RadioButton
            )
            .padding(horizontal = 16.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        RadioButton(selected = actual == valor, onClick = null)
        Spacer(Modifier.width(12.dp))
        Text(texto, style = MaterialTheme.typography.bodyLarge)
    }
}
