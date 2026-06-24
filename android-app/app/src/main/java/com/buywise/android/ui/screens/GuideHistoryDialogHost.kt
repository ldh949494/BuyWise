package com.buywise.android.ui.screens

import androidx.compose.runtime.Composable
import androidx.navigation.NavHostController
import com.buywise.android.viewmodel.BuyWiseViewModel

@Composable
fun GuideHistoryDialogHost(
    visible: Boolean,
    viewModel: BuyWiseViewModel,
    navController: NavHostController,
    onDismiss: () -> Unit,
) {
    if (!visible) return
    GuideSessionHistoryDialog(
        state = viewModel.guideState.sessionHistory,
        onDismiss = onDismiss,
        onOpenSession = { sessionId ->
            onDismiss()
            viewModel.openGuideSession(sessionId)
            navController.navigate("guide/chat")
        },
    )
}
