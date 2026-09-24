package com.example.campusmarket.data

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "productos")
data class Producto(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val nombre: String,
    val descripcion: String,
    val categoria: String,
    val precio: Double,
    val stock: Int,
    val disponible: Boolean,
    // Ruta de la foto guardada en el almacenamiento interno de la app (opcional)
    val imagenPath: String? = null
)
