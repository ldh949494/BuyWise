package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.ShoppingBag
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.buywise.android.data.FeedbackDraft
import com.buywise.android.data.FeedbackPrompt
import com.buywise.android.data.FeedbackUiState
import com.buywise.android.data.HomeState
import com.buywise.android.data.Product
import com.buywise.android.data.cleanMarkdownText
import com.buywise.android.ui.BuyWiseIcons
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.BuyWiseVisualAssets
import com.buywise.android.ui.components.CategoryShortcut
import com.buywise.android.ui.components.FloatingAssetBadge
import com.buywise.android.ui.components.FloatingGlassCard
import com.buywise.android.ui.components.FloatingGlassTone
import com.buywise.android.ui.components.SearchPill
import com.buywise.android.ui.components.SectionTitle
import com.buywise.android.ui.components.ShowcaseProductCard
import com.buywise.android.ui.components.TactileIconTile
import com.buywise.android.ui.components.TactileIconTone

@Composable
fun HomeScreen(
    state: HomeState,
    onProductClick: (String) -> Unit,
    isInCompareBasket: (String) -> Boolean,
    onToggleCompare: (Product) -> Unit,
    onOpenSearch: () -> Unit,
    onOpenGuide: () -> Unit,
    onOpenCompare: () -> Unit,
    onOpenVision: () -> Unit,
    feedbackState: FeedbackUiState,
    onToggleFeedbackForm: (FeedbackPrompt) -> Unit,
    onFeedbackDraftChange: (FeedbackPrompt, FeedbackDraft) -> Unit,
    onSubmitFeedback: (FeedbackPrompt) -> Unit,
    onRetry: () -> Unit,
) {
    var selectedCategory by remember { mutableStateOf(HomeCategory.Keyboard) }
    val displayedProducts = state.products.forHomeCategory(selectedCategory)
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(18.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item {
            HomeTopBar()
        }
        item {
            SearchPill(
                text = "搜索商品、品牌或功能",
                trailingIcon = BuyWiseIcons.Speech,
                onClick = onOpenSearch,
                onTrailingClick = onOpenGuide,
            )
        }
        item {
            HomeCategoryRow(
                selectedCategory = selectedCategory,
                onCategorySelected = { selectedCategory = it },
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
        item {
            HomeGreetingPanel(
                title = state.heroTitle,
                subtitle = state.heroSubtitle,
                onOpenGuide = onOpenGuide,
            )
        }
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text("${selectedCategory.label}推荐", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
                Text("全部", color = BuyWiseTheme.colors.primary, style = MaterialTheme.typography.labelMedium)
            }
        }
        if (!state.isLoading && displayedProducts.isEmpty() && state.errorMessage == null) {
            item { Text("暂无商品。", color = BuyWiseTheme.colors.muted) }
        }
        item {
            LazyRow(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                items(displayedProducts.take(8)) { product ->
                    ShowcaseProductCard(
                        product = product,
                        onClick = { onProductClick(product.id) },
                        modifier = Modifier.width(132.dp),
                        selected = isInCompareBasket(product.id),
                    )
                }
            }
        }
        if (!state.canUseFeedback) {
            item {
                InfoPanel(
                    icon = { Icon(BuyWiseIcons.Shopping, contentDescription = null) },
                    title = "购买后反馈",
                    body = state.tokenRequiredMessage ?: "购买后反馈功能暂未开启。",
                )
            }
        } else if (state.feedbackPrompts.isNotEmpty()) {
            item {
                SectionTitle("待评价", "记录真实使用体验")
            }
            feedbackState.successMessage?.let { message ->
                item { InfoPanel(icon = { Icon(BuyWiseIcons.CheckCircle, contentDescription = null) }, title = "反馈", body = message) }
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
            HomeFeedbackSummaryCard(
                productName = state.feedbackPrompts.firstOrNull()?.productName
                    ?: displayedProducts.firstOrNull()?.shortHomeName()
                    ?: "近期查看的商品",
            )
        }
    }
}

@Composable
private fun HomeTopBar() {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        TactileIconTile(
            icon = BuyWiseIcons.Menu,
            contentDescription = "菜单",
            size = 44.dp,
            iconSize = 22.dp,
            rounded = true,
            tone = TactileIconTone.Neutral,
        )
        Text("BuyWise", style = MaterialTheme.typography.titleLarge, color = BuyWiseTheme.colors.ink)
        TactileIconTile(
            icon = BuyWiseIcons.Notifications,
            contentDescription = "通知",
            size = 44.dp,
            iconSize = 22.dp,
            rounded = true,
            tone = TactileIconTone.Neutral,
        )
    }
}

@Composable
private fun HomeCategoryRow(
    selectedCategory: HomeCategory,
    onCategorySelected: (HomeCategory) -> Unit,
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.Top,
    ) {
        HomeCategory.entries.forEach { category ->
            CategoryShortcut(
                label = category.label,
                icon = category.icon,
                assetRes = category.assetRes,
                modifier = Modifier.weight(1f),
                tone = if (selectedCategory == category) TactileIconTone.Primary else TactileIconTone.Neutral,
                onClick = { onCategorySelected(category) },
            )
        }
    }
}

