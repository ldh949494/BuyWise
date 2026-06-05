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
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
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
import com.buywise.android.data.Product
import com.buywise.android.ui.BuyWiseIcons
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.components.FloatingAssetBadge
import com.buywise.android.ui.components.FloatingGlassCard
import com.buywise.android.ui.components.FloatingGlassTone
import com.buywise.android.ui.components.ProductCard
import com.buywise.android.ui.components.SoftTag
import com.buywise.android.ui.components.TactileIconTile
import com.buywise.android.ui.components.TactileIconTone

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
        when {
            products.isEmpty() -> item {
                InfoPanel(
                    icon = { Icon(BuyWiseIcons.Inventory, contentDescription = null) },
                    title = "暂无商品数据",
                    body = "商品列表加载后，这里会展示搜索结果。",
                )
            }
            results.isEmpty() -> item {
                InfoPanel(
                    icon = { Icon(BuyWiseIcons.Search, contentDescription = null) },
                    title = "没有找到相关商品",
                    body = "换一个商品名、品牌或功能关键词再试。",
                )
            }
            else -> items(results, key = { it.id }) { product ->
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
