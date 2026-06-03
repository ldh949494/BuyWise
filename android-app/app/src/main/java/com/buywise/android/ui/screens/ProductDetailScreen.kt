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
import com.buywise.android.ui.displayPrice
import com.buywise.android.ui.displayRating
import com.buywise.android.ui.displayRecommendationReason
import com.buywise.android.ui.components.FloatingGlassCard
import com.buywise.android.ui.components.FloatingGlassTone
import com.buywise.android.ui.components.ProductImagePreview

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
            item { PurchaseAdviceCard(product = product) }
            if (product.cautions.isNotEmpty()) {
                item { DetailBlock("购买前注意", product.cautions, BuyWiseTheme.colors.dangerSoft) }
            }
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
                Text("为什么推荐", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
            }
            val reasons = product.advantages.take(3).ifEmpty {
                listOf(product.displayRecommendationReason())
            }
            reasons.forEachIndexed { index, reason ->
                AdviceLine("理由 ${index + 1}", reason)
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
            Text(product.name, style = MaterialTheme.typography.headlineMedium, color = BuyWiseTheme.colors.ink)
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = androidx.compose.ui.Alignment.CenterVertically,
            ) {
                Text(product.price.displayPrice(), color = BuyWiseTheme.colors.primary, style = MaterialTheme.typography.headlineMedium)
                Text("★ ${product.rating.displayRating()}", color = BuyWiseTheme.colors.accent, fontWeight = FontWeight.Bold)
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
