package com.buywise.android.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
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
import androidx.compose.material.icons.automirrored.outlined.OpenInNew
import androidx.compose.material.icons.outlined.AddShoppingCart
import androidx.compose.material.icons.outlined.AutoAwesome
import androidx.compose.material.icons.outlined.Favorite
import androidx.compose.material.icons.outlined.Share
import androidx.compose.material.icons.outlined.ShoppingBag
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.buywise.android.data.Product
import com.buywise.android.data.ProductDetailState
import com.buywise.android.ui.BuyWiseDimens
import com.buywise.android.ui.BuyWiseIcons
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.BuyWiseVisualAssets
import com.buywise.android.ui.displayPrice
import com.buywise.android.ui.displayRating
import com.buywise.android.ui.displayRecommendationReason
import com.buywise.android.ui.components.EvidenceTag
import com.buywise.android.ui.components.EvidenceTone
import com.buywise.android.ui.components.FloatingAssetBadge
import com.buywise.android.ui.components.FloatingGlassCard
import com.buywise.android.ui.components.FloatingGlassTone
import com.buywise.android.ui.components.ProductImagePreview
import com.buywise.android.ui.components.RatingPill
import com.buywise.android.ui.components.ShowcaseTopBar
import com.buywise.android.ui.components.SoftDivider
import com.buywise.android.ui.components.TactileIconTile
import com.buywise.android.ui.components.TactileIconTone

@Composable
fun ProductDetailScreen(
    state: ProductDetailState,
    fallbackProduct: Product?,
    onBack: () -> Unit,
    isInCompareBasket: (String) -> Boolean,
    onToggleCompare: (Product) -> Unit,
    onAddToCart: (Product) -> Unit,
    onRecordPurchase: (String) -> Unit,
    onOpenProductPage: (String) -> Unit,
) {
    val product = state.product ?: fallbackProduct
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(18.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item {
            ShowcaseTopBar(
                title = "",
                onBack = onBack,
                actionIcon = Icons.Outlined.Share,
                actionDescription = "分享",
                extraAction = {
                    TactileIconTile(
                        icon = Icons.Outlined.Favorite,
                        contentDescription = "收藏",
                        size = 42.dp,
                        iconSize = 21.dp,
                        rounded = true,
                        tone = TactileIconTone.Warm,
                    )
                },
            )
        }
        if (state.isLoading) {
            item { LinearProgressIndicator(modifier = Modifier.fillMaxWidth()) }
        }
        state.errorMessage?.takeIf { product == null }?.let { message ->
            item { ErrorPanel(message = message) }
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
                )
            }
        }
        if (product != null) {
            item {
                ProductDecisionSummaryCard(product = product)
            }
            item {
                ReviewSummaryCard(product = product)
            }
            item {
                KeySpecsCard(product = product)
            }
            if (product.cautions.isNotEmpty()) {
                item { DetailBlock("购买前注意", product.cautions, BuyWiseTheme.colors.dangerSoft) }
            }
            state.errorMessage?.let { message ->
                item { ErrorPanel(message = message) }
            }
            state.orderStatusMessage?.let { message ->
                item { InfoPanel(icon = { Icon(Icons.Outlined.ShoppingBag, contentDescription = null) }, title = "购买记录", body = message) }
            }
            state.cartStatusMessage?.let { message ->
                item { InfoPanel(icon = { Icon(Icons.Outlined.AddShoppingCart, contentDescription = null) }, title = "购物车", body = message) }
            }
            item {
                DetailPurchaseBar(
                    product = product,
                    isInCompareBasket = isInCompareBasket(product.id),
                    canRecordPurchase = state.canRecordPurchase,
                    onToggleCompare = { onToggleCompare(product) },
                    onAddToCart = { onAddToCart(product) },
                    onRecordPurchase = { onRecordPurchase(product.id) },
                    onOpenProductPage = onOpenProductPage,
                )
            }
        }
    }
}

