package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.AutoAwesome
import androidx.compose.material.icons.outlined.Search
import androidx.compose.material.icons.outlined.Tune
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.buywise.android.data.GuideState
import com.buywise.android.data.Product
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.components.ProductCard
import com.buywise.android.ui.components.SectionTitle

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
        item { SectionTitle("AI 导购工作台", "告诉我预算、用途和偏好，我帮你找到最适合的宿舍数码好物。") }
        item { GuideInputPanel(state = state, onQueryChange = onQueryChange, onSubmit = onSubmit) }
        guideStreamItems(state)
        item {
            DemandPanel(summary = state.intentSummary)
        }
        item { SectionTitle("推荐结果", "优先展示更贴近预算和场景的商品。") }
        if (!state.isStreaming && state.recommendations.isEmpty()) {
            item { Text("提交需求后显示后端推荐。", color = BuyWiseTheme.colors.muted) }
        }
        items(state.recommendations) { recommendation ->
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
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
        shape = RoundedCornerShape(8.dp),
        border = CardDefaults.outlinedCardBorder(),
    ) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
            Surface(color = BuyWiseTheme.colors.primarySoft, shape = RoundedCornerShape(8.dp)) {
                Text(
                    "一句话描述需求，BuyWise 会抽取预算、场景和偏好再推荐商品。",
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 9.dp),
                    color = BuyWiseTheme.colors.primary,
                    fontWeight = FontWeight.Bold,
                )
            }
            OutlinedTextField(
                value = state.query,
                onValueChange = onQueryChange,
                modifier = Modifier.fillMaxWidth(),
                minLines = 4,
                label = { Text("购物需求") },
                placeholder = { Text("例如：300 元以内，宿舍低噪，适合写代码的机械键盘") },
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
private fun DemandPanel(summary: String) {
    val chips = summary.intentChips()
    Card(
        colors = CardDefaults.cardColors(containerColor = BuyWiseTheme.colors.panel),
        shape = RoundedCornerShape(8.dp),
        border = CardDefaults.outlinedCardBorder(),
    ) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            androidx.compose.foundation.layout.Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Icon(Icons.Outlined.Tune, contentDescription = null, tint = BuyWiseTheme.colors.primary)
                Text("结构化需求画像", color = BuyWiseTheme.colors.ink, fontWeight = FontWeight.Bold)
            }
            if (chips.isEmpty()) {
                Text(summary.ifBlank { "提交需求后展示后端抽取出的预算、品类、场景和偏好。" }, color = BuyWiseTheme.colors.muted)
            } else {
                FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    chips.forEach { chip ->
                        AssistChip(
                            onClick = {},
                            label = { Text(chip, maxLines = 1, overflow = TextOverflow.Ellipsis) },
                        )
                    }
                }
                Text(summary, color = BuyWiseTheme.colors.muted)
            }
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

private fun String.intentChips(): List<String> {
    if (isBlank()) return emptyList()
    val candidates = split("，", ",", "；", ";", "\n")
        .map { it.trim().trim('-', ' ') }
        .filter { it.length in 2..18 }
    return candidates.take(6)
}
