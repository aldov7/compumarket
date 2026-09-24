package com.example.campusmarket.data

import android.content.Context

// Preferencias sencillas del usuario guardadas con SharedPreferences
class Preferencias(context: Context) {

    private val prefs = context.applicationContext
        .getSharedPreferences("campus_market_prefs", Context.MODE_PRIVATE)

    fun leerNombre(): String = prefs.getString(CLAVE_NOMBRE, "") ?: ""

    fun guardarNombre(nombre: String) {
        prefs.edit().putString(CLAVE_NOMBRE, nombre).apply()
    }

    fun leerTema(): Int = prefs.getInt(CLAVE_TEMA, TEMA_SISTEMA)

    fun guardarTema(tema: Int) {
        prefs.edit().putInt(CLAVE_TEMA, tema).apply()
    }

    companion object {
        const val TEMA_SISTEMA = 0
        const val TEMA_CLARO = 1
        const val TEMA_OSCURO = 2
        private const val CLAVE_NOMBRE = "nombre_usuario"
        private const val CLAVE_TEMA = "tema"
    }
}
