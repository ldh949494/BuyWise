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
import androidx.compose.material.icons.outlined.Search
import androidx.compose.material.icons.outlined.ShoppingBag
import androidx.compose.material.icons.outlined.Tune
import androidx.compose.material3.AssistChip
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
import com.buywise.android.ui.displayMatchPercent
import com.buywise.android.ui.displayPrice
import com.buywise.android.ui.components.ProductCard
import com.buywise.android.ui.components.SectionTitle
import com.buywise.android.ui.components.SoftTag

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
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item { SectionTitle("AI 导购工作台", "一句话说出你的购物需求") }
        item { GuideInputPanel(state = state, onQueryChange = onQueryChange, onSubmit = onSubmit) }
        guideStreamItems(state)
        item {
            DemandPanel(query = state.query, summary = state.intentSummary)
        }
        item { SectionTitle("推荐结果", "优先展示更贴近预算和场景的商品。") }
        if (!state.isStreaming && state.recommendations.isEmpty()) {
            item { RecommendationEmptyState() }
        }
        itemsIndexed(state.recommendations) { index, recommendation ->
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
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
private fun GuideInputPanel(state: GuideState, onQueryChange: (String) -> Unit, onSubmit: () -> Unit) {
    Card(
        colors = CardDefaults.cardColors(containerColor = BuyWiseTheme.colors.panel),
        shape = RoundedCornerShape(BuyWiseDimens.CardRadius.dp),
        border = CardDefaults.outlinedCardBorder(),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
    ) {
        Column(modifier = Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
            Surface(color = BuyWiseTheme.colors.primarySoft, shape = RoundedCornerShape(12.dp)) {
                Text(
                    "试试这样说：宿舍用机械键盘，预算300以内，声音小，适合写代码",
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 9.dp),
                    color = BuyWiseTheme.colors.primary,
                    fontWeight = FontWeight.Bold,
                )
            }
            OutlinedTextField(
                value = state.query,
                onValueChange = onQueryChange,
                modifier = Modifier.fillMaxWidth(),
                minLines = 3,
                label = { Text("购物需求") },
                placeholder = { Text("例如：我想买一个宿舍用的机械键盘，预算300以内，声音小一点") },
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
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
    ) {
        Column(modifier = Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Outlined.Tune, contentDescription = null, tint = BuyWiseTheme.colors.primary)
                Text("结构化需求画像", color = BuyWiseTheme.colors.ink, fontWeight = FontWeight.Bold)
            }
            FlowRow(horizontalArrangement = Arrangement.spacedBy(10.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                DemandChip("预算", profile.budget)
                DemandChip("场景", profile.scene)
                DemandChip("偏好", profile.preference)
                DemandChip("品类", profile.category)
            }
            if (summary.isNotBlank()) {
                Text(summary, color = BuyWiseTheme.colors.muted)
            }
        }
    }
}

@Composable
private fun DemandChip(label: String, value: String) {
    Column(
        modifier = Modifier
            .fillMaxWidth(0.47f)
            .padding(0.dp),
        verticalArrangement = Arrangement.spacedBy(4.dp),
    ) {
        Text(label, color = BuyWiseTheme.colors.primary, style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.Bold)
        SoftTag(value)
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
                Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center) {
                    Icon(Icons.Outlined.ShoppingBag, contentDescription = null, tint = BuyWiseTheme.colors.primary)
                }
            }
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text("还没有推荐结果", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
                Text(
                    "输入你的预算、用途和偏好后，BuyWise 会为你生成 3 款候选商品，并给出推荐理由。",
                    color = BuyWiseTheme.colors.muted,
                    style = MaterialTheme.typography.bodyMedium,
                )
            }
        }
    }
}

@Composable
private fun TopRecommendationStrip(product: Product) {
    Surface(color = BuyWiseTheme.colors.secondarySoft, shape = RoundedCornerShape(14.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text("最推荐", color = BuyWiseTheme.colors.secondary, fontWeight = FontWeight.Bold)
                Text(product.name, color = BuyWiseTheme.colors.ink, maxLines = 1, overflow = TextOverflow.Ellipsis)
            }
            Text("${product.price.displayPrice()}  匹配度 ${product.displayMatchPercent()}", color = BuyWiseTheme.colors.primary, fontWeight = FontWeight.Bold)
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
                title = "BuyWise",
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
            "宿舍" in text -> "宿舍"
            "通勤" in text -> "通勤"
            "办公" in text -> "办公"
            else -> "日常使用"
        },
        preference = listOfNotNull(
            "低噪音".takeIf { "低噪" in text || "静音" in text || "声音小" in text },
            "写代码".takeIf { "代码" in text || "编程" in text },
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
