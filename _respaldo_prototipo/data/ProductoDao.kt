package com.example.campusmarket.data

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import kotlinx.coroutines.flow.Flow

@Dao
interface ProductoDao {
    // Flow: la interfaz se actualiza sola cada vez que cambia la tabla
    @Query("SELECT * FROM productos ORDER BY nombre")
    fun obtenerTodos(): Flow<List<Producto>>

    @Query("SELECT * FROM productos WHERE id = :id")
    fun obtenerPorId(id: Int): Flow<Producto?>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertar(producto: Producto)

    @Update
    suspend fun actualizar(producto: Producto)

    @Delete
    suspend fun eliminar(producto: Producto)
}
