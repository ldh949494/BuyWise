package com.buywise.android.ui.screens

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.CompareArrows
import androidx.compose.material.icons.outlined.EmojiEvents
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.buywise.android.data.CompareRow
import com.buywise.android.data.CompareState
import com.buywise.android.data.Product
import com.buywise.android.ui.BuyWiseDimens
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.components.EvidenceTag
import com.buywise.android.ui.components.EvidenceTone
import com.buywise.android.ui.components.FloatingGlassCard
import com.buywise.android.ui.components.FloatingGlassTone
import com.buywise.android.ui.displayPrice
import com.buywise.android.ui.displayRating
import com.buywise.android.ui.shortName

@Composable
fun CompareDecisionCard(state: CompareState) {
    val winner = state.products.firstOrNull { it.id == state.winnerId }
        ?: state.products.minByOrNull { it.price ?: Double.MAX_VALUE }
    FloatingGlassCard(
        tone = FloatingGlassTone.Warm,
        radius = BuyWiseDimens.CardRadius.dp,
        contentPadding = 16.dp,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Icon(Icons.Outlined.EmojiEvents, contentDescription = null, tint = BuyWiseTheme.colors.accent)
                Text("AI 对比结论", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
            }
            Text(
                state.summary ?: "BuyWise 会优先比较价格、评分和明确的商品差异，帮助你缩小候选范围。",
                color = BuyWiseTheme.colors.muted,
                style = MaterialTheme.typography.bodyMedium,
            )
            winner?.let {
                FloatingGlassCard(tone = FloatingGlassTone.Success, elevated = false, contentPadding = 14.dp) {
                    EvidenceTag("优先推荐", tone = EvidenceTone.Success)
                    Text(it.name, color = BuyWiseTheme.colors.ink, style = MaterialTheme.typography.titleMedium)
                    Text(
                        "价格 ${it.price.displayPrice()}，评分 ${it.rating.displayRating()}。优先看它是否满足你的核心需求。",
                        color = BuyWiseTheme.colors.muted,
                        style = MaterialTheme.typography.bodyMedium,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis,
                    )
                }
            }
            if (winner == null) {
                Text("选择 2 个以上商品后，BuyWise 会结合价格、评分和场景适配生成决策建议。", color = BuyWiseTheme.colors.muted)
            }
        }
    }
}

@Composable
fun CompareTable(rows: List<CompareRow>, products: List<Product>) {
    FloatingGlassCard(
        tone = FloatingGlassTone.Neutral,
        radius = BuyWiseDimens.CardRadius.dp,
        contentPadding = 18.dp,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Icon(Icons.AutoMirrored.Outlined.CompareArrows, contentDescription = null, tint = BuyWiseTheme.colors.primary)
                Text("对比维度", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
            }
            if (products.isEmpty()) {
                Text("选择候选商品后，这里会展示横向对比维度。", color = BuyWiseTheme.colors.muted)
            } else {
                CompareMatrix(rows = rows, products = products)
            }
        }
    }
}

@Composable
private fun CompareMatrix(rows: List<CompareRow>, products: List<Product>) {
    val matrixRows = if (rows.isNotEmpty()) rows else products.defaultCompareRows()
    val cellWidth = 112.dp
    Row(modifier = Modifier.horizontalScroll(rememberScrollState())) {
        Column {
            TableCell("维度", width = 92.dp, isHeader = true)
            matrixRows.forEach { TableCell(it.title, width = 92.dp, isHeader = true) }
        }
        products.forEachIndexed { index, product ->
            Column {
                TableCell(product.shortName(), width = cellWidth, isHeader = true)
                matrixRows.forEach { row ->
                    TableCell(row.values.getOrNull(index) ?: "-", width = cellWidth)
                }
            }
        }
    }
}

@Composable
private fun TableCell(value: String, width: Dp, isHeader: Boolean = false) {
    Text(
        value,
        modifier = Modifier.width(width).padding(horizontal = 8.dp, vertical = 10.dp),
        color = if (isHeader) BuyWiseTheme.colors.ink else BuyWiseTheme.colors.muted,
        fontWeight = if (isHeader) FontWeight.Bold else FontWeight.Normal,
        style = MaterialTheme.typography.bodyMedium,
        maxLines = 2,
        overflow = TextOverflow.Ellipsis,
    )
    HorizontalDivider(color = BuyWiseTheme.colors.border)
}

private fun List<Product>.defaultCompareRows(): List<CompareRow> = listOf(
    CompareRow("价格", map { it.price.displayPrice() }),
    CompareRow("评分", map { it.rating.displayRating() }),
    CompareRow("推荐理由", map { it.headline.takeIf { headline -> headline.isNotBlank() } ?: "查看详情" }),
)
