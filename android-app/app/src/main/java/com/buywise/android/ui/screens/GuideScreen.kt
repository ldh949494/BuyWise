package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.AutoAwesome
import androidx.compose.material.icons.outlined.Category
import androidx.compose.material.icons.outlined.Inventory2
import androidx.compose.material.icons.outlined.ShoppingBag
import androidx.compose.material.icons.outlined.Tune
import androidx.compose.material.icons.outlined.Wallet
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.buywise.android.data.GuideState
import com.buywise.android.data.Product
import com.buywise.android.ui.BuyWiseDimens
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.components.ProductCard
import com.buywise.android.ui.components.SectionTitle
import com.buywise.android.ui.components.SoftTag
import com.buywise.android.ui.displayPrice

@Composable
fun GuideScreen(
    state: GuideState,
    onQueryChange: (String) -> Unit,
    onSubmit: () -> Unit,
    onProductClick: (String) -> Unit,
    isInCompareBasket: (String) -> Boolean,
    onToggleCompare: (Product, String?) -> Unit,
) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(18.dp),
        verticalArrangement = Arrangement.spacedBy(18.dp),
    ) {
        item { WorkbenchHeader() }
        item { GuideInputPanel(state = state, onQueryChange = onQueryChange, onSubmit = onSubmit) }
        guideStreamItems(state)
        item { DemandPanel(query = state.query, summary = state.intentSummary) }
        item {
            SectionTitle(
                title = "推荐结果",
                subtitle = "基于你的需求，AI 为你精选了最合适的商品",
            )
        }
        if (!state.isStreaming && state.recommendations.isEmpty()) {
            item { RecommendationEmptyState() }
        }
        itemsIndexed(state.recommendations) { index, recommendation ->
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                if (index == 0) {
                    TopRecommendationStrip(recommendation.product)
                }
                ProductCard(
                    product = recommendation.product,
                    onClick = { onProductClick(recommendation.product.id) },
                    isInCompareBasket = isInCompareBasket(recommendation.product.id),
                    onToggleCompare = { onToggleCompare(recommendation.product, state.query) },
                    recommendationReason = recommendation.reason,
                )
            }
        }
    }
}

@Composable
private fun WorkbenchHeader() {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.weight(1f)) {
            Text("AI 导购工作台", style = MaterialTheme.typography.headlineMedium, color = BuyWiseTheme.colors.ink)
            Text(
                "告诉我预算、用途和偏好，我帮你找到最适合的宿舍数码好物。",
                color = BuyWiseTheme.colors.muted,
                style = MaterialTheme.typography.bodyMedium,
            )
        }
        Surface(
            color = BuyWiseTheme.colors.panel,
            shape = RoundedCornerShape(16.dp),
            shadowElevation = 4.dp,
            modifier = Modifier.size(58.dp),
        ) {
            Icon(
                Icons.Outlined.AutoAwesome,
                contentDescription = null,
                tint = BuyWiseTheme.colors.primary,
                modifier = Modifier.padding(15.dp),
            )
        }
    }
}

