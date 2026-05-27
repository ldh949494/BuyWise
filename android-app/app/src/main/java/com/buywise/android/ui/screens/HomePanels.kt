package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.AutoAwesome
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.ImageSearch
import androidx.compose.material.icons.outlined.ShoppingBag
import androidx.compose.material.icons.outlined.Storefront
import androidx.compose.material3.AssistChip
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
import com.buywise.android.ui.displayMatchPercent
import com.buywise.android.ui.displayPrice

@Composable
fun HeroPanel(title: String, subtitle: String, previewProducts: List<Product>, onOpenGuide: () -> Unit) {
    Card(
        colors = CardDefaults.cardColors(containerColor = BuyWiseTheme.colors.panel),
        shape = RoundedCornerShape(BuyWiseDimens.HeroRadius.dp),
        border = CardDefaults.outlinedCardBorder(),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
    ) {
        Column(modifier = Modifier.padding(24.dp), verticalArrangement = Arrangement.spacedBy(18.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Surface(color = BuyWiseTheme.colors.primarySoft, shape = RoundedCornerShape(8.dp)) {
                    Icon(
                        Icons.Outlined.ShoppingBag,
                        contentDescription = null,
                        tint = BuyWiseTheme.colors.primary,
                        modifier = Modifier.padding(9.dp),
                    )
                }
                Column {
                    Text("BuyWise", color = BuyWiseTheme.colors.primary, fontWeight = FontWeight.Bold)
                    Text("AI 智能购物决策助手", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.labelMedium)
                }
            }
            Text(title, style = MaterialTheme.typography.headlineMedium, color = BuyWiseTheme.colors.ink)
            Text(subtitle, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf("预算匹配", "场景理解", "可解释推荐").forEach { label ->
                    AssistChip(
                        onClick = {},
                        label = { Text(label) },
                        leadingIcon = { Icon(Icons.Outlined.CheckCircle, contentDescription = null) },
                    )
                }
            }
            if (previewProducts.isNotEmpty()) {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("实时推荐预览", color = BuyWiseTheme.colors.ink, fontWeight = FontWeight.Bold)
                    previewProducts.forEach { product ->
                        PreviewProductRow(product = product)
                    }
                }
            }
            Button(onClick = onOpenGuide, modifier = Modifier.fillMaxWidth()) {
                Icon(Icons.Outlined.AutoAwesome, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text("打开 AI 导购")
            }
        }
    }
}

@Composable
private fun PreviewProductRow(product: Product) {
    Surface(color = BuyWiseTheme.colors.panelAlt, shape = RoundedCornerShape(14.dp)) {
        Column(
            modifier = Modifier.fillMaxWidth().padding(horizontal = 14.dp, vertical = 12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                Text(
                    product.name,
                    modifier = Modifier.weight(1f),
                    color = BuyWiseTheme.colors.ink,
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.SemiBold,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
                Spacer(modifier = Modifier.width(10.dp))
                Text(product.price.displayPrice(), color = BuyWiseTheme.colors.primary, fontWeight = FontWeight.Bold)
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                SoftTag("匹配度 ${product.displayMatchPercent()}")
                product.displayFitTags().take(2).forEach { SoftTag(it) }
            }
        }
    }
}

@Composable
fun QuickEntryPanel(
    onOpenGuide: () -> Unit,
    onOpenCompare: () -> Unit,
    onOpenVision: () -> Unit,
) {
    Card(
        colors = CardDefaults.cardColors(containerColor = BuyWiseTheme.colors.panel),
        shape = RoundedCornerShape(BuyWiseDimens.CardRadius.dp),
        border = CardDefaults.outlinedCardBorder(),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
    ) {
        Column(modifier = Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
            Text("快速入口", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
            FlowRow(horizontalArrangement = Arrangement.spacedBy(10.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Button(onClick = onOpenGuide) {
                    Icon(Icons.Outlined.AutoAwesome, contentDescription = null)
                    Spacer(modifier = Modifier.width(6.dp))
                    Text("AI 导购")
                }
                Button(onClick = onOpenCompare) {
                    Icon(Icons.Outlined.CheckCircle, contentDescription = null)
                    Spacer(modifier = Modifier.width(6.dp))
                    Text("商品对比")
                }
                Button(onClick = onOpenVision) {
                    Icon(Icons.Outlined.ImageSearch, contentDescription = null)
                    Spacer(modifier = Modifier.width(6.dp))
                    Text("上传图片识别")
                }
                Button(onClick = {}) {
                    Icon(Icons.Outlined.Storefront, contentDescription = null)
                    Spacer(modifier = Modifier.width(6.dp))
                    Text("精选商品")
                }
            }
        }
    }
}
