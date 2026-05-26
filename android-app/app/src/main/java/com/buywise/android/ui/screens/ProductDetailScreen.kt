package com.buywise.android.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
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
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.automirrored.outlined.CompareArrows
import androidx.compose.material.icons.automirrored.outlined.TrendingUp
import androidx.compose.material.icons.outlined.AutoAwesome
import androidx.compose.material.icons.outlined.ShoppingBag
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.buywise.android.data.Product
import com.buywise.android.data.ProductDetailState
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.components.MetricPill

@Composable
fun ProductDetailScreen(
    state: ProductDetailState,
    fallbackProduct: Product?,
    onBack: () -> Unit,
    isInCompareBasket: (String) -> Boolean,
    onToggleCompare: (Product) -> Unit,
    onRecordPurchase: (String) -> Unit,
) {
    val product = state.product ?: fallbackProduct
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(18.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item {
            IconButton(
                onClick = onBack,
                modifier = Modifier
                    .size(42.dp)
                    .background(BuyWiseTheme.colors.panel, RoundedCornerShape(8.dp))
                    .border(1.dp, BuyWiseTheme.colors.border, RoundedCornerShape(8.dp)),
            ) {
                Icon(Icons.AutoMirrored.Outlined.ArrowBack, contentDescription = "返回")
            }
        }
        if (state.isLoading) {
            item { LinearProgressIndicator(modifier = Modifier.fillMaxWidth()) }
        }
        state.errorMessage?.let { message ->
            item { ErrorPanel(message = message) }
        }
        state.orderStatusMessage?.let { message ->
            item { InfoPanel(icon = { Icon(Icons.Outlined.ShoppingBag, contentDescription = null) }, title = "购买记录", body = message) }
        }
        item {
            if (product == null) {
                Text("商品不存在", style = MaterialTheme.typography.titleLarge, color = BuyWiseTheme.colors.ink)
            } else {
                ProductHeader(
                    product = product,
                    isInCompareBasket = isInCompareBasket(product.id),
                    canRecordPurchase = state.canRecordPurchase,
                    tokenRequiredMessage = state.tokenRequiredMessage,
                    onToggleCompare = { onToggleCompare(product) },
                    onRecordPurchase = { onRecordPurchase(product.id) },
                )
            }
        }
        if (product != null) {
            item { PurchaseAdviceCard(product = product) }
            item { SignalSummaryCard(product = product) }
            item { DetailBlock("适合原因", product.advantages, BuyWiseTheme.colors.secondarySoft) }
            item { DetailBlock("注意事项", product.cautions, BuyWiseTheme.colors.dangerSoft) }
            item { DetailBlock("标签", product.tags, BuyWiseTheme.colors.primarySoft) }
        }
    }
}

@Composable
private fun PurchaseAdviceCard(product: Product) {
    Card(
        colors = CardDefaults.cardColors(containerColor = BuyWiseTheme.colors.panel),
        shape = RoundedCornerShape(8.dp),
        border = CardDefaults.outlinedCardBorder(),
    ) {
        Column(modifier = Modifier.fillMaxWidth().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Icon(Icons.Outlined.AutoAwesome, contentDescription = null, tint = BuyWiseTheme.colors.primary)
                Text("AI 购买建议", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
            }
            AdviceLine("适合人群", product.audienceAdvice())
            AdviceLine("核心优势", product.advantages.take(2).joinToString(" / ").ifBlank { product.headline })
            AdviceLine("不适合", product.cautions.take(2).joinToString(" / ").ifBlank { "暂未发现明显限制，建议结合预算和平台售后确认。" })
            AdviceLine("购买建议", product.buyingAdvice())
        }
    }
}

@Composable
private fun SignalSummaryCard(product: Product) {
    Card(
        colors = CardDefaults.cardColors(containerColor = BuyWiseTheme.colors.panel),
        shape = RoundedCornerShape(8.dp),
        border = CardDefaults.outlinedCardBorder(),
    ) {
        Column(modifier = Modifier.fillMaxWidth().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Icon(Icons.AutoMirrored.Outlined.TrendingUp, contentDescription = null, tint = BuyWiseTheme.colors.secondary)
                Text("价格与口碑信号", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
            }
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.fillMaxWidth()) {
                MetricPill("当前价格", product.price.displayPrice(), modifier = Modifier.weight(1f))
                MetricPill("推荐指数", product.recommendationScore.displayScore(), modifier = Modifier.weight(1f))
            }
            Text(
                product.reviewSummary ?: "后端暂未返回评论摘要，当前建议主要依据商品参数、标签和推荐分生成。",
                color = BuyWiseTheme.colors.muted,
                style = MaterialTheme.typography.bodyMedium,
            )
        }
    }
}

