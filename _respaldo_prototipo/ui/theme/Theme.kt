package com.example.campusmarket.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

// Paleta verde con buen contraste (texto oscuro sobre fondos claros y viceversa)
private val EsquemaClaro = lightColorScheme(
    primary = Color(0xFF00695C),
    onPrimary = Color.White,
    primaryContainer = Color(0xFFB2DFDB),
    onPrimaryContainer = Color(0xFF00201C),
    secondary = Color(0xFF4A635F),
    secondaryContainer = Color(0xFFCCE8E3),
    onSecondaryContainer = Color(0xFF05201D),
    error = Color(0xFFB3261E),
    errorContainer = Color(0xFFF9DEDC),
    onErrorContainer = Color(0xFF410E0B),
    background = Color(0xFFF6FBF9),
    surface = Color(0xFFF6FBF9)
)

private val EsquemaOscuro = darkColorScheme(
    primary = Color(0xFF4DB6AC),
    onPrimary = Color(0xFF003731),
    primaryContainer = Color(0xFF005048),
    onPrimaryContainer = Color(0xFFB2DFDB),
    secondary = Color(0xFFB0CCC7),
    secondaryContainer = Color(0xFF334B47),
    onSecondaryContainer = Color(0xFFCCE8E3),
    error = Color(0xFFF2B8B5),
    errorContainer = Color(0xFF8C1D18),
    onErrorContainer = Color(0xFFF9DEDC),
    background = Color(0xFF0F1614),
    surface = Color(0xFF0F1614)
)

@Composable
fun CampusMarketTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    MaterialTheme(
        colorScheme = if (darkTheme) EsquemaOscuro else EsquemaClaro,
        content = content
    )
}
