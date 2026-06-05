package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
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
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.unit.dp
import com.buywise.android.data.FeedbackDraft
import com.buywise.android.data.FeedbackPrompt
import com.buywise.android.data.FeedbackUiState
import com.buywise.android.data.HomeState
import com.buywise.android.data.Product
import com.buywise.android.data.cleanMarkdownText
import com.buywise.android.ui.BuyWiseIcons
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.components.CategoryShortcut
import com.buywise.android.ui.components.FloatingAssetBadge
import com.buywise.android.ui.components.FloatingGlassCard
import com.buywise.android.ui.components.FloatingGlassTone
import com.buywise.android.ui.components.ProductCard
import com.buywise.android.ui.components.SearchPill
import com.buywise.android.ui.components.SectionTitle
import com.buywise.android.ui.components.ShowcaseProductCard
import com.buywise.android.ui.components.SoftTag
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
fun ProductSearchScreen(
    products: List<Product>,
    onBack: () -> Unit,
    onProductClick: (String) -> Unit,
    isInCompareBasket: (String) -> Boolean,
    onToggleCompare: (Product) -> Unit,
) {
    var query by remember { mutableStateOf("") }
    val normalizedQuery = query.trim()
    val results = remember(normalizedQuery, products) {
        if (normalizedQuery.isBlank()) {
            products.sortedByDescending { it.recommendationScore ?: it.rating ?: 0.0 }.take(10)
        } else {
            products.searchProducts(normalizedQuery)
        }
    }
    val resultTitle = if (normalizedQuery.isBlank()) "热门商品" else "搜索结果"
    val resultSubtitle = if (normalizedQuery.isBlank()) "输入商品、品牌或功能关键词开始搜索。" else "找到 ${results.size} 个相关商品。"

    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(18.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        item {
            ProductSearchTopBar(
                query = query,
                onQueryChange = { query = it },
                onBack = onBack,
                onClear = { query = "" },
            )
        }
        item {
            SearchResultSummaryCard(
                title = resultTitle,
                subtitle = resultSubtitle,
                query = normalizedQuery,
                resultCount = results.size,
            )
        }
        if (products.isEmpty()) {
            item {
                InfoPanel(
                    icon = { Icon(BuyWiseIcons.Inventory, contentDescription = null) },
                    title = "暂无商品数据",
                    body = "商品列表加载后，这里会展示搜索结果。",
                )
            }
        } else if (results.isEmpty()) {
            item {
                InfoPanel(
                    icon = { Icon(BuyWiseIcons.Search, contentDescription = null) },
                    title = "没有找到相关商品",
                    body = "换一个商品名、品牌或功能关键词再试。",
                )
            }
        } else {
            items(results, key = { it.id }) { product ->
                ProductCard(
                    product = product,
                    onClick = { onProductClick(product.id) },
                    isInCompareBasket = isInCompareBasket(product.id),
                    onToggleCompare = { onToggleCompare(product) },
                )
            }
        }
    }
}

@Composable
private fun ProductSearchTopBar(
    query: String,
    onQueryChange: (String) -> Unit,
    onBack: () -> Unit,
    onClear: () -> Unit,
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        TactileIconTile(
            icon = BuyWiseIcons.Back,
            contentDescription = "返回",
            size = 42.dp,
            iconSize = 22.dp,
            rounded = true,
            tone = TactileIconTone.Neutral,
            onClick = onBack,
        )
        FloatingGlassCard(
            modifier = Modifier.weight(1f),
            tone = FloatingGlassTone.Neutral,
            radius = 999.dp,
            contentPadding = 0.dp,
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(min = 52.dp)
                    .padding(start = 14.dp, top = 8.dp, end = 8.dp, bottom = 8.dp),
                horizontalArrangement = Arrangement.spacedBy(10.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Icon(BuyWiseIcons.Search, contentDescription = null, tint = BuyWiseTheme.colors.primary)
                BasicTextField(
                    value = query,
                    onValueChange = onQueryChange,
                    modifier = Modifier.weight(1f),
                    singleLine = true,
                    textStyle = MaterialTheme.typography.bodyMedium.copy(color = BuyWiseTheme.colors.ink),
                    cursorBrush = SolidColor(BuyWiseTheme.colors.primary),
                    decorationBox = { innerTextField ->
                        if (query.isBlank()) {
                            Text(
                                "搜索商品、品牌或功能",
                                color = BuyWiseTheme.colors.muted,
                                style = MaterialTheme.typography.bodyMedium,
                                maxLines = 1,
                            )
                        }
                        innerTextField()
                    },
                )
                TactileIconTile(
                    icon = BuyWiseIcons.Close,
                    contentDescription = "清除",
                    size = 36.dp,
                    iconSize = 18.dp,
                    rounded = true,
                    tone = TactileIconTone.Neutral,
                    enabled = query.isNotBlank(),
                    onClick = onClear,
                )
            }
        }
    }
}

@Composable
private fun SearchResultSummaryCard(
    title: String,
    subtitle: String,
    query: String,
    resultCount: Int,
) {
    FloatingGlassCard(tone = FloatingGlassTone.Primary, radius = 16.dp, contentPadding = 14.dp, elevated = false) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            FloatingAssetBadge(
                icon = BuyWiseIcons.Search,
                contentDescription = null,
                size = 44.dp,
                iconSize = 22.dp,
                tone = TactileIconTone.Primary,
            )
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text(title, style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
                Text(subtitle, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
                FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    if (query.isNotBlank()) {
                        SoftTag(query)
                    }
                    SoftTag("${resultCount} 个商品")
                }
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
                contentDescription = null,
                size = 64.dp,
                iconSize = 34.dp,
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
                    contentDescription = null,
                    tone = TactileIconTone.Warm,
                    size = 50.dp,
                    iconSize = 26.dp,
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
) {
    Keyboard("键盘", listOf("键盘", "keyboard", "keychron", "switch"), BuyWiseIcons.Keyboard),
    Audio("音频", listOf("音频", "耳机", "音箱", "audio", "headphone"), BuyWiseIcons.Headphones),
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

private fun List<Product>.searchProducts(query: String): List<Product> {
    val terms = query.lowercase().split(Regex("""\s+""")).filter { it.isNotBlank() }
    if (terms.isEmpty()) return emptyList()
    return mapNotNull { product ->
        val haystack = product.searchText()
        val score = terms.sumOf { term -> product.matchScore(term, haystack) }
        product.takeIf { score > 0 }?.let { it to score }
    }.sortedWith(
        compareByDescending<Pair<Product, Int>> { it.second }
            .thenByDescending { it.first.recommendationScore ?: it.first.rating ?: 0.0 },
    ).map { it.first }
}

private fun Product.searchText(): String =
    buildString {
        append(name).append(' ')
        append(brand.orEmpty()).append(' ')
        append(category.orEmpty()).append(' ')
        append(headline).append(' ')
        append(tags.joinToString(" ")).append(' ')
        append(advantages.joinToString(" ")).append(' ')
        append(cautions.joinToString(" "))
    }.lowercase()

private fun Product.matchScore(term: String, haystack: String): Int {
    val nameText = name.lowercase()
    val brandText = brand.orEmpty().lowercase()
    val categoryText = category.orEmpty().lowercase()
    return when {
        nameText == term -> 80
        nameText.startsWith(term) -> 60
        brandText == term -> 50
        categoryText == term -> 42
        term in nameText -> 36
        term in brandText -> 28
        term in categoryText -> 24
        tags.any { term in it.lowercase() } -> 20
        term in haystack -> 10
        else -> 0
    }
}

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