@Composable
private fun AdviceLine(label: String, value: String) {
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text(label, color = BuyWiseTheme.colors.primary, fontWeight = FontWeight.Bold)
        Text(value, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
    }
}

@Composable
private fun ProductHeader(
    product: Product,
    isInCompareBasket: Boolean,
    canRecordPurchase: Boolean,
    tokenRequiredMessage: String?,
    onToggleCompare: () -> Unit,
    onRecordPurchase: () -> Unit,
) {
    Card(
        colors = CardDefaults.cardColors(containerColor = BuyWiseTheme.colors.panel),
        shape = RoundedCornerShape(8.dp),
        border = CardDefaults.outlinedCardBorder(),
    ) {
        Column(modifier = Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
            Text(product.brand ?: "BuyWise", color = BuyWiseTheme.colors.secondary, fontWeight = FontWeight.Bold)
            Text(product.name, style = MaterialTheme.typography.headlineMedium, color = BuyWiseTheme.colors.ink)
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.fillMaxWidth()) {
                MetricPill("价格", product.price.displayPrice(), modifier = Modifier.weight(1f))
                MetricPill("评分", product.rating.displayRating(), modifier = Modifier.weight(1f))
            }
            Text(product.headline, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
            product.reviewSummary?.let {
                Text(it, color = BuyWiseTheme.colors.ink, style = MaterialTheme.typography.bodyMedium)
            }
            Button(onClick = onToggleCompare, modifier = Modifier.fillMaxWidth()) {
                Icon(Icons.AutoMirrored.Outlined.CompareArrows, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text(if (isInCompareBasket) "已加入对比" else "加入对比")
            }
            Button(onClick = onRecordPurchase, enabled = canRecordPurchase, modifier = Modifier.fillMaxWidth()) {
                Icon(Icons.Outlined.ShoppingBag, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text("记录购买")
            }
            if (!canRecordPurchase) {
                Text(
                    tokenRequiredMessage ?: "当前构建未配置 beta token，无法记录购买。",
                    color = BuyWiseTheme.colors.danger,
                    style = MaterialTheme.typography.bodyMedium,
                )
            }
        }
    }
}

@Composable
private fun DetailBlock(title: String, items: List<String>, tone: androidx.compose.ui.graphics.Color) {
    Card(
        colors = CardDefaults.cardColors(containerColor = BuyWiseTheme.colors.panel),
        shape = RoundedCornerShape(8.dp),
        border = CardDefaults.outlinedCardBorder(),
    ) {
        Column(modifier = Modifier.fillMaxWidth().padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text(title, style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
            if (items.isEmpty()) {
                Text("暂无", color = BuyWiseTheme.colors.muted)
            } else {
                FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    items.forEach { item ->
                        Text(
                            item,
                            modifier = Modifier
                                .background(tone, RoundedCornerShape(6.dp))
                                .padding(horizontal = 10.dp, vertical = 7.dp),
                            color = BuyWiseTheme.colors.ink,
                            maxLines = 2,
                            overflow = TextOverflow.Ellipsis,
                        )
                    }
                }
            }
        }
    }
}

private fun Double?.displayPrice(): String = this?.let { "¥${formatNumber(it)}" } ?: "暂无价格"

private fun Double?.displayRating(): String = this?.let { formatNumber(it) } ?: "暂无"

private fun Double?.displayScore(): String = this?.let { "${formatNumber(it)}分" } ?: "待分析"

private fun Product.audienceAdvice(): String {
    val scenes = tags.filter { it.length <= 8 }.take(2)
    val categoryText = category ?: "数码产品"
    return (scenes + categoryText).distinct().joinToString("、").ifBlank { "关注预算、实用性和购买确定性的用户" }
}

private fun Product.buyingAdvice(): String {
    val score = recommendationScore ?: 0.0
    return when {
        score >= 90.0 -> "推荐指数很高，若价格符合预算，可以优先考虑入手。"
        score >= 80.0 -> "整体匹配度较高，建议和同价位候选商品对比后决定。"
        price != null -> "当前价格为 ${price.displayPrice()}，建议结合预算、评价摘要和售后再判断。"
        else -> "价格信息不足，建议确认实时价格和平台售后后再购买。"
    }
}

private fun formatNumber(value: Double): String =
    if (value % 1.0 == 0.0) value.toInt().toString() else "%.1f".format(value)
