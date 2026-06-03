package com.buywise.android.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
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
import com.buywise.android.ui.BuyWiseDimens
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.displayBrandCategory
import com.buywise.android.ui.displayFitTags
import com.buywise.android.ui.displayMatchPercent
import com.buywise.android.ui.displayPlatform
import com.buywise.android.ui.displayPrice
import com.buywise.android.ui.displayRating
import com.buywise.android.ui.displayRecommendationReason
import com.buywise.android.ui.displaySales
import com.buywise.android.ui.displayStockLabel
import com.buywise.android.ui.components.EvidenceTag
import com.buywise.android.ui.components.EvidenceTone
import com.buywise.android.ui.components.FloatingGlassCard
import com.buywise.android.ui.components.FloatingGlassTone
import com.buywise.android.ui.components.MetricPill
import com.buywise.android.ui.components.ProductImagePreview
import com.buywise.android.ui.components.SoftTag

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
                    .background(BuyWiseTheme.colors.panel, RoundedCornerShape(12.dp))
                    .border(1.dp, BuyWiseTheme.colors.border, RoundedCornerShape(12.dp)),
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
            item { DetailEvidenceCard(product = product) }
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
    FloatingGlassCard(
        tone = FloatingGlassTone.Primary,
        radius = BuyWiseDimens.CardRadius.dp,
        contentPadding = 16.dp,
    ) {
        Column(modifier = Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(12.dp)) {
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
    FloatingGlassCard(
        tone = FloatingGlassTone.Success,
        radius = BuyWiseDimens.CardRadius.dp,
        contentPadding = 16.dp,
    ) {
        Column(modifier = Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Icon(Icons.AutoMirrored.Outlined.TrendingUp, contentDescription = null, tint = BuyWiseTheme.colors.secondary)
                Text("价格与口碑信号", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
            }
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.fillMaxWidth()) {
                MetricPill("当前价格", product.price.displayPrice(), modifier = Modifier.weight(1f))
                MetricPill("AI 匹配度", product.displayMatchPercent(), modifier = Modifier.weight(1f))
            }
            Text(
                product.reviewSummary ?: "当前建议主要依据商品参数、标签、价格和口碑信号生成。",
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
    FloatingGlassCard(
        tone = if (isInCompareBasket) FloatingGlassTone.Success else FloatingGlassTone.Neutral,
        radius = BuyWiseDimens.CardRadius.dp,
        contentPadding = 16.dp,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
            ProductImagePreview(
                product = product,
                modifier = Modifier.fillMaxWidth().aspectRatio(1.28f),
            )
            Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                EvidenceTag(product.displayBrandCategory(), tone = EvidenceTone.Success)
                EvidenceTag(product.displayStockLabel(), tone = EvidenceTone.Success)
            }
            Text(product.name, style = MaterialTheme.typography.headlineMedium, color = BuyWiseTheme.colors.ink)
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = androidx.compose.ui.Alignment.CenterVertically,
            ) {
                Text(product.price.displayPrice(), color = BuyWiseTheme.colors.primary, style = MaterialTheme.typography.headlineMedium)
                Text("★ ${product.rating.displayRating()} · ${product.displaySales()}", color = BuyWiseTheme.colors.accent, fontWeight = FontWeight.Bold)
            }
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                SoftTag(product.displayPlatform())
                product.displayFitTags().take(2).forEach { SoftTag(it) }
            }
            Text(product.displayRecommendationReason(), color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
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
                    tokenRequiredMessage ?: "购买后反馈功能暂未开启。",
                    color = BuyWiseTheme.colors.danger,
                    style = MaterialTheme.typography.bodyMedium,
                )
            }
        }
    }
}

@Composable
private fun DetailEvidenceCard(product: Product) {
    FloatingGlassCard(
        tone = FloatingGlassTone.Neutral,
        radius = BuyWiseDimens.CardRadius.dp,
        contentPadding = 16.dp,
    ) {
        Column(modifier = Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text("推荐证据", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.fillMaxWidth()) {
                MetricPill("预算", if ((product.price ?: Double.MAX_VALUE) <= 500.0) "匹配" else "需确认", modifier = Modifier.weight(1f))
                MetricPill("场景", product.displayFitTags().firstOrNull() ?: "日常", modifier = Modifier.weight(1f))
                MetricPill("反馈", product.rating.displayRating(), modifier = Modifier.weight(1f))
            }
        }
    }
}

@Composable
private fun DetailBlock(title: String, items: List<String>, tone: androidx.compose.ui.graphics.Color) {
    FloatingGlassCard(
        tone = FloatingGlassTone.Neutral,
        radius = BuyWiseDimens.CardRadius.dp,
        contentPadding = 16.dp,
    ) {
        Column(modifier = Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(10.dp)) {
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

private fun Product.audienceAdvice(): String {
    val scenes = tags.filter { it.length <= 8 }.take(2)
    val categoryText = category ?: "数码产品"
    return (scenes + categoryText).distinct().joinToString("、").ifBlank { "关注预算、实用性和购买确定性的用户" }
}

private fun Product.buyingAdvice(): String {
    val score = displayMatchPercent().removeSuffix("%").toIntOrNull() ?: 0
    return when {
        score >= 90 -> "AI 匹配度很高，若价格符合预算，可以优先考虑入手。"
        score >= 80 -> "整体匹配度较高，建议和同价位候选商品对比后决定。"
        price != null -> "当前价格为 ${price.displayPrice()}，建议结合预算、评价摘要和售后再判断。"
        else -> "价格信息不足，建议确认实时价格和平台售后后再购买。"
    }
}