@Composable
private fun HomeGreetingPanel(title: String, subtitle: String, onOpenGuide: () -> Unit) {
    FloatingGlassCard(
        tone = FloatingGlassTone.Primary,
        radius = 16.dp,
        contentPadding = 16.dp,
        onClick = onOpenGuide,
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(5.dp)) {
                Text(title, style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
                Text(subtitle, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium, maxLines = 2)
            }
            FloatingAssetBadge(
                icon = BuyWiseIcons.Assistant,
                assetRes = BuyWiseVisualAssets.AssistantRobot,
                contentDescription = null,
                size = 64.dp,
                iconSize = 54.dp,
                tone = TactileIconTone.Primary,
            )
        }
    }
}

@Composable
private fun HomeFeedbackSummaryCard(productName: String) {
    FloatingGlassCard(
        tone = FloatingGlassTone.Primary,
        radius = 16.dp,
        contentPadding = 14.dp,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
                Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text("你的反馈待完成", color = BuyWiseTheme.colors.primary, style = MaterialTheme.typography.titleMedium)
                    Text(
                        "你最近查看了 $productName，使用体验如何？",
                        color = BuyWiseTheme.colors.ink,
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
                FloatingAssetBadge(
                    icon = BuyWiseIcons.Favorite,
                    assetRes = BuyWiseVisualAssets.Star,
                    contentDescription = null,
                    tone = TactileIconTone.Warm,
                    size = 50.dp,
                    iconSize = 38.dp,
                )
            }
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.fillMaxWidth()) {
                FeedbackActionButton("有帮助", BuyWiseIcons.ThumbsUp, modifier = Modifier.weight(1f))
                FeedbackActionButton("没帮助", BuyWiseIcons.ThumbsDown, modifier = Modifier.weight(1f))
            }
        }
    }
}

@Composable
private fun FeedbackActionButton(label: String, icon: androidx.compose.ui.graphics.vector.ImageVector, modifier: Modifier = Modifier) {
    FloatingGlassCard(
        modifier = modifier,
        tone = FloatingGlassTone.Neutral,
        radius = 12.dp,
        contentPadding = 10.dp,
        elevated = false,
    ) {
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
            Icon(icon, contentDescription = null, tint = BuyWiseTheme.colors.secondary, modifier = Modifier.size(18.dp))
            Text(label, color = BuyWiseTheme.colors.ink, style = MaterialTheme.typography.labelMedium)
        }
    }
}

private enum class HomeCategory(
    val label: String,
    val keywords: List<String>,
    val icon: androidx.compose.ui.graphics.vector.ImageVector,
    val assetRes: Int? = null,
) {
    Keyboard("键盘", listOf("键盘", "keyboard", "keychron", "switch"), BuyWiseIcons.Keyboard, BuyWiseVisualAssets.Keyboard),
    Audio("音频", listOf("音频", "耳机", "音箱", "audio", "headphone"), BuyWiseIcons.Headphones, BuyWiseVisualAssets.Headphones),
    Laptop("笔记本", listOf("笔记本", "电脑", "laptop", "notebook"), BuyWiseIcons.Laptop),
    Desk("桌面", listOf("桌", "支架", "显示器", "desk", "monitor"), BuyWiseIcons.Desktop),
    More("更多", emptyList(), BuyWiseIcons.More),
}

private fun List<Product>.forHomeCategory(category: HomeCategory): List<Product> {
    if (category == HomeCategory.More || category.keywords.isEmpty()) return this
    val filtered = filter { product ->
        val haystack = buildString {
            append(product.name).append(' ')
            append(product.brand.orEmpty()).append(' ')
            append(product.category.orEmpty()).append(' ')
            append(product.tags.joinToString(" "))
        }.lowercase()
        category.keywords.any { it.lowercase() in haystack }
    }
    return filtered.ifEmpty { this }
}

private fun Product.shortHomeName(): String =
    name.take(18).ifBlank { brand ?: "商品" }

@Composable
fun InfoPanel(icon: @Composable () -> Unit, title: String, body: String) {
    val displayBody = body.cleanMarkdownText().ifBlank { body }
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
                Text(displayBody, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
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
