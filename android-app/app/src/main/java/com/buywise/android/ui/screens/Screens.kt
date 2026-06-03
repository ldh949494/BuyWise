package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.ShoppingBag
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.buywise.android.data.FeedbackDraft
import com.buywise.android.data.FeedbackPrompt
import com.buywise.android.data.FeedbackUiState
import com.buywise.android.data.HomeState
import com.buywise.android.data.Product
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.components.FloatingGlassCard
import com.buywise.android.ui.components.FloatingGlassTone
import com.buywise.android.ui.components.ProductCard
import com.buywise.android.ui.components.SectionTitle

@Composable
fun HomeScreen(
    state: HomeState,
    onProductClick: (String) -> Unit,
    isInCompareBasket: (String) -> Boolean,
    onToggleCompare: (Product) -> Unit,
    onOpenGuide: () -> Unit,
    onOpenCompare: () -> Unit,
    onOpenVision: () -> Unit,
    feedbackState: FeedbackUiState,
    onToggleFeedbackForm: (FeedbackPrompt) -> Unit,
    onFeedbackDraftChange: (FeedbackPrompt, FeedbackDraft) -> Unit,
    onSubmitFeedback: (FeedbackPrompt) -> Unit,
    onRetry: () -> Unit,
) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(18.dp),
        verticalArrangement = Arrangement.spacedBy(18.dp),
    ) {
        item {
            HeroPanel(
                title = state.heroTitle,
                subtitle = state.heroSubtitle,
                previewProducts = state.products.take(3),
                onOpenGuide = onOpenGuide,
            )
        }
        item {
            QuickEntryPanel(
                onOpenGuide = onOpenGuide,
                onOpenCompare = onOpenCompare,
                onOpenVision = onOpenVision,
            )
        }
        if (state.isLoading) {
            item { LinearProgressIndicator(modifier = Modifier.fillMaxWidth()) }
        }
        state.errorMessage?.let { message ->
            item {
                ErrorPanel(message = message, actionLabel = "重试", onAction = onRetry)
            }
        }
        if (!state.canUseFeedback) {
            item {
                InfoPanel(
                    icon = { Icon(Icons.Outlined.ShoppingBag, contentDescription = null) },
                    title = "购买后反馈",
                    body = state.tokenRequiredMessage ?: "购买后反馈功能暂未开启。",
                )
            }
        } else if (state.feedbackPrompts.isNotEmpty()) {
            item {
                SectionTitle("待评价", "收货后的真实反馈会进入商品分析")
            }
            feedbackState.successMessage?.let { message ->
                item { InfoPanel(icon = { Icon(Icons.Outlined.CheckCircle, contentDescription = null) }, title = "反馈", body = message) }
            }
            items(state.feedbackPrompts) { prompt ->
                FeedbackPromptCard(
                    prompt = prompt,
                    draft = feedbackState.draftFor(prompt),
                    expanded = feedbackState.activePromptId == prompt.orderItemId,
                    isSubmitting = prompt.orderItemId in feedbackState.submittingIds,
                    errorMessage = feedbackState.submitErrors[prompt.orderItemId],
                    canUseFeedback = feedbackState.canUseFeedback,
                    tokenRequiredMessage = feedbackState.tokenRequiredMessage,
                    onToggle = { onToggleFeedbackForm(prompt) },
                    onDraftChange = { onFeedbackDraftChange(prompt, it) },
                    onSubmit = { onSubmitFeedback(prompt) },
                )
            }
        }
        item {
            SectionTitle("精选商品", "为你精选的候选商品")
        }
        if (!state.isLoading && state.products.isEmpty() && state.errorMessage == null) {
            item { Text("暂无商品。", color = BuyWiseTheme.colors.muted) }
        }
        items(state.products) { product ->
            ProductCard(
                product = product,
                onClick = { onProductClick(product.id) },
                isInCompareBasket = isInCompareBasket(product.id),
                onToggleCompare = { onToggleCompare(product) },
            )
        }
    }
}

@Composable
fun InfoPanel(icon: @Composable () -> Unit, title: String, body: String) {
    FloatingGlassCard(tone = FloatingGlassTone.Success, contentPadding = 16.dp) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Surface(color = BuyWiseTheme.colors.secondarySoft, shape = RoundedCornerShape(8.dp), modifier = Modifier.size(40.dp)) {
                Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center) {
                    icon()
                }
            }
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text(title, style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
                Text(body, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
            }
        }
    }
}

@Composable
fun ErrorPanel(message: String, actionLabel: String? = null, onAction: (() -> Unit)? = null) {
    FloatingGlassCard(tone = FloatingGlassTone.Warm, contentPadding = 16.dp) {
        Column(modifier = Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text(message, color = BuyWiseTheme.colors.danger, style = MaterialTheme.typography.bodyMedium)
            if (actionLabel != null && onAction != null) {
                Button(onClick = onAction) {
                    Text(actionLabel)
                }
            }
        }
    }
}
