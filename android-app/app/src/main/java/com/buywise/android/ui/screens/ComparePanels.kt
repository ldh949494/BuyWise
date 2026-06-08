package com.buywise.android.ui.screens

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.CompareArrows
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.Forum
import androidx.compose.material.icons.outlined.EmojiEvents
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
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
import com.buywise.android.ui.BuyWiseIcons
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.BuyWiseVisualAssets
import com.buywise.android.ui.components.EvidenceTag
import com.buywise.android.ui.components.EvidenceTone
import com.buywise.android.ui.components.FloatingAssetBadge
import com.buywise.android.ui.components.FloatingGlassCard
import com.buywise.android.ui.components.FloatingGlassTone
import com.buywise.android.ui.components.TactileIconTone
import com.buywise.android.ui.displayPrice
import com.buywise.android.ui.displayRating
import com.buywise.android.ui.shortName

private val AnalysisSteps = listOf("理解需求", "整理候选商品", "核对价格与评价", "生成决策摘要")

@Composable
fun AnalysisProgressCard(title: String, activeStepIndex: Int = AnalysisSteps.lastIndex) {
    FloatingGlassCard(
        tone = FloatingGlassTone.Neutral,
        radius = BuyWiseDimens.CardRadius.dp,
        contentPadding = 16.dp,
        elevated = false,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text(title, style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                AnalysisSteps.forEachIndexed { index, step ->
                    val isActive = index <= activeStepIndex
                    Row(horizontalArrangement = Arrangement.spacedBy(10.dp), verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            Icons.Outlined.CheckCircle,
                            contentDescription = null,
                            tint = if (isActive) BuyWiseTheme.colors.primary else BuyWiseTheme.colors.muted,
                            modifier = Modifier.size(18.dp),
                        )
                        Text(
                            step,
                            color = if (isActive) BuyWiseTheme.colors.ink else BuyWiseTheme.colors.muted,
                            style = MaterialTheme.typography.bodyMedium,
                            fontWeight = if (isActive) FontWeight.Bold else FontWeight.Normal,
                        )
                    }
                }
            }
        }
    }
}

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
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                FloatingAssetBadge(
                    icon = BuyWiseIcons.Trophy,
                    assetRes = BuyWiseVisualAssets.Trophy,
                    contentDescription = null,
                    tone = TactileIconTone.Warm,
                    size = 46.dp,
                    iconSize = 36.dp,
                )
                Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                    Text("AI 决策摘要", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
                    Text("先看推荐结论，再核对价格、评分和风险", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.labelMedium)
                }
            }
            Text(
                state.summary ?: "BuyWise 会先给出优先候选，再把价格、评分和明确差异拆开，帮助你快速缩小选择范围。",
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
fun CompareFitDecisionCard(products: List<Product>, winnerId: String?) {
    if (products.isEmpty()) return
    FloatingGlassCard(
        tone = FloatingGlassTone.Neutral,
        radius = BuyWiseDimens.CardRadius.dp,
        contentPadding = 16.dp,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
            Text("哪个更适合你？", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
            products.take(4).forEach { product ->
                FitProductBlock(product = product, isWinner = product.id == winnerId)
            }
        }
    }
}

@Composable
private fun FitProductBlock(product: Product, isWinner: Boolean) {
    FloatingGlassCard(
        tone = if (isWinner) FloatingGlassTone.Success else FloatingGlassTone.Neutral,
        radius = 12.dp,
        contentPadding = 12.dp,
        elevated = false,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                Text(product.shortName(), color = BuyWiseTheme.colors.ink, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
                if (isWinner) {
                    EvidenceTag("优先候选", tone = EvidenceTone.Success)
                }
            }
            product.fitReasons().forEach { reason ->
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Outlined.CheckCircle, contentDescription = null, tint = BuyWiseTheme.colors.primary, modifier = Modifier.size(16.dp))
                    Text("选它，如果$reason", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
                }
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
                buildCompareRowGroups(rows = rows, products = products).forEach { group ->
                    CompareRowGroupBlock(group = group, products = products)
                }
            }
        }
    }
}

