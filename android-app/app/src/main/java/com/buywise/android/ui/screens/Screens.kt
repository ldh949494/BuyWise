package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
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
import com.buywise.android.ui.components.ProductCard
import com.buywise.android.ui.components.SearchPill
import com.buywise.android.ui.components.SectionTitle
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
    onStartGuide: (String) -> Unit,
    onOpenCompare: () -> Unit,
    onOpenVision: () -> Unit,
    feedbackState: FeedbackUiState,
    onToggleFeedbackForm: (FeedbackPrompt) -> Unit,
    onFeedbackDraftChange: (FeedbackPrompt, FeedbackDraft) -> Unit,
    onSubmitFeedback: (FeedbackPrompt) -> Unit,
    onRetry: () -> Unit,
) {
    var selectedCategory by remember { mutableStateOf(HomeCategory.Dorm) }
    var guideDraft by remember { mutableStateOf("") }
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
            HomeGuideEntry(
                query = guideDraft,
                onQueryChange = { guideDraft = it },
                onStartGuide = { onStartGuide(guideDraft) },
            )
        }
        item {
            HomeCategoryRow(
                selectedCategory = selectedCategory,
                onCategorySelected = { selectedCategory = it },
            )
        }
        if (state.isLoading) {
            item { InlineLoadingNotice() }
        }
        state.errorMessage?.let { message ->
            item {
                ErrorPanel(message = message, actionLabel = "重试", onAction = onRetry)
            }
        }
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text("${selectedCategory.label}决策流", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
                Text("单列浏览", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.labelMedium)
            }
        }
        if (!state.isLoading && displayedProducts.isEmpty() && state.errorMessage == null) {
            item {
                EmptyActionPanel(
                    onRetry = onRetry,
                    onOpenGuide = onOpenGuide,
                )
            }
        }
        items(displayedProducts.take(12)) { product ->
            ProductCard(
                product = product,
                onClick = { onProductClick(product.id) },
                isInCompareBasket = isInCompareBasket(product.id),
                onToggleCompare = { onToggleCompare(product) },
            )
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
                SectionTitle("购买后反馈", "这件商品用下来怎么样")
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
private fun InlineLoadingNotice() {
    FloatingGlassCard(
        tone = FloatingGlassTone.Neutral,
        radius = 12.dp,
        contentPadding = 12.dp,
        elevated = false,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("正在更新商品列表", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
            LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
        }
    }
}

@Composable
private fun EmptyActionPanel(
    onRetry: () -> Unit,
    onOpenGuide: () -> Unit,
) {
    FloatingGlassCard(
        tone = FloatingGlassTone.Neutral,
        radius = 14.dp,
        contentPadding = 16.dp,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text("暂时没有匹配商品", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
            Text("可以刷新商品列表，或直接描述需求让 BuyWise 帮你找候选。", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                OutlinedButton(onClick = onRetry, modifier = Modifier.weight(1f)) {
                    Text("重试")
                }
                Button(onClick = onOpenGuide, modifier = Modifier.weight(1f)) {
                    Icon(BuyWiseIcons.Guide, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text("去导购")
                }
            }
        }
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
private fun HomeGuideEntry(
    query: String,
    onQueryChange: (String) -> Unit,
    onStartGuide: () -> Unit,
) {
    FloatingGlassCard(
        tone = FloatingGlassTone.Neutral,
        radius = 12.dp,
        elevated = false,
        contentPadding = 16.dp,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                FloatingAssetBadge(
                    icon = BuyWiseIcons.Assistant,
                    assetRes = BuyWiseVisualAssets.AssistantRobot,
                    contentDescription = null,
                    size = 48.dp,
                    iconSize = 40.dp,
                    tone = TactileIconTone.Primary,
                )
                Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text("说说预算、用途和偏好", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
                    Text("适合还没确定买哪一款时使用，BuyWise 会先给候选，再补理由。", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
                }
            }
            OutlinedTextField(
                value = query,
                onValueChange = onQueryChange,
                modifier = Modifier.fillMaxWidth(),
                minLines = 2,
                placeholder = { Text("例如：宿舍写代码，300以内，低噪音无线键盘") },
                shape = RoundedCornerShape(14.dp),
            )
            Text(
                if (query.isBlank()) "先描述需求，导购会自动进入结果页。" else "将带着这条需求进入导购页并自动生成。",
                color = BuyWiseTheme.colors.muted,
                style = MaterialTheme.typography.labelMedium,
            )
            Button(onClick = onStartGuide, enabled = query.isNotBlank(), modifier = Modifier.fillMaxWidth()) {
                Icon(BuyWiseIcons.Guide, contentDescription = null)
                Spacer(Modifier.width(8.dp))
                Text("开始导购")
            }
        }
    }
}

private enum class HomeCategory(
    val label: String,
    val keywords: List<String>,
    val icon: androidx.compose.ui.graphics.vector.ImageVector,
    val assetRes: Int? = null,
) {
    Dorm("宿舍", listOf("宿舍", "低噪", "键盘", "台灯", "收纳"), BuyWiseIcons.Keyboard, BuyWiseVisualAssets.Keyboard),
    Commute("通勤", listOf("通勤", "耳机", "降噪", "双肩包", "轻便"), BuyWiseIcons.Headphones, BuyWiseVisualAssets.Headphones),
    Office("办公", listOf("办公", "桌面", "显示器", "支架", "电脑"), BuyWiseIcons.Desktop),
    Travel("旅行", listOf("旅行", "充电宝", "便携", "续航", "防泼水"), BuyWiseIcons.Laptop),
    More("全部", emptyList(), BuyWiseIcons.More),
}

private fun List<Product>.forHomeCategory(category: HomeCategory): List<Product> {
    if (category == HomeCategory.More || category.keywords.isEmpty()) return this
    val filtered = filter { product ->
        val haystack = buildString {
            append(product.name).append(' ')
            append(product.brand.orEmpty()).append(' ')
            append(product.category.orEmpty()).append(' ')
            append(product.headline).append(' ')
            append(product.advantages.joinToString(" ")).append(' ')
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
