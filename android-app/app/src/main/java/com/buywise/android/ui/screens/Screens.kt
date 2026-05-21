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
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.automirrored.outlined.CompareArrows
import androidx.compose.material.icons.outlined.AutoAwesome
import androidx.compose.material.icons.outlined.CameraAlt
import androidx.compose.material.icons.outlined.ImageSearch
import androidx.compose.material.icons.outlined.Inventory2
import androidx.compose.material.icons.outlined.Search
import androidx.compose.material.icons.outlined.ShoppingBag
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.buywise.android.data.CompareRow
import com.buywise.android.data.CompareState
import com.buywise.android.data.GuideState
import com.buywise.android.data.HomeState
import com.buywise.android.data.Product
import com.buywise.android.data.VisionState
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.components.MetricPill
import com.buywise.android.ui.components.ProductCard
import com.buywise.android.ui.components.SectionTitle

@Composable
fun HomeScreen(state: HomeState, onProductClick: (String) -> Unit, onOpenGuide: () -> Unit) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(18.dp),
        verticalArrangement = Arrangement.spacedBy(18.dp),
    ) {
        item {
            HeroPanel(
                title = state.heroTitle,
                subtitle = state.heroSubtitle,
                onOpenGuide = onOpenGuide,
            )
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.fillMaxWidth()) {
                MetricPill("导购模式", "MVP", modifier = Modifier.weight(1f))
                MetricPill("后端地址", "10.0.2.2", modifier = Modifier.weight(1f))
            }
        }
        item {
            SectionTitle("精选商品", "用价格、评分和场景标签快速筛选候选商品")
        }
        items(state.products) { product ->
            ProductCard(product = product, onClick = { onProductClick(product.id) })
        }
    }
}
@Composable
fun ProductDetailScreen(product: Product?, onBack: () -> Unit) {
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
        item {
            if (product == null) {
                Text("商品不存在", style = MaterialTheme.typography.titleLarge, color = BuyWiseTheme.colors.ink)
            } else {
                ProductHeader(product = product)
            }
        }
        if (product != null) {
            item {
                DetailBlock("适合原因", product.advantages, BuyWiseTheme.colors.secondarySoft)
            }
            item {
                DetailBlock("注意事项", product.cautions, BuyWiseTheme.colors.dangerSoft)
            }
            item {
                DetailBlock("标签", product.tags, BuyWiseTheme.colors.primarySoft)
            }
        }
    }
}

@Composable
private fun HeroPanel(title: String, subtitle: String, onOpenGuide: () -> Unit) {
    Card(
        colors = CardDefaults.cardColors(containerColor = BuyWiseTheme.colors.panel),
        shape = RoundedCornerShape(8.dp),
        border = CardDefaults.outlinedCardBorder(),
    ) {
        Column(modifier = Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
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
                    Text("智能购物决策助手", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.labelMedium)
                }
            }
            Text(title, style = MaterialTheme.typography.headlineMedium, color = BuyWiseTheme.colors.ink)
            Text(subtitle, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
            Button(onClick = onOpenGuide, modifier = Modifier.fillMaxWidth()) {
                Icon(Icons.Outlined.AutoAwesome, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text("打开 AI 导购")
            }
        }
    }
}

@Composable
fun InfoPanel(icon: @Composable () -> Unit, title: String, body: String) {
    Card(
        colors = CardDefaults.cardColors(containerColor = BuyWiseTheme.colors.panel),
        shape = RoundedCornerShape(8.dp),
        border = CardDefaults.outlinedCardBorder(),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(16.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Surface(color = BuyWiseTheme.colors.secondarySoft, shape = RoundedCornerShape(8.dp), modifier = Modifier.size(40.dp)) {
                Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center) {
                    icon()
                }
            }
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text(title, style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
                Text(body, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
            }
        }
    }
}
@Composable
private fun ProductHeader(product: Product) {
    Card(
        colors = CardDefaults.cardColors(containerColor = BuyWiseTheme.colors.panel),
        shape = RoundedCornerShape(8.dp),
        border = CardDefaults.outlinedCardBorder(),
    ) {
        Column(modifier = Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
            Text(product.brand, color = BuyWiseTheme.colors.secondary, fontWeight = FontWeight.Bold)
            Text(product.name, style = MaterialTheme.typography.headlineMedium, color = BuyWiseTheme.colors.ink)
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.fillMaxWidth()) {
                MetricPill("价格", "¥${product.price}", modifier = Modifier.weight(1f))
                MetricPill("评分", "${product.score}", modifier = Modifier.weight(1f))
            }
            Text(product.headline, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
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

