package com.example.campusmarket.data

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase

@Database(entities = [Producto::class], version = 3, exportSchema = false)
abstract class AppDatabase : RoomDatabase() {
    abstract fun productoDao(): ProductoDao

    companion object {
        @Volatile private var INSTANCE: AppDatabase? = null

        // Productos de ejemplo (nombre, descripcion, categoria, precio, stock, disponible, imagen)
        private val PRODUCTOS_INICIALES = listOf(
            "('Cuaderno A4', 'Libreta de 100 hojas, tamaño A4.', 'Útiles', 12.50, 20, 1, 'res:prod_cuaderno')",
            "('Lapicero azul', 'Lapicero de tinta azul.', 'Útiles', 2.50, 50, 1, 'res:prod_lapicero')",
            "('Botella reutilizable', 'Botella de acero inoxidable, 500 ml.', 'Accesorios', 18.00, 12, 1, 'res:prod_botella')",
            "('Mochila', 'Mochila resistente para laptop.', 'Accesorios', 65.00, 8, 1, 'res:prod_mochila')",
            "('Memoria USB', 'Memoria USB de 64 GB.', 'Tecnología', 25.00, 10, 1, 'res:prod_usb')"
        )

        private val IMAGENES_INICIALES = mapOf(
            "Cuaderno A4" to "prod_cuaderno",
            "Lapicero azul" to "prod_lapicero",
            "Botella reutilizable" to "prod_botella",
            "Mochila" to "prod_mochila",
            "Memoria USB" to "prod_usb"
        )

        // Migracion 1 a 2: agrega la columna de la foto sin perder los datos existentes
        private val MIGRACION_1_2 = object : Migration(1, 2) {
            override fun migrate(db: SupportSQLiteDatabase) {
                db.execSQL("ALTER TABLE productos ADD COLUMN imagenPath TEXT")
            }
        }

        // Migracion 2 a 3: asigna las imagenes de ejemplo a los productos iniciales
        private val MIGRACION_2_3 = object : Migration(2, 3) {
            override fun migrate(db: SupportSQLiteDatabase) {
                IMAGENES_INICIALES.forEach { (nombre, recurso) ->
                    db.execSQL(
                        "UPDATE productos SET imagenPath = 'res:$recurso' WHERE nombre = '$nombre' AND imagenPath IS NULL"
                    )
                }
            }
        }

        fun getDatabase(context: Context): AppDatabase {
            val appContext = context.applicationContext
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: Room.databaseBuilder(appContext, AppDatabase::class.java, "campus_market.db")
                    .addMigrations(MIGRACION_1_2, MIGRACION_2_3)
                    .addCallback(object : RoomDatabase.Callback() {
                        // Se ejecuta solo la primera vez que se crea la base de datos
                        override fun onCreate(db: SupportSQLiteDatabase) {
                            super.onCreate(db)
                            PRODUCTOS_INICIALES.forEach { valores ->
                                db.execSQL(
                                    "INSERT INTO productos (nombre, descripcion, categoria, precio, stock, disponible, imagenPath) VALUES $valores"
                                )
                            }
                        }
                    })
                    .build()
                    .also { INSTANCE = it }
            }
        }
    }
}
