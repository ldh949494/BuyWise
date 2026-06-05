package com.buywise.android

import android.content.Context
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
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
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.Modifier
import androidx.compose.ui.Alignment
import androidx.compose.ui.draw.clip
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
import com.buywise.android.ui.screens.AccountScreen
import com.buywise.android.ui.screens.GuideChatScreen
import com.buywise.android.ui.screens.GuideScreen
import com.buywise.android.ui.screens.HomeScreen
import com.buywise.android.ui.screens.LandingScreen
import com.buywise.android.ui.screens.ProductDetailScreen
import com.buywise.android.ui.screens.ProductSearchScreen
import com.buywise.android.ui.screens.VisionScreen
import com.buywise.android.viewmodel.BuyWiseViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

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

@Composable
private fun BuyWiseRoot(
    navController: NavHostController = rememberNavController(),
) {
    val context = LocalContext.current
    val viewModel: BuyWiseViewModel = viewModel(factory = BuyWiseViewModel.factory(context))
    val destinations = bottomDestinations()
    val currentRoute = navController.currentBackStackEntryAsState().value?.destination?.route
    val showBottomBar = currentRoute != null &&
        currentRoute != "landing" &&
        currentRoute != "search" &&
        currentRoute.startsWith("detail/") != true
    val showCompareBasket = currentRoute != null &&
        currentRoute != "landing" &&
        currentRoute != "search" &&
        currentRoute != "compare"
    val snackbarHostState = remember { SnackbarHostState() }
    val basketMessage = viewModel.compareBasketState.message
    val scope = rememberCoroutineScope()
    var multimodalTarget by remember { mutableStateOf(MultimodalTarget.VisionTab) }
    val imagePickerLauncher = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        if (uri == null) {
            return@rememberLauncherForActivityResult
        }
        scope.launch {
            val selectedImage = runCatching { withContext(Dispatchers.IO) { context.readSelectedImage(uri) } }.getOrNull()
            if (selectedImage == null) {
                snackbarHostState.showSnackbar("无法读取所选图片")
            } else {
                if (multimodalTarget == MultimodalTarget.GuideChat) {
                    viewModel.recognizeImageForGuideChat(
                        filename = selectedImage.filename,
                        contentType = selectedImage.contentType, bytes = selectedImage.bytes)
                } else {
                    viewModel.recognizeImage(
                        filename = selectedImage.filename,
                        contentType = selectedImage.contentType, bytes = selectedImage.bytes)
                }
            }
        }
    }
    val cameraLauncher = rememberLauncherForActivityResult(ActivityResultContracts.TakePicturePreview()) { bitmap ->
        if (bitmap == null) {
            return@rememberLauncherForActivityResult
        }
        if (multimodalTarget == MultimodalTarget.GuideChat) {
            viewModel.recognizeImageForGuideChat(
                filename = "camera-photo.png", contentType = "image/png", bytes = bitmap.toPngBytes())
        } else {
            viewModel.recognizeImage(
                filename = "camera-photo.png", contentType = "image/png", bytes = bitmap.toPngBytes())
        }
    }

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
                    modifier = Modifier
                        .padding(horizontal = 14.dp, vertical = 10.dp)
                        .clip(RoundedCornerShape(22.dp)),
                    containerColor = BuyWiseTheme.colors.panel,
                    tonalElevation = NavigationBarDefaults.Elevation,
                ) {
                    destinations.forEach { destination ->
                        NavigationBarItem(
                            selected = currentRoute == destination.route,
                            onClick = {
                                navController.navigateTopLevel(destination.route)
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
                .padding(padding),
        ) {
            NavHost(navController = navController, startDestination = "landing") {
                composable("landing") {
                    LandingScreen(
                        state = viewModel.accountState,
                        onPhoneChange = viewModel::updateAccountPhone,
                        onCodeChange = viewModel::updateAccountCode,
                        onRequestOtp = viewModel::requestAccountOtp,
                        onVerifyOtp = {
                            viewModel.verifyAccountOtp {
                                navController.navigateHomeFromLanding()
                            }
                        },
                        onGuestMode = {
                            viewModel.enterGuestMode {
                                navController.navigateHomeFromLanding()
                            }
                        },
                        onContinue = {
                            navController.navigateHomeFromLanding()
                        },
                    )
                }
                composable("home") {
                    HomeScreen(
                        state = viewModel.homeState,
                        onProductClick = { navController.navigate("detail/$it") },
                        isInCompareBasket = viewModel::isInCompareBasket,
                        onToggleCompare = { viewModel.toggleCompareBasket(it) },
                        onOpenSearch = { navController.navigate("search") },
                        onOpenGuide = { navController.navigateTopLevel("guide") },
                        onOpenCompare = { navController.navigateTopLevel("compare") },
                        onOpenVision = { navController.navigateTopLevel("vision") },
                        feedbackState = viewModel.feedbackState,
                        onToggleFeedbackForm = viewModel::toggleFeedbackForm,
                        onFeedbackDraftChange = viewModel::updateFeedbackDraft,
                        onSubmitFeedback = viewModel::submitFeedback,
                        onRetry = viewModel::loadHomeProducts,
                    )
                }
                composable("search") {
                    ProductSearchScreen(
                        products = viewModel.homeState.products,
                        onBack = navController::popBackStack,
                        onProductClick = { navController.navigate("detail/$it") },
                        isInCompareBasket = viewModel::isInCompareBasket,
                        onToggleCompare = { viewModel.toggleCompareBasket(it) },
                    )
                }
                composable("guide") {
                    GuideScreen(
                        state = viewModel.guideState,
                        onQueryChange = viewModel::updateGuideQuery,
                        onSubmit = viewModel::submitGuideQuery,
                        onOpenChat = {
                            viewModel.prepareGuideChatDraft()
                            navController.navigate("guide/chat")
                        },
                        onProductClick = { navController.navigate("detail/$it") },
                        isInCompareBasket = viewModel::isInCompareBasket,
                        onToggleCompare = viewModel::toggleCompareBasket,
                    )
                }
                composable("guide/chat") {
                    GuideChatScreen(
                        state = viewModel.guideState,
                        onBack = navController::popBackStack,
                        onDraftChange = viewModel::updateGuideChatDraft,
                        onSend = viewModel::sendGuideChatMessage,
                        onPickImage = {
                            multimodalTarget = MultimodalTarget.GuideChat
                            imagePickerLauncher.launch("image/*")
                        },
                        onTakePhoto = {
                            multimodalTarget = MultimodalTarget.GuideChat
                            cameraLauncher.launch(null)
                        },
                        onRunVisionDemo = viewModel::runVisionDemoForGuideChat,
                        onRunSpeechDemo = viewModel::runSpeechDemoForGuideChat,
                        onProductClick = { navController.navigate("detail/$it") },
                    )
                }
                composable("compare") {
                    CompareScreen(
                        state = viewModel.compareState,
                        onProductClick = { navController.navigate("detail/$it") },
                        onRefresh = viewModel::refreshCompare,
                        onOpenHome = { navController.navigateTopLevel("home") },
                        onOpenGuide = { navController.navigateTopLevel("guide") },
                    )
                }
                composable("vision") {
                    VisionScreen(
                        state = viewModel.visionState,
                        onTakePhoto = {
                            multimodalTarget = MultimodalTarget.VisionTab
                            cameraLauncher.launch(null)
                        },
                        onPickImage = {
                            multimodalTarget = MultimodalTarget.VisionTab
                            imagePickerLauncher.launch("image/*")
                        },
                        onRunVisionDemo = viewModel::runVisionDemo,
                        onRunSpeechDemo = viewModel::runSpeechDemo,
                        onUseQuery = {
                            viewModel.useVisionQueryInGuide()
                            navController.navigateTopLevel("guide")
                        },
                        onProductClick = { navController.navigate("detail/$it") },
                        isInCompareBasket = viewModel::isInCompareBasket,
                        onToggleCompare = { viewModel.toggleCompareBasket(it) },
                    )
                }
                composable("account") {
                    AccountScreen(
                        state = viewModel.accountState,
                        onPhoneChange = viewModel::updateAccountPhone,
                        onCodeChange = viewModel::updateAccountCode,
                        onRequestOtp = viewModel::requestAccountOtp,
                        onVerifyOtp = viewModel::verifyAccountOtp,
                        onGuestMode = { viewModel.enterGuestMode { navController.navigateTopLevel("home") } },
                        onLogout = viewModel::logoutAccount,
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
                            navController.navigateTopLevel("compare")
                        }
                    },
                    modifier = Modifier
                        .align(Alignment.BottomEnd)
                        .padding(end = 18.dp, bottom = 88.dp),
                )
            }
        }
    }
}

private fun NavHostController.navigateHomeFromLanding() {
    navigate("home") {
        popUpTo("landing") {
            inclusive = true
        }
        launchSingleTop = true
    }
}

private fun NavHostController.navigateTopLevel(route: String) {
    navigate(route) {
        popUpTo(graph.findStartDestination().id) {
            saveState = true
        }
        launchSingleTop = true
        restoreState = true
    }
}
