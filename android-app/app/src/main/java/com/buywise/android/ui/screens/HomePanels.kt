package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.CompareArrows
import androidx.compose.material.icons.outlined.AutoAwesome
import androidx.compose.material.icons.outlined.ImageSearch
import androidx.compose.material.icons.outlined.ShoppingBag
import androidx.compose.material3.Button
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
import com.buywise.android.ui.components.FloatingGlassCard
import com.buywise.android.ui.components.FloatingGlassTone
import com.buywise.android.ui.displayPrice

@Composable
fun HeroPanel(title: String, subtitle: String, previewProducts: List<Product>, onOpenGuide: () -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Surface(
                    color = BuyWiseTheme.colors.panel,
                    shape = RoundedCornerShape(12.dp),
                    shadowElevation = 0.dp,
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
                shape = RoundedCornerShape(12.dp),
                shadowElevation = 0.dp,
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
        FloatingGlassCard(
            tone = FloatingGlassTone.Primary,
            radius = BuyWiseDimens.HeroRadius.dp,
            contentPadding = 18.dp,
        ) {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text(title, style = MaterialTheme.typography.titleLarge, color = BuyWiseTheme.colors.ink)
                Text(subtitle, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
                Button(onClick = onOpenGuide) {
                    Icon(Icons.Outlined.AutoAwesome, contentDescription = null)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("开始导购")
                }
            }
        }
        FloatingGlassCard(
            tone = FloatingGlassTone.Neutral,
            radius = BuyWiseDimens.HeroRadius.dp,
            contentPadding = 20.dp,
        ) {
            Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
                Text("推荐预览", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
                if (previewProducts.isNotEmpty()) {
                    previewProducts.forEach { product ->
                        PreviewProductRow(product = product)
                    }
                } else {
                    Text("商品加载后会在这里显示推荐预览。", color = BuyWiseTheme.colors.muted)
                }
            }
        }
    }
}

@Composable
private fun PreviewProductRow(product: Product) {
    FloatingGlassCard(
        tone = FloatingGlassTone.Neutral,
        elevated = false,
        contentPadding = 12.dp,
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
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
            }
            Spacer(modifier = Modifier.width(12.dp))
            Text(product.price.displayPrice(), color = BuyWiseTheme.colors.primary, style = MaterialTheme.typography.titleLarge)
        }
    }
}

@Composable
private fun CapabilityPill(label: String, icon: androidx.compose.ui.graphics.vector.ImageVector) {
    FloatingGlassCard(
        tone = FloatingGlassTone.Neutral,
        radius = 999.dp,
        elevated = false,
        fillMaxWidth = false,
        contentPadding = 0.dp,
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
                label = "导购推荐",
                value = "描述需求",
                icon = Icons.Outlined.AutoAwesome,
                modifier = Modifier.weight(1f),
                onClick = onOpenGuide,
            )
            StatusTile(
                label = "商品对比",
                value = "比较候选",
                icon = Icons.AutoMirrored.Outlined.CompareArrows,
                modifier = Modifier.weight(1f),
                onClick = onOpenCompare,
            )
        }
        FloatingGlassCard(
            tone = FloatingGlassTone.Warm,
            radius = BuyWiseDimens.CardRadius.dp,
            contentPadding = 18.dp,
            onClick = onOpenVision,
        ) {
            Row(
                horizontalArrangement = Arrangement.spacedBy(14.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Surface(color = BuyWiseTheme.colors.accentSoft, shape = RoundedCornerShape(14.dp), modifier = Modifier.size(52.dp)) {
                    Icon(Icons.Outlined.ImageSearch, contentDescription = null, tint = BuyWiseTheme.colors.accent, modifier = Modifier.padding(14.dp))
                }
                Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text("识别商品", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
                    Text("用图片或语音生成需求，再带入导购推荐。", color = BuyWiseTheme.colors.muted)
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
    FloatingGlassCard(
        modifier = modifier,
        tone = FloatingGlassTone.Primary,
        radius = BuyWiseDimens.CardRadius.dp,
        contentPadding = 16.dp,
        onClick = onClick,
    ) {
        Row(
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
