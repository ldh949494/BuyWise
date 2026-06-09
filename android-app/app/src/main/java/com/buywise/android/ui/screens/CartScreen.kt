package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Add
import androidx.compose.material.icons.outlined.DeleteOutline
import androidx.compose.material.icons.outlined.Inventory2
import androidx.compose.material.icons.outlined.Refresh
import androidx.compose.material.icons.outlined.Remove
import androidx.compose.material.icons.outlined.ShoppingBag
import androidx.compose.material.icons.outlined.ShoppingCartCheckout
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.buywise.android.data.CartItem
import com.buywise.android.data.CartState
import com.buywise.android.ui.BuyWiseDimens
import com.buywise.android.ui.BuyWiseIcons
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.displayPrice
import com.buywise.android.ui.components.FloatingGlassCard
import com.buywise.android.ui.components.FloatingGlassTone
import com.buywise.android.ui.components.ShowcaseTopBar
import com.buywise.android.ui.components.SoftDivider

@Composable
fun CartScreen(
    state: CartState,
    onRefresh: () -> Unit,
    onOpenHome: () -> Unit,
    onQuantityChange: (CartItem, Int) -> Unit,
    onRemove: (CartItem) -> Unit,
    onCheckout: () -> Unit,
) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(18.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        item {
            ShowcaseTopBar(
                title = "购物车",
                onBack = null,
                leadingIcon = BuyWiseIcons.Shopping,
                actionIcon = Icons.Outlined.Refresh,
                actionDescription = "刷新购物车",
                onAction = onRefresh,
            )
        }
        if (state.isLoading) {
            item { LinearProgressIndicator(modifier = Modifier.fillMaxWidth()) }
        }
        state.message?.let { message ->
            item {
                InfoPanel(
                    icon = { Icon(Icons.Outlined.ShoppingBag, contentDescription = null) },
                    title = "购物车",
                    body = message,
                )
            }
        }
        state.errorMessage?.let { message ->
            item { ErrorPanel(message = message, actionLabel = "刷新", onAction = onRefresh) }
        }
        if (state.items.isEmpty()) {
            item { EmptyCartCard(onOpenHome = onOpenHome) }
        } else {
            item { CartSummaryCard(state = state, onCheckout = onCheckout) }
            items(state.items, key = { it.id }) { item ->
                CartItemRow(
                    item = item,
                    onQuantityChange = { quantity -> onQuantityChange(item, quantity) },
                    onRemove = { onRemove(item) },
                )
            }
            item { CheckoutHintCard() }
        }
    }
}

@Composable
private fun CartSummaryCard(state: CartState, onCheckout: () -> Unit) {
    FloatingGlassCard(
        tone = FloatingGlassTone.Primary,
        radius = BuyWiseDimens.CardRadius.dp,
        contentPadding = 16.dp,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text("待下单 ${state.totalQuantity} 件", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
                    Text("默认地址结算，生成 BuyWise 影子订单。", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
                }
                Text(state.totalPrice.displayPrice(), color = BuyWiseTheme.colors.primary, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
            }
            Button(
                onClick = onCheckout,
                enabled = !state.isLoading,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Icon(Icons.Outlined.ShoppingCartCheckout, contentDescription = null, modifier = Modifier.size(18.dp))
                Spacer(Modifier.width(8.dp))
                Text("下单")
            }
        }
    }
}

@Composable
private fun CartItemRow(
    item: CartItem,
    onQuantityChange: (Int) -> Unit,
    onRemove: () -> Unit,
) {
    FloatingGlassCard(
        tone = FloatingGlassTone.Neutral,
        radius = 14.dp,
        contentPadding = 12.dp,
    ) {
        Row(
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            FloatingGlassCard(
                modifier = Modifier.size(56.dp),
                tone = FloatingGlassTone.Success,
                radius = 12.dp,
                fillMaxWidth = false,
                contentPadding = 0.dp,
                elevated = false,
            ) {
                Column(
                    modifier = Modifier.fillMaxSize(),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center,
                ) {
                    Icon(Icons.Outlined.Inventory2, contentDescription = null, tint = BuyWiseTheme.colors.secondary)
                }
            }
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text(item.name, color = BuyWiseTheme.colors.ink, fontWeight = FontWeight.Bold, maxLines = 1, overflow = TextOverflow.Ellipsis)
                Text("${item.unitPrice.displayPrice()} x ${item.quantity}", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.labelMedium)
                Row(horizontalArrangement = Arrangement.spacedBy(4.dp), verticalAlignment = Alignment.CenterVertically) {
                    IconButton(onClick = { onQuantityChange(item.quantity - 1) }, enabled = item.quantity > 1) {
                        Icon(Icons.Outlined.Remove, contentDescription = "减少数量")
                    }
                    Text(item.quantity.toString(), color = BuyWiseTheme.colors.ink, fontWeight = FontWeight.Bold)
                    IconButton(onClick = { onQuantityChange(item.quantity + 1) }, enabled = item.quantity < 99) {
                        Icon(Icons.Outlined.Add, contentDescription = "增加数量")
                    }
                }
            }
            Column(horizontalAlignment = Alignment.End, verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(item.lineTotal.displayPrice(), color = BuyWiseTheme.colors.primary, fontWeight = FontWeight.Bold)
                IconButton(onClick = onRemove) {
                    Icon(Icons.Outlined.DeleteOutline, contentDescription = "移除", tint = BuyWiseTheme.colors.danger)
                }
            }
        }
    }
}

@Composable
private fun EmptyCartCard(onOpenHome: () -> Unit) {
    FloatingGlassCard(
        tone = FloatingGlassTone.Neutral,
        radius = 16.dp,
        contentPadding = 18.dp,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text("购物车为空", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink, fontWeight = FontWeight.Bold)
            Text("从导购、识图或商品详情里把候选加入购物车后，可在这里删除、调整数量并下单。", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
            OutlinedButton(onClick = onOpenHome, modifier = Modifier.fillMaxWidth()) {
                Icon(BuyWiseIcons.Search, contentDescription = null, modifier = Modifier.size(18.dp))
                Spacer(Modifier.width(8.dp))
                Text("去选商品")
            }
        }
    }
}

@Composable
private fun CheckoutHintCard() {
    FloatingGlassCard(
        tone = FloatingGlassTone.Success,
        radius = 14.dp,
        contentPadding = 14.dp,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text("结算说明", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
            SoftDivider()
            Text("当前不会跳转真实支付渠道；下单会生成 BuyWise 影子订单，用于闭环记录和购买后反馈。", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
        }
    }
}
