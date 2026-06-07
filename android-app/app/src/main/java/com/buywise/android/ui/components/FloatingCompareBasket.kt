package com.buywise.android.ui.components

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutVertically
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.CompareArrows
import androidx.compose.material.icons.outlined.Close
import androidx.compose.material.icons.outlined.DeleteSweep
import androidx.compose.material.icons.outlined.ShoppingBag
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.scale
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.buywise.android.data.CompareBasketState
import com.buywise.android.data.Product
import com.buywise.android.ui.BuyWiseTheme
import kotlinx.coroutines.delay

@Composable
fun FloatingCompareBasket(
    state: CompareBasketState,
    onExpandedChange: (Boolean) -> Unit,
    onRemoveProduct: (Product) -> Unit,
    onClear: () -> Unit,
    onStartCompare: () -> Unit,
    onContinueShopping: () -> Unit,
    modifier: Modifier = Modifier,
) {
    if (state.products.isEmpty()) {
        return
    }

    Column(
        modifier = modifier.widthIn(max = 320.dp),
        horizontalAlignment = Alignment.End,
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        AnimatedVisibility(
            visible = state.isExpanded,
            enter = fadeIn() + slideInVertically { it / 4 },
            exit = fadeOut() + slideOutVertically { it / 4 },
        ) {
            ExpandedBasket(
                state = state,
                onRemoveProduct = onRemoveProduct,
                onClear = onClear,
                onStartCompare = onStartCompare,
                onContinueShopping = onContinueShopping,
            )
        }
        BasketButton(
            count = state.products.size,
            expanded = state.isExpanded,
            onClick = { onExpandedChange(!state.isExpanded) },
        )
    }
}

@Composable
private fun BasketButton(count: Int, expanded: Boolean, onClick: () -> Unit) {
    var pulsing by remember { mutableStateOf(false) }
    val badgeScale by animateFloatAsState(
        targetValue = if (pulsing) 1.25f else 1f,
        label = "compareBasketBadgeScale",
    )
    LaunchedEffect(count) {
        pulsing = true
        delay(180)
        pulsing = false
    }

    FloatingGlassCard(
        tone = FloatingGlassTone.SolidPrimary,
        radius = 999.dp,
        fillMaxWidth = false,
        contentPadding = 0.dp,
        onClick = onClick,
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Icon(
                if (expanded) Icons.Outlined.Close else Icons.Outlined.ShoppingBag,
                contentDescription = null,
                tint = BuyWiseTheme.colors.panel,
            )
            Text("对比", color = BuyWiseTheme.colors.panel, fontWeight = FontWeight.Bold)
            Box(
                modifier = Modifier
                    .scale(badgeScale)
                    .size(24.dp)
                    .background(BuyWiseTheme.colors.accent, CircleShape),
                contentAlignment = Alignment.Center,
            ) {
                Text(count.toString(), color = BuyWiseTheme.colors.panel, style = MaterialTheme.typography.labelMedium)
            }
        }
    }
}

@Composable
private fun ExpandedBasket(
    state: CompareBasketState,
    onRemoveProduct: (Product) -> Unit,
    onClear: () -> Unit,
    onStartCompare: () -> Unit,
    onContinueShopping: () -> Unit,
) {
    val haptic = LocalHapticFeedback.current
    FloatingGlassCard(
        tone = FloatingGlassTone.Neutral,
        radius = 8.dp,
        contentPadding = 14.dp,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Icon(Icons.AutoMirrored.Outlined.CompareArrows, contentDescription = null, tint = BuyWiseTheme.colors.primary)
                Text("已选商品", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
                Spacer(modifier = Modifier.weight(1f))
                IconButton(
                    onClick = {
                        haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                        onClear()
                    },
                    modifier = Modifier.size(36.dp),
                ) {
                    Icon(Icons.Outlined.DeleteSweep, contentDescription = "清空对比篮", tint = BuyWiseTheme.colors.muted)
                }
            }
            if (state.hasMixedCategories) {
                Text("包含不同类别商品，对比结果可能不够直接。", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodySmall)
            }
            state.products.forEach { product ->
                BasketProductRow(product = product, onRemove = { onRemoveProduct(product) })
            }
            if (state.products.size < 2) {
                Text("再选 1 件商品，就能生成横向对比和决策摘要。", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodySmall)
                OutlinedButton(
                    onClick = {
                        haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                        onContinueShopping()
                    },
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text("继续选择商品")
                }
            } else {
                Button(
                    onClick = {
                        haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                        onStartCompare()
                    },
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Icon(Icons.AutoMirrored.Outlined.CompareArrows, contentDescription = null)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("开始对比")
                }
            }
        }
    }
}

@Composable
private fun BasketProductRow(product: Product, onRemove: () -> Unit) {
    val haptic = LocalHapticFeedback.current
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
            Text(
                product.name,
                color = BuyWiseTheme.colors.ink,
                style = MaterialTheme.typography.bodyMedium,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
            Text(product.price.displayPrice(), color = BuyWiseTheme.colors.primary, fontWeight = FontWeight.Bold)
        }
        IconButton(
            onClick = {
                haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                onRemove()
            },
            modifier = Modifier.size(34.dp),
        ) {
            Icon(Icons.Outlined.Close, contentDescription = "移除商品", tint = BuyWiseTheme.colors.muted)
        }
    }
}

private fun Double?.displayPrice(): String = this?.let { "¥${formatNumber(it)}" } ?: "暂无价格"

private fun formatNumber(value: Double): String =
    if (value % 1.0 == 0.0) value.toInt().toString() else "%.1f".format(value)
