package com.buywise.android.ui.screens

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.CompareArrows
import androidx.compose.material.icons.outlined.EmojiEvents
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.buywise.android.data.CompareRow
import com.buywise.android.data.CompareState
import com.buywise.android.data.Product
import com.buywise.android.ui.BuyWiseDimens
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.components.SoftTag
import com.buywise.android.ui.displayMatchPercent
import com.buywise.android.ui.displayPrice
import com.buywise.android.ui.displayRating
import com.buywise.android.ui.fitLevel
import com.buywise.android.ui.noiseLevel
import com.buywise.android.ui.shortName

@Composable
fun CompareDecisionCard(state: CompareState) {
    val winner = state.products.firstOrNull { it.id == state.winnerId }
        ?: state.products.maxByOrNull { it.matchPercent() }
    var showReason by remember { mutableStateOf(false) }
    Card(
        colors = CardDefaults.cardColors(containerColor = BuyWiseTheme.colors.panel),
        shape = RoundedCornerShape(BuyWiseDimens.CardRadius.dp),
        border = CardDefaults.outlinedCardBorder(),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
    ) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Icon(Icons.Outlined.EmojiEvents, contentDescription = null, tint = BuyWiseTheme.colors.accent)
                Text("AI 对比结论", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
            }
            Text("AI 对比结论", color = BuyWiseTheme.colors.primary, fontWeight = FontWeight.Bold)
            winner?.let {
                Surface(color = BuyWiseTheme.colors.secondarySoft, shape = RoundedCornerShape(14.dp)) {
                    Column(modifier = Modifier.fillMaxWidth().padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Text("优先推荐 ${it.name}", color = BuyWiseTheme.colors.ink, fontWeight = FontWeight.Bold)
                        Text(
                            "原因：价格、评分和宿舍静音场景匹配度更高。",
                            color = BuyWiseTheme.colors.muted,
                            style = MaterialTheme.typography.bodyMedium,
                            maxLines = 2,
                            overflow = TextOverflow.Ellipsis,
                        )
                    }
                }
                CompareSummaryChips(products = state.products, winner = it)
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    Button(onClick = { showReason = false }) { Text("选择这款") }
                    FilledTonalButton(onClick = { showReason = !showReason }) { Text("生成购买理由") }
                }
                if (showReason) {
                    Text(
                        "购买理由：${it.name} 的价格为 ${it.price.displayPrice()}，AI 匹配度 ${it.displayMatchPercent()}，更贴近当前预算和使用场景。",
                        color = BuyWiseTheme.colors.muted,
                        style = MaterialTheme.typography.bodyMedium,
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
private fun CompareSummaryChips(products: List<Product>, winner: Product) {
    val cheapest = products.minByOrNull { it.price ?: Double.MAX_VALUE } ?: winner
    val topRated = products.maxByOrNull { it.rating ?: -1.0 } ?: winner
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        SoftTag("价格最优：${cheapest.shortName()}")
        SoftTag("评分最高：${topRated.shortName()}")
        SoftTag("场景适配：${winner.shortName()}")
    }
}

@Composable
fun CompareTable(rows: List<CompareRow>, products: List<Product>) {
    Card(
        colors = CardDefaults.cardColors(containerColor = BuyWiseTheme.colors.panel),
        shape = RoundedCornerShape(BuyWiseDimens.CardRadius.dp),
        border = CardDefaults.outlinedCardBorder(),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
    ) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
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
    CompareRow("AI 匹配度", map { it.displayMatchPercent() }),
    CompareRow("宿舍适配", map { it.fitLevel() }),
    CompareRow("低噪表现", map { it.noiseLevel() }),
)

private fun Product.matchPercent(): Int = displayMatchPercent().removeSuffix("%").toIntOrNull() ?: 0
