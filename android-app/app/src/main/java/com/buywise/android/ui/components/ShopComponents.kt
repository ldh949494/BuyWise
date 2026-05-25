package com.buywise.android.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.CompareArrows
import androidx.compose.material.icons.outlined.AutoAwesome
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.draw.scale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.buywise.android.data.Product
import com.buywise.android.ui.BuyWiseTheme
import kotlinx.coroutines.delay

@Composable
fun SectionTitle(title: String, subtitle: String? = null) {
    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Text(title, style = MaterialTheme.typography.titleLarge, color = BuyWiseTheme.colors.ink)
        subtitle?.let {
            Text(it, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
        }
    }
}

@Composable
fun ProductCard(
    product: Product,
    onClick: () -> Unit,
    isInCompareBasket: Boolean = false,
    onToggleCompare: (() -> Unit)? = null,
    recommendationReason: String? = null,
) {
    var comparePressed by remember { mutableStateOf(false) }
    val compareScale by animateFloatAsState(
        targetValue = if (comparePressed) 0.94f else 1f,
        label = "productCompareButtonScale",
    )
    LaunchedEffect(comparePressed) {
        if (comparePressed) {
            delay(160)
            comparePressed = false
        }
    }
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        colors = CardDefaults.cardColors(containerColor = BuyWiseTheme.colors.panel),
        shape = RoundedCornerShape(8.dp),
        border = CardDefaults.outlinedCardBorder(),
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                    Text(
                        product.brand ?: "BuyWise",
                        color = BuyWiseTheme.colors.secondary,
                        style = MaterialTheme.typography.labelMedium,
                        fontWeight = FontWeight.Bold,
                    )
                    Text(
                        product.name,
                        style = MaterialTheme.typography.titleMedium,
                        color = BuyWiseTheme.colors.ink,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis,
                    )
                }
                Spacer(modifier = Modifier.width(12.dp))
                Surface(color = BuyWiseTheme.colors.primarySoft, shape = RoundedCornerShape(6.dp)) {
                    Text(
                        product.price.displayPrice(),
                        modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                        color = BuyWiseTheme.colors.primary,
                        fontWeight = FontWeight.Bold,
                    )
                }
            }
            ProductScoreBar(product = product)
            AiTagRow(product = product, reason = recommendationReason)
            Text(
                recommendationReason?.takeIf { it.isNotBlank() } ?: product.headline,
                color = BuyWiseTheme.colors.muted,
                style = MaterialTheme.typography.bodyMedium,
                maxLines = 3,
                overflow = TextOverflow.Ellipsis,
            )
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                product.tags.take(2).forEach { tag ->
                    AssistChip(onClick = {}, label = { Text(tag, maxLines = 1, overflow = TextOverflow.Ellipsis) })
                }
            }
            Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                Text(product.stockStatus ?: "推荐可选", fontWeight = FontWeight.Bold, color = BuyWiseTheme.colors.accent)
                Text(product.category ?: "商品", color = Color(0xFF64748B))
            }
            if (onToggleCompare != null) {
                if (isInCompareBasket) {
                    Button(
                        onClick = {
                            comparePressed = true
                            onToggleCompare()
                        },
                        modifier = Modifier.fillMaxWidth().scale(compareScale),
                    ) {
                        Icon(Icons.AutoMirrored.Outlined.CompareArrows, contentDescription = null)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("已加入对比")
                    }
                } else {
                    OutlinedButton(
                        onClick = {
                            comparePressed = true
                            onToggleCompare()
                        },
                        modifier = Modifier.fillMaxWidth().scale(compareScale),
                    ) {
                        Icon(Icons.AutoMirrored.Outlined.CompareArrows, contentDescription = null)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("加入对比")
                    }
                }
            }
        }
    }
}

@Composable
private fun ProductScoreBar(product: Product) {
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
        MetricPill("推荐指数", product.recommendationScore.displayScore(), modifier = Modifier.weight(1f))
        MetricPill("口碑评分", product.rating.displayRating(), modifier = Modifier.weight(1f))
    }
}

@Composable
private fun AiTagRow(product: Product, reason: String?) {
    val tags = product.aiTags(reason)
    if (tags.isEmpty()) return
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        tags.forEach { tag ->
            AssistChip(
                onClick = {},
                label = { Text(tag, maxLines = 1, overflow = TextOverflow.Ellipsis) },
                leadingIcon = {
                    Icon(Icons.Outlined.AutoAwesome, contentDescription = null)
                },
            )
        }
    }
}

@Composable
fun MetricPill(label: String, value: String, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .defaultMinSize(minHeight = 68.dp)
            .background(Color.White, RoundedCornerShape(8.dp))
            .border(1.dp, BuyWiseTheme.colors.border, RoundedCornerShape(8.dp))
            .padding(horizontal = 14.dp, vertical = 12.dp),
    ) {
        Text(label, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.labelMedium)
        Spacer(modifier = Modifier.height(2.dp))
        Text(value, fontWeight = FontWeight.Bold, color = BuyWiseTheme.colors.ink)
    }
}

private fun Double?.displayPrice(): String = this?.let { "¥${formatNumber(it)}" } ?: "暂无价格"

private fun Double?.displayRating(): String = this?.let { formatNumber(it) } ?: "暂无"

private fun Double?.displayScore(): String = this?.let { "${formatNumber(it)}分" } ?: "待分析"

private fun Product.aiTags(reason: String?): List<String> {
    val text = listOfNotNull(
        category,
        headline,
        reviewSummary,
        reason,
        tags.joinToString(" "),
        advantages.joinToString(" "),
    ).joinToString(" ").lowercase()
    val tags = mutableListOf<String>()
    val score = recommendationScore ?: 0.0
    when {
        score >= 90.0 -> tags += "最推荐"
        score >= 80.0 -> tags += "高匹配"
    }
    if (price != null && price <= 300.0) tags += "预算友好"
    if ("宿舍" in text || "dorm" in text) tags += "宿舍适配"
    if ("静音" in text || "低噪" in text || "quiet" in text) tags += "低噪优先"
    if ("代码" in text || "编程" in text || "coding" in text) tags += "适合写代码"
    if ("性价比" in text || "value" in text) tags += "性价比优先"
    return tags.distinct().take(3)
}

private fun formatNumber(value: Double): String =
    if (value % 1.0 == 0.0) value.toInt().toString() else "%.1f".format(value)
