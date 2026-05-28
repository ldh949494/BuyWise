package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.AutoAwesome
import androidx.compose.material.icons.outlined.Lightbulb
import androidx.compose.material.icons.outlined.ImageSearch
import androidx.compose.material.icons.outlined.ShoppingBag
import androidx.compose.material.icons.outlined.Storefront
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.buywise.android.data.Product
import com.buywise.android.ui.BuyWiseDimens
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.components.SoftTag
import com.buywise.android.ui.displayFitTags
import com.buywise.android.ui.displayPrice

@Composable
fun HeroPanel(title: String, subtitle: String, previewProducts: List<Product>, onOpenGuide: () -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(22.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Surface(
                    color = BuyWiseTheme.colors.panel,
                    shape = RoundedCornerShape(18.dp),
                    shadowElevation = 4.dp,
                    modifier = Modifier.size(64.dp),
                ) {
                    Icon(
                        Icons.Outlined.ShoppingBag,
                        contentDescription = null,
                        tint = BuyWiseTheme.colors.primary,
                        modifier = Modifier.padding(16.dp),
                    )
                }
                Column {
                    Text("BuyWise", color = BuyWiseTheme.colors.primary, style = MaterialTheme.typography.titleLarge)
                    Text("智能购物决策助手", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
                }
            }
            Surface(
                color = BuyWiseTheme.colors.panel,
                shape = RoundedCornerShape(16.dp),
                shadowElevation = 4.dp,
                modifier = Modifier.size(58.dp),
            ) {
                Icon(
                    Icons.Outlined.AutoAwesome,
                    contentDescription = null,
                    tint = BuyWiseTheme.colors.primary,
                    modifier = Modifier.padding(15.dp),
                )
            }
        }
        Text(title, style = MaterialTheme.typography.headlineMedium, color = BuyWiseTheme.colors.ink)
        Text(subtitle, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
        FlowRow(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            CapabilityPill("预算匹配", Icons.Outlined.ShoppingBag)
            CapabilityPill("需求结构化", Icons.Outlined.Storefront)
            CapabilityPill("可解释推荐", Icons.Outlined.Lightbulb)
        }
        Card(
            colors = CardDefaults.cardColors(containerColor = BuyWiseTheme.colors.panel),
            shape = RoundedCornerShape(BuyWiseDimens.HeroRadius.dp),
            border = CardDefaults.outlinedCardBorder(),
            elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
        ) {
            Column(modifier = Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                    Text("实时推荐预览", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
                    Text("查看全部 ›", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
                }
                if (previewProducts.isNotEmpty()) {
                    previewProducts.forEach { product ->
                        PreviewProductRow(product = product)
                    }
                } else {
                    Text("商品加载后会在这里显示推荐预览。", color = BuyWiseTheme.colors.muted)
                }
                Button(onClick = onOpenGuide, modifier = Modifier.fillMaxWidth()) {
                    Icon(Icons.Outlined.AutoAwesome, contentDescription = null)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("打开 AI 导购")
                }
            }
        }
    }
}

@Composable
private fun PreviewProductRow(product: Product) {
    Surface(
        color = BuyWiseTheme.colors.panel,
        shape = RoundedCornerShape(16.dp),
        border = CardDefaults.outlinedCardBorder(),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text(
                    product.name,
                    color = BuyWiseTheme.colors.ink,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
                product.displayFitTags().firstOrNull()?.let { SoftTag(it) }
            }
            Spacer(modifier = Modifier.width(12.dp))
            Text(product.price.displayPrice(), color = BuyWiseTheme.colors.primary, style = MaterialTheme.typography.titleLarge)
        }
    }
}

@Composable
private fun CapabilityPill(label: String, icon: androidx.compose.ui.graphics.vector.ImageVector) {
    Surface(
        color = BuyWiseTheme.colors.panel,
        shape = RoundedCornerShape(999.dp),
        border = CardDefaults.outlinedCardBorder(),
        shadowElevation = 2.dp,
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 14.dp, vertical = 10.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(icon, contentDescription = null, tint = BuyWiseTheme.colors.primary)
            Text(label, color = BuyWiseTheme.colors.ink, fontWeight = FontWeight.SemiBold)
        }
    }
}

@Composable
fun QuickEntryPanel(
    onOpenGuide: () -> Unit,
    onOpenCompare: () -> Unit,
    onOpenVision: () -> Unit,
) {
    Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
        Row(horizontalArrangement = Arrangement.spacedBy(14.dp), modifier = Modifier.fillMaxWidth()) {
            StatusTile(
                label = "导购模式",
                value = "MVP",
                icon = Icons.Outlined.AutoAwesome,
                modifier = Modifier.weight(1f),
                onClick = onOpenGuide,
            )
            StatusTile(
                label = "后端地址",
                value = "10.0.2.2",
                icon = Icons.Outlined.Storefront,
                modifier = Modifier.weight(1f),
                onClick = onOpenCompare,
            )
        }
        Card(
            colors = CardDefaults.cardColors(containerColor = BuyWiseTheme.colors.panel),
            shape = RoundedCornerShape(BuyWiseDimens.CardRadius.dp),
            border = CardDefaults.outlinedCardBorder(),
            elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
            modifier = Modifier.fillMaxWidth(),
            onClick = onOpenVision,
        ) {
            Row(
                modifier = Modifier.padding(18.dp),
                horizontalArrangement = Arrangement.spacedBy(14.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Surface(color = BuyWiseTheme.colors.accentSoft, shape = RoundedCornerShape(14.dp), modifier = Modifier.size(52.dp)) {
                    Icon(Icons.Outlined.ImageSearch, contentDescription = null, tint = BuyWiseTheme.colors.accent, modifier = Modifier.padding(14.dp))
                }
                Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text("多模态联调", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
                    Text("用图片或语音提取 query，再带入导购推荐。", color = BuyWiseTheme.colors.muted)
                }
                Text("›", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.titleLarge)
            }
        }
    }
}

@Composable
private fun StatusTile(
    label: String,
    value: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    modifier: Modifier = Modifier,
    onClick: () -> Unit,
) {
    Card(
        colors = CardDefaults.cardColors(containerColor = BuyWiseTheme.colors.panel),
        shape = RoundedCornerShape(BuyWiseDimens.CardRadius.dp),
        border = CardDefaults.outlinedCardBorder(),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
        modifier = modifier,
        onClick = onClick,
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Surface(color = BuyWiseTheme.colors.primarySoft, shape = RoundedCornerShape(14.dp), modifier = Modifier.size(48.dp)) {
                Icon(icon, contentDescription = null, tint = BuyWiseTheme.colors.primary, modifier = Modifier.padding(13.dp))
            }
            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text(label, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
                Text(value, color = BuyWiseTheme.colors.ink, style = MaterialTheme.typography.titleMedium)
            }
        }
    }
}