@Composable
private fun ProductDecisionSummaryCard(product: Product) {
    FloatingGlassCard(
        tone = FloatingGlassTone.Neutral,
        radius = BuyWiseDimens.CardRadius.dp,
        elevated = false,
        contentPadding = 16.dp,
    ) {
        Column(modifier = Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Icon(Icons.Outlined.AutoAwesome, contentDescription = null, tint = BuyWiseTheme.colors.primary)
                Text("决策摘要", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
            }
            Text(
                product.headline.takeIf { it.isNotBlank() } ?: product.displayRecommendationReason(),
                color = BuyWiseTheme.colors.ink,
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.Bold,
            )
            val reasons = product.advantages.take(2).ifEmpty {
                listOf(product.displayRecommendationReason())
            }
            reasons.forEach { reason ->
                AdviceLine("适合", reason)
            }
            val caution = product.cautions.firstOrNull { it.isNotBlank() }
                ?: "购买前建议核对商家页面的价格、库存和售后信息。"
            AdviceLine("注意", caution)
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                product.productUrl?.takeIf { it.isNotBlank() }?.let {
                    EvidenceTag("真实商品页", tone = EvidenceTone.Info)
                }
                if (product.price != null || product.stockStatus?.isNotBlank() == true) {
                    EvidenceTag("价格/库存快照", tone = EvidenceTone.Success)
                }
                product.reviewSummary?.takeIf { it.isNotBlank() }?.let {
                    EvidenceTag("评价摘要", tone = EvidenceTone.Info)
                }
                if (product.productUrl.isNullOrBlank() && product.reviewSummary.isNullOrBlank()) {
                    EvidenceTag("证据较少，建议核实", tone = EvidenceTone.Warning)
                }
            }
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
) {
    FloatingGlassCard(
        tone = if (isInCompareBasket) FloatingGlassTone.Success else FloatingGlassTone.Neutral,
        radius = 16.dp,
        contentPadding = 16.dp,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
            Box(modifier = Modifier.fillMaxWidth()) {
                ProductImagePreview(
                    product = product,
                    modifier = Modifier.fillMaxWidth().aspectRatio(1.28f),
                )
                FloatingAssetBadge(
                    icon = BuyWiseIcons.Headphones,
                    assetRes = BuyWiseVisualAssets.Keyboard,
                    contentDescription = null,
                    size = 52.dp,
                    iconSize = 40.dp,
                    modifier = Modifier.align(androidx.compose.ui.Alignment.BottomEnd).padding(end = 10.dp, bottom = 10.dp),
                )
            }
            Text(product.name, style = MaterialTheme.typography.headlineMedium, color = BuyWiseTheme.colors.ink)
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = androidx.compose.ui.Alignment.CenterVertically,
            ) {
                Text(product.price.displayPrice(), color = BuyWiseTheme.colors.primary, style = MaterialTheme.typography.headlineMedium)
                RatingPill(product.rating.displayRating())
            }
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                product.stockStatus?.takeIf { it.isNotBlank() }?.let {
                    EvidenceTag(it, tone = EvidenceTone.Success)
                }
                if (product.price != null || product.stockStatus?.isNotBlank() == true) {
                    EvidenceTag("价格/库存快照", tone = EvidenceTone.Success)
                }
                product.productUrl?.takeIf { it.isNotBlank() }?.let {
                    EvidenceTag("真实商品页", tone = EvidenceTone.Info)
                }
                product.reviewSummary?.takeIf { it.isNotBlank() }?.let {
                    EvidenceTag("评价摘要", tone = EvidenceTone.Info)
                }
                product.tags.take(2).forEach { tag ->
                    EvidenceTag(tag, tone = EvidenceTone.Info)
                }
                if (product.productUrl.isNullOrBlank() && product.reviewSummary.isNullOrBlank()) {
                    EvidenceTag("证据较少", tone = EvidenceTone.Warning)
                }
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
private fun ReviewSummaryCard(product: Product) {
    FloatingGlassCard(tone = FloatingGlassTone.Neutral, radius = 14.dp, contentPadding = 16.dp) {
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("评价摘要", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
                Text("购买前参考", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.labelMedium)
            }
            Row(horizontalArrangement = Arrangement.spacedBy(14.dp), verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                Text(product.rating.displayRating(), style = MaterialTheme.typography.headlineMedium, color = BuyWiseTheme.colors.ink, fontWeight = FontWeight.Bold)
                Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(5.dp)) {
                    (5 downTo 1).forEachIndexed { index, stars ->
                        ReviewBar(stars = stars, fraction = listOf(0.73f, 0.18f, 0.06f, 0.02f, 0.01f)[index])
                    }
                }
            }
            Text(
                product.reviewSummary ?: product.displayRecommendationReason(),
                color = BuyWiseTheme.colors.muted,
                style = MaterialTheme.typography.bodyMedium,
                maxLines = 3,
                overflow = TextOverflow.Ellipsis,
            )
        }
    }
}

