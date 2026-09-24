package com.example.campusmarket.data

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

@Database(entities = [Producto::class], version = 2, exportSchema = false)
abstract class AppDatabase : RoomDatabase() {
    abstract fun productoDao(): ProductoDao

    companion object {
        @Volatile private var INSTANCE: AppDatabase? = null

        // Migracion 1 -> 2: agrega la columna de la foto sin perder los datos existentes
        private val MIGRACION_1_2 = object : Migration(1, 2) {
            override fun migrate(db: SupportSQLiteDatabase) {
                db.execSQL("ALTER TABLE productos ADD COLUMN imagenPath TEXT")
            }
        }

        fun getDatabase(context: Context): AppDatabase {
            val appContext = context.applicationContext
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: Room.databaseBuilder(appContext, AppDatabase::class.java, "campus_market.db")
                    .addMigrations(MIGRACION_1_2)
                    .addCallback(object : RoomDatabase.Callback() {
                        // Se ejecuta solo la primera vez que se crea la base de datos
                        override fun onCreate(db: SupportSQLiteDatabase) {
                            super.onCreate(db)
                            CoroutineScope(Dispatchers.IO).launch {
                                val dao = getDatabase(appContext).productoDao()
                                dao.insertar(Producto(nombre = "Cuaderno A4", descripcion = "Libreta de 100 hojas, tamaño A4.", categoria = "Útiles", precio = 12.50, stock = 20, disponible = true))
                                dao.insertar(Producto(nombre = "Lapicero azul", descripcion = "Lapicero de tinta azul.", categoria = "Útiles", precio = 2.50, stock = 50, disponible = true))
                                dao.insertar(Producto(nombre = "Botella reutilizable", descripcion = "Botella de acero inoxidable, 500 ml.", categoria = "Accesorios", precio = 18.00, stock = 12, disponible = true))
                                dao.insertar(Producto(nombre = "Mochila", descripcion = "Mochila resistente para laptop.", categoria = "Accesorios", precio = 65.00, stock = 8, disponible = true))
                                dao.insertar(Producto(nombre = "Memoria USB", descripcion = "Memoria USB de 64 GB.", categoria = "Tecnología", precio = 25.00, stock = 10, disponible = true))
                            }
                        }
                    })
                    .build()
                    .also { INSTANCE = it }
            }
        }
    }
}