@Composable
private fun GuideInputPanel(state: GuideState, onQueryChange: (String) -> Unit, onSubmit: () -> Unit) {
    Card(
        colors = CardDefaults.cardColors(containerColor = BuyWiseTheme.colors.panel),
        shape = RoundedCornerShape(BuyWiseDimens.HeroRadius.dp),
        border = CardDefaults.outlinedCardBorder(),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
    ) {
        Column(modifier = Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
            Surface(color = BuyWiseTheme.colors.primarySoft, shape = RoundedCornerShape(16.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 14.dp),
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Icon(Icons.Outlined.AutoAwesome, contentDescription = null, tint = BuyWiseTheme.colors.primary)
                    Text(
                        "一句话描述需求，BuyWise 会提取预算、场景和偏好，再推荐商品。",
                        color = BuyWiseTheme.colors.primary,
                        fontWeight = FontWeight.Bold,
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
            }
            Text("购物需求", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
            OutlinedTextField(
                value = state.query,
                onValueChange = onQueryChange,
                modifier = Modifier.fillMaxWidth(),
                minLines = 4,
                placeholder = { Text("宿舍写代码用，预算300以内，想要低噪音机械键盘，最好便于收纳。") },
            )
            Button(
                onClick = onSubmit,
                modifier = Modifier.fillMaxWidth(),
                enabled = !state.isStreaming,
            ) {
                Icon(Icons.Outlined.AutoAwesome, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text(if (state.isStreaming) "生成中..." else "生成推荐")
            }
            FlowRow(horizontalArrangement = Arrangement.spacedBy(10.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                SoftTag("预算300内")
                SoftTag("宿舍场景")
                SoftTag("低噪音")
            }
        }
    }
}

@Composable
private fun DemandPanel(query: String, summary: String) {
    val profile = demandProfile(query = query, summary = summary)
    Card(
        colors = CardDefaults.cardColors(containerColor = BuyWiseTheme.colors.panel),
        shape = RoundedCornerShape(BuyWiseDimens.CardRadius.dp),
        border = CardDefaults.outlinedCardBorder(),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
    ) {
        Column(modifier = Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp), verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Outlined.Tune, contentDescription = null, tint = BuyWiseTheme.colors.primary)
                Text("结构化需求画像", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
                Spacer(modifier = Modifier.weight(1f))
                Text("AI 已提取", color = BuyWiseTheme.colors.primary, fontWeight = FontWeight.Bold)
            }
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {
                DemandTile("预算", profile.budget, Icons.Outlined.Wallet, Modifier.weight(1f))
                DemandTile("场景", profile.scene, Icons.Outlined.Inventory2, Modifier.weight(1f))
            }
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {
                DemandTile("偏好", profile.preference, Icons.Outlined.AutoAwesome, Modifier.weight(1f))
                DemandTile("品类", profile.category, Icons.Outlined.Category, Modifier.weight(1f))
            }
            if (summary.isNotBlank()) {
                Text(summary, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
            }
        }
    }
}

@Composable
private fun DemandTile(
    label: String,
    value: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    modifier: Modifier = Modifier,
) {
    Surface(
        color = BuyWiseTheme.colors.panel,
        shape = RoundedCornerShape(16.dp),
        border = CardDefaults.outlinedCardBorder(),
        modifier = modifier,
    ) {
        Row(
            modifier = Modifier.padding(14.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Surface(color = BuyWiseTheme.colors.primarySoft, shape = RoundedCornerShape(12.dp), modifier = Modifier.size(42.dp)) {
                Icon(icon, contentDescription = null, tint = BuyWiseTheme.colors.primary, modifier = Modifier.padding(10.dp))
            }
            Column(verticalArrangement = Arrangement.spacedBy(4.dp), modifier = Modifier.weight(1f)) {
                Text(label, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.labelMedium)
                Text(
                    value,
                    color = BuyWiseTheme.colors.ink,
                    fontWeight = FontWeight.Bold,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis,
                )
            }
        }
    }
}

@Composable
private fun RecommendationEmptyState() {
    Card(
        colors = CardDefaults.cardColors(containerColor = BuyWiseTheme.colors.panel),
        shape = RoundedCornerShape(BuyWiseDimens.CardRadius.dp),
        border = CardDefaults.outlinedCardBorder(),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(20.dp),
            horizontalArrangement = Arrangement.spacedBy(14.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Surface(color = BuyWiseTheme.colors.primarySoft, shape = RoundedCornerShape(14.dp), modifier = Modifier.size(52.dp)) {
                Icon(Icons.Outlined.ShoppingBag, contentDescription = null, tint = BuyWiseTheme.colors.primary, modifier = Modifier.padding(14.dp))
            }
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text("还没有推荐结果", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
                Text(
                    "输入预算、用途和偏好后，BuyWise 会生成候选商品和推荐理由。",
                    color = BuyWiseTheme.colors.muted,
                    style = MaterialTheme.typography.bodyMedium,
                )
            }
        }
    }
}

@Composable
private fun TopRecommendationStrip(product: Product) {
    Surface(color = BuyWiseTheme.colors.secondarySoft, shape = RoundedCornerShape(16.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(14.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text("优先推荐", color = BuyWiseTheme.colors.secondary, fontWeight = FontWeight.Bold)
                Text(product.name, color = BuyWiseTheme.colors.ink, maxLines = 1, overflow = TextOverflow.Ellipsis)
            }
            Text(product.price.displayPrice(), color = BuyWiseTheme.colors.primary, style = MaterialTheme.typography.titleMedium)
        }
    }
}

private fun androidx.compose.foundation.lazy.LazyListScope.guideStreamItems(state: GuideState) {
    if (state.isStreaming) {
        item { LinearProgressIndicator(modifier = Modifier.fillMaxWidth()) }
    }
    if (state.partialReply.isNotBlank()) {
        item {
            InfoPanel(
                icon = { Icon(Icons.Outlined.AutoAwesome, contentDescription = null) },
                title = "AI 推荐理由",
                body = state.partialReply,
            )
        }
    }
    if (state.errorMessage != null) {
        item {
            ErrorPanel(message = state.errorMessage)
        }
    }
}

private data class DemandProfile(val budget: String, val scene: String, val preference: String, val category: String)

private fun demandProfile(query: String, summary: String): DemandProfile {
    val text = "$query $summary"
    return DemandProfile(
        budget = Regex("""\d+\s*(元|以内|以下)?""").find(text)?.value?.replace(" ", "") ?: "待确认",
        scene = when {
            "宿舍" in text -> "宿舍 / 写代码"
            "通勤" in text -> "通勤"
            "办公" in text -> "办公"
            else -> "日常使用"
        },
        preference = listOfNotNull(
            "低噪音".takeIf { "低噪" in text || "静音" in text || "声音小" in text },
            "收纳友好".takeIf { "收纳" in text || "便携" in text },
            "预算友好".takeIf { "预算" in text || "以内" in text },
        ).joinToString(" / ").ifBlank { "实用优先" },
        category = when {
            "键盘" in text -> "机械键盘"
            "耳机" in text -> "耳机"
            "鼠标" in text -> "鼠标"
            else -> "数码商品"
        },
    )
}
