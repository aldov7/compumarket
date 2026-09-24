package com.example.campusmarket.navegacion

import androidx.compose.runtime.Composable
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.example.campusmarket.ui.PantallaDetalle
import com.example.campusmarket.ui.PantallaFormulario
import com.example.campusmarket.ui.PantallaPrincipal
import com.example.campusmarket.ui.ProductoViewModel

// Rutas centralizadas: evita errores de escritura en los textos de navegacion
object Rutas {
    const val ARG_ID = "id"
    const val PRINCIPAL = "principal"
    const val FORMULARIO = "formulario/{$ARG_ID}"
    const val DETALLE = "detalle/{$ARG_ID}"

    fun formulario(id: Int = 0) = "formulario/$id"   // id = 0 significa "producto nuevo"
    fun detalle(id: Int) = "detalle/$id"
}

@Composable
fun AppNavegacion() {
    val nav = rememberNavController()
    // El ViewModel vive mientras viva la Activity: sobrevive a la rotacion de pantalla
    val vm: ProductoViewModel = viewModel()

    NavHost(navController = nav, startDestination = Rutas.PRINCIPAL) {

        composable(Rutas.PRINCIPAL) {
            PantallaPrincipal(
                vm = vm,
                onAgregar = { nav.navigate(Rutas.formulario()) { launchSingleTop = true } },
                onDetalle = { id -> nav.navigate(Rutas.detalle(id)) { launchSingleTop = true } }
            )
        }

        composable(
            route = Rutas.FORMULARIO,
            arguments = listOf(navArgument(Rutas.ARG_ID) { type = NavType.IntType })
        ) { entry ->
            PantallaFormulario(
                vm = vm,
                productoId = entry.arguments?.getInt(Rutas.ARG_ID) ?: 0,
                onVolver = { nav.popBackStack() }
            )
        }

        composable(
            route = Rutas.DETALLE,
            arguments = listOf(navArgument(Rutas.ARG_ID) { type = NavType.IntType })
        ) { entry ->
            PantallaDetalle(
                vm = vm,
                productoId = entry.arguments?.getInt(Rutas.ARG_ID) ?: 0,
                onEditar = { id -> nav.navigate(Rutas.formulario(id)) { launchSingleTop = true } },
                onVolver = { nav.popBackStack() }
            )
        }
    }
}
