package com.example.campusmarket

import android.os.Bundle
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import com.example.campusmarket.navegacion.AppNavegacion
import com.example.campusmarket.ui.theme.CampusMarketTheme

class MainActivity : ComponentActivity() {

    private val etiqueta = "CicloVida"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        Log.d(etiqueta, "onCreate (estado guardado: ${savedInstanceState != null})")
        setContent {
            CampusMarketTheme {
                Surface(modifier = Modifier.fillMaxSize()) { AppNavegacion() }
            }
        }
    }

    override fun onStart() { super.onStart(); Log.d(etiqueta, "onStart: la pantalla es visible") }
    override fun onResume() { super.onResume(); Log.d(etiqueta, "onResume: la app esta en primer plano") }
    override fun onPause() { super.onPause(); Log.d(etiqueta, "onPause: la app pierde el foco") }
    override fun onStop() { super.onStop(); Log.d(etiqueta, "onStop: la app ya no es visible") }
    override fun onDestroy() {
        super.onDestroy()
        Log.d(etiqueta, "onDestroy (por rotacion: $isChangingConfigurations)")
    }
}