@Composable
private fun ReviewBar(stars: Int, fraction: Float) {
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
        Text("$stars ★", color = BuyWiseTheme.colors.ink, style = MaterialTheme.typography.labelMedium, modifier = Modifier.width(30.dp))
        androidx.compose.material3.LinearProgressIndicator(
            progress = { fraction },
            modifier = Modifier.weight(1f),
            color = BuyWiseTheme.colors.accent,
            trackColor = BuyWiseTheme.colors.panelAlt,
        )
    }
}

@Composable
private fun KeySpecsCard(product: Product) {
    FloatingGlassCard(tone = FloatingGlassTone.Neutral, radius = 14.dp, contentPadding = 16.dp) {
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text("关键规格", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
            SpecLine("品牌", product.brand ?: "BuyWise 推荐")
            SpecLine("品类", product.category ?: "购物商品")
            SpecLine("库存", product.stockStatus ?: "查看商家库存")
            SpecLine("标签", product.tags.take(3).joinToString(" / ").ifBlank { "推荐商品" })
        }
    }
}

@Composable
private fun SpecLine(label: String, value: String) {
    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        Text(label, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium, modifier = Modifier.width(92.dp))
        Text(value, color = BuyWiseTheme.colors.ink, style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f), maxLines = 1, overflow = TextOverflow.Ellipsis)
    }
}

@Composable
private fun DetailPurchaseBar(
    product: Product,
    isInCompareBasket: Boolean,
    canRecordPurchase: Boolean,
    onToggleCompare: () -> Unit,
    onAddToCart: () -> Unit,
    onRecordPurchase: () -> Unit,
    onOpenProductPage: (String) -> Unit,
) {
    val productUrl = product.productUrl?.takeIf { it.isNotBlank() }
    FloatingGlassCard(tone = FloatingGlassTone.Neutral, radius = 16.dp, contentPadding = 10.dp) {
        Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Button(
                onClick = onToggleCompare,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Icon(Icons.AutoMirrored.Outlined.CompareArrows, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text(if (isInCompareBasket) "已选入对比" else "加入对比")
            }
            Button(
                onClick = onAddToCart,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Icon(Icons.Outlined.AddShoppingCart, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text("加入购物车")
            }
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp), verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                OutlinedButton(
                    onClick = onRecordPurchase,
                    enabled = canRecordPurchase,
                    modifier = Modifier.weight(1f),
                ) {
                    Icon(Icons.Outlined.ShoppingBag, contentDescription = null)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("记录已购买", maxLines = 1, overflow = TextOverflow.Ellipsis)
                }
                if (productUrl != null) {
                    OutlinedButton(
                        onClick = { onOpenProductPage(productUrl) },
                        modifier = Modifier.weight(1f),
                    ) {
                        Icon(Icons.AutoMirrored.Outlined.OpenInNew, contentDescription = null)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("查看商品页", maxLines = 1, overflow = TextOverflow.Ellipsis)
                    }
                }
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
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                items.take(3).forEach { item ->
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
