package com.buywise.android

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.CompareArrows
import androidx.compose.material.icons.outlined.Home
import androidx.compose.material.icons.outlined.ImageSearch
import androidx.compose.material.icons.outlined.SmartToy
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarDefaults
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.Alignment
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.components.FloatingCompareBasket
import com.buywise.android.ui.screens.CompareScreen
import com.buywise.android.ui.screens.GuideScreen
import com.buywise.android.ui.screens.HomeScreen
import com.buywise.android.ui.screens.ProductDetailScreen
import com.buywise.android.ui.screens.VisionScreen
import com.buywise.android.viewmodel.BuyWiseViewModel

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            BuyWiseTheme {
                BuyWiseRoot()
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
private fun BuyWiseRoot(
    navController: NavHostController = rememberNavController(),
    viewModel: BuyWiseViewModel = viewModel(),
) {
    val destinations = listOf(
        BottomDestination("home", "首页") { Icon(Icons.Outlined.Home, contentDescription = null) },
        BottomDestination("guide", "导购") { Icon(Icons.Outlined.SmartToy, contentDescription = null) },
        BottomDestination("compare", "对比") { Icon(Icons.AutoMirrored.Outlined.CompareArrows, contentDescription = null) },
        BottomDestination("vision", "识图") { Icon(Icons.Outlined.ImageSearch, contentDescription = null) },
    )
    val currentRoute = navController.currentBackStackEntryAsState().value?.destination?.route
    val showBottomBar = currentRoute?.startsWith("detail/") != true
    val showCompareBasket = currentRoute != "compare"
    val snackbarHostState = remember { SnackbarHostState() }
    val basketMessage = viewModel.compareBasketState.message

    LaunchedEffect(basketMessage) {
        if (basketMessage != null) {
            snackbarHostState.showSnackbar(basketMessage)
            viewModel.clearCompareBasketMessage()
        }
    }

    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) },
        bottomBar = {
            if (showBottomBar) {
                NavigationBar(
                    containerColor = BuyWiseTheme.colors.panel,
                    tonalElevation = NavigationBarDefaults.Elevation,
                ) {
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
                            colors = NavigationBarItemDefaults.colors(
                                selectedIconColor = BuyWiseTheme.colors.primary,
                                selectedTextColor = BuyWiseTheme.colors.primary,
                                indicatorColor = BuyWiseTheme.colors.primarySoft,
                                unselectedIconColor = BuyWiseTheme.colors.muted,
                                unselectedTextColor = BuyWiseTheme.colors.muted,
                            ),
                        )
                    }
                }
            }
        },
    ) { padding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(BuyWiseTheme.colors.surface)
                .padding(PaddingValues(bottom = padding.calculateBottomPadding())),
        ) {
            NavHost(navController = navController, startDestination = "home") {
                composable("home") {
                    HomeScreen(
                        state = viewModel.homeState,
                        onProductClick = { navController.navigate("detail/$it") },
                        isInCompareBasket = viewModel::isInCompareBasket,
                        onToggleCompare = { viewModel.toggleCompareBasket(it) },
                        onOpenGuide = { navController.navigate("guide") },
                        onSubmitFeedback = viewModel::submitFeedback,
                        onRetry = viewModel::loadHomeProducts,
                    )
                }
                composable("guide") {
                    GuideScreen(
                        state = viewModel.guideState,
                        onQueryChange = viewModel::updateGuideQuery,
                        onSubmit = viewModel::submitGuideQuery,
                        onProductClick = { navController.navigate("detail/$it") },
                        isInCompareBasket = viewModel::isInCompareBasket,
                        onToggleCompare = viewModel::toggleCompareBasket,
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
                        onRunVisionDemo = viewModel::runVisionDemo,
                        onRunSpeechDemo = viewModel::runSpeechDemo,
                        onUseQuery = {
                            viewModel.useVisionQueryInGuide()
                            navController.navigate("guide")
                        },
                        onProductClick = { navController.navigate("detail/$it") },
                        isInCompareBasket = viewModel::isInCompareBasket,
                        onToggleCompare = { viewModel.toggleCompareBasket(it) },
                    )
                }
                composable("detail/{productId}") { backStackEntry ->
                    val productId = backStackEntry.arguments?.getString("productId")
                    LaunchedEffect(productId) {
                        viewModel.loadProductDetail(productId)
                    }
                    ProductDetailScreen(
                        state = viewModel.productDetailState,
                        fallbackProduct = viewModel.product(productId),
                        onBack = navController::popBackStack,
                        isInCompareBasket = viewModel::isInCompareBasket,
                        onToggleCompare = { viewModel.toggleCompareBasket(it) },
                        onRecordPurchase = viewModel::recordPurchase,
                    )
                }
            }
            if (showCompareBasket) {
                FloatingCompareBasket(
                    state = viewModel.compareBasketState,
                    onExpandedChange = viewModel::setCompareBasketExpanded,
                    onRemoveProduct = { viewModel.toggleCompareBasket(it) },
                    onClear = viewModel::clearCompareBasket,
                    onStartCompare = {
                        if (viewModel.startCompareFromBasket()) {
                            navController.navigate("compare") {
                                launchSingleTop = true
                            }
                        }
                    },
                    modifier = Modifier
                        .align(Alignment.BottomEnd)
                        .padding(18.dp),
                )
            }
        }
    }
}