@Composable
private fun CompareRowGroupBlock(group: CompareRowGroup, products: List<Product>) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(group.title, color = BuyWiseTheme.colors.primary, style = MaterialTheme.typography.labelLarge, fontWeight = FontWeight.Bold)
        CompareMatrix(rows = group.rows, products = products)
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

@Composable
fun ContinueCompareChatCard(onContinueCompareChat: () -> Unit) {
    FloatingGlassCard(
        tone = FloatingGlassTone.Neutral,
        radius = BuyWiseDimens.CardRadius.dp,
        contentPadding = 16.dp,
    ) {
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
            Icon(Icons.Outlined.Forum, contentDescription = null, tint = BuyWiseTheme.colors.primary)
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text("还不确定？", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
                Text("继续围绕这组商品追问，保留当前对比上下文。", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
            }
            OutlinedButton(onClick = onContinueCompareChat) {
                Text("继续追问")
            }
        }
    }
}

private data class CompareRowGroup(
    val title: String,
    val rows: List<CompareRow>,
)

private fun buildCompareRowGroups(rows: List<CompareRow>, products: List<Product>): List<CompareRowGroup> {
    val fallbackRows = if (rows.isNotEmpty()) rows else products.defaultCompareRows()
    return listOf(
        CompareRowGroup(
            "购买结论",
            listOf(
                CompareRow("推荐理由", products.map { it.headline.takeIf(String::isNotBlank) ?: "查看详情" }),
                CompareRow("优势", products.map { it.advantages.take(2).joinToString(" / ").ifBlank { "暂无" } }),
            ),
        ),
        CompareRowGroup(
            "价格与库存",
            listOf(
                CompareRow("价格", products.map { it.price.displayPrice() }),
                CompareRow("库存", products.map { it.stockStatus?.takeIf(String::isNotBlank) ?: "查看商家库存" }),
            ),
        ),
        CompareRowGroup(
            "核心信息",
            listOf(
                CompareRow("品类", products.map { it.category?.takeIf(String::isNotBlank) ?: "购物商品" }),
                CompareRow("标签", products.map { it.tags.take(3).joinToString(" / ").ifBlank { "暂无" } }),
            ),
        ),
        CompareRowGroup(
            "体验评分",
            listOf(
                CompareRow("评分", products.map { it.rating.displayRating() }),
                CompareRow("推荐分", products.map { it.recommendationScore?.toInt()?.toString() ?: "暂无" }),
            ),
        ),
        CompareRowGroup(
            "风险提示",
            listOf(
                CompareRow("注意事项", products.map { it.cautions.take(2).joinToString(" / ").ifBlank { "暂无明确风险" } }),
            ),
        ),
        CompareRowGroup(
            "用户评价",
            listOf(
                CompareRow("评价摘要", products.map { it.reviewSummary?.takeIf(String::isNotBlank) ?: "暂无足够评价证据" }),
            ),
        ),
    ).ifEmpty { listOf(CompareRowGroup("对比维度", fallbackRows)) }
}

private fun Product.fitReasons(): List<String> {
    val reasons = (advantages + tags + listOfNotNull(headline.takeIf(String::isNotBlank)))
        .map { it.trim() }
        .filter { it.isNotBlank() }
        .distinct()
        .take(3)
    return reasons.ifEmpty { listOf("你想进一步核对详情和真实评价") }
}

private fun List<Product>.defaultCompareRows(): List<CompareRow> = listOf(
    CompareRow("价格", map { it.price.displayPrice() }),
    CompareRow("评分", map { it.rating.displayRating() }),
    CompareRow("推荐理由", map { it.headline.takeIf { headline -> headline.isNotBlank() } ?: "查看详情" }),
)
