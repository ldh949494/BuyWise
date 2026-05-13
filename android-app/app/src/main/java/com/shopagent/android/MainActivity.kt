package com.shopagent.android

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.CompareArrows
import androidx.compose.material.icons.outlined.Home
import androidx.compose.material.icons.outlined.ImageSearch
import androidx.compose.material.icons.outlined.SmartToy
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.shopagent.android.ui.ShopAgentTheme
import com.shopagent.android.ui.screens.CompareScreen
import com.shopagent.android.ui.screens.GuideScreen
import com.shopagent.android.ui.screens.HomeScreen
import com.shopagent.android.ui.screens.ProductDetailScreen
import com.shopagent.android.ui.screens.VisionScreen
import com.shopagent.android.viewmodel.ShopAgentViewModel

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            ShopAgentTheme {
                ShopAgentRoot()
            }
        }
    }
}

private data class BottomDestination(
    val route: String,
    val label: String,
    val icon: @Composable () -> Unit,
)

@Composable
private fun ShopAgentRoot(
    navController: NavHostController = rememberNavController(),
    viewModel: ShopAgentViewModel = viewModel(),
) {
    val destinations = listOf(
        BottomDestination("home", "首页") { Icon(Icons.Outlined.Home, contentDescription = null) },
        BottomDestination("guide", "导购") { Icon(Icons.Outlined.SmartToy, contentDescription = null) },
        BottomDestination("compare", "对比") { Icon(Icons.AutoMirrored.Outlined.CompareArrows, contentDescription = null) },
        BottomDestination("vision", "识图") { Icon(Icons.Outlined.ImageSearch, contentDescription = null) },
    )
    val currentRoute = navController.currentBackStackEntryAsState().value?.destination?.route
    val showBottomBar = currentRoute?.startsWith("detail/") != true

    Scaffold(
        bottomBar = {
            if (showBottomBar) {
                NavigationBar {
                    destinations.forEach { destination ->
                        NavigationBarItem(
                            selected = currentRoute == destination.route,
                            onClick = {
                                navController.navigate(destination.route) {
                                    popUpTo(navController.graph.findStartDestination().id) {
                                        saveState = true
                                    }
                                    launchSingleTop = true
                                    restoreState = true
                                }
                            },
                            icon = destination.icon,
                            label = { Text(destination.label) },
                        )
                    }
                }
            }
        },
    ) { padding ->
        Box(
            modifier = Modifier
                .background(ShopAgentTheme.colors.surface)
                .padding(PaddingValues(bottom = padding.calculateBottomPadding())),
        ) {
            NavHost(navController = navController, startDestination = "home") {
                composable("home") {
                    HomeScreen(
                        state = viewModel.homeState,
                        onProductClick = { navController.navigate("detail/$it") },
                        onOpenGuide = { navController.navigate("guide") },
                    )
                }
                composable("guide") {
                    GuideScreen(
                        state = viewModel.guideState,
                        onQueryChange = viewModel::updateGuideQuery,
                        onSubmit = viewModel::submitGuideQuery,
                        onProductClick = { navController.navigate("detail/$it") },
                    )
                }
                composable("compare") {
                    CompareScreen(
                        state = viewModel.compareState,
                        onProductClick = { navController.navigate("detail/$it") },
                    )
                }
                composable("vision") {
                    VisionScreen(
                        state = viewModel.visionState,
                        onProductClick = { navController.navigate("detail/$it") },
                    )
                }
                composable("detail/{productId}") { backStackEntry ->
                    ProductDetailScreen(
                        product = viewModel.product(backStackEntry.arguments?.getString("productId")),
                        onBack = navController::popBackStack,
                    )
                }
            }
        }
    }
}
