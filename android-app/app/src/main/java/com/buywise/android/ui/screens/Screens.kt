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
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.outlined.AutoAwesome
import androidx.compose.material.icons.outlined.ShoppingBag
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.buywise.android.data.HomeState
import com.buywise.android.data.Product
import com.buywise.android.data.ProductDetailState
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.components.MetricPill
import com.buywise.android.ui.components.ProductCard
import com.buywise.android.ui.components.SectionTitle

@Composable
fun HomeScreen(
    state: HomeState,
    onProductClick: (String) -> Unit,
    onOpenGuide: () -> Unit,
    onSubmitFeedback: (com.buywise.android.data.FeedbackPrompt) -> Unit,
    onRetry: () -> Unit,
) {
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
        if (state.isLoading) {
            item { LinearProgressIndicator(modifier = Modifier.fillMaxWidth()) }
        }
        state.errorMessage?.let { message ->
            item {
                ErrorPanel(message = message, actionLabel = "重试", onAction = onRetry)
            }
        }
        if (state.feedbackPrompts.isNotEmpty()) {
            item {
                SectionTitle("待评价", "收货后的真实反馈会进入商品分析")
            }
            items(state.feedbackPrompts) { prompt ->
                FeedbackPromptCard(
                    productName = prompt.productName,
                    onSubmit = { onSubmitFeedback(prompt) },
                )
            }
        }
        item {
            SectionTitle("精选商品", "来自 BuyWise 后端的商品列表")
        }
        if (!state.isLoading && state.products.isEmpty() && state.errorMessage == null) {
            item { Text("暂无商品。", color = BuyWiseTheme.colors.muted) }
        }
        items(state.products) { product ->
            ProductCard(product = product, onClick = { onProductClick(product.id) })
        }
    }
}

@Composable
fun ProductDetailScreen(
    state: ProductDetailState,
    fallbackProduct: Product?,
    onBack: () -> Unit,
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
                ProductHeader(product = product, onRecordPurchase = { onRecordPurchase(product.id) })
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
fun ErrorPanel(message: String, actionLabel: String? = null, onAction: (() -> Unit)? = null) {
    Card(
        colors = CardDefaults.cardColors(containerColor = BuyWiseTheme.colors.dangerSoft),
        shape = RoundedCornerShape(8.dp),
        border = CardDefaults.outlinedCardBorder(),
    ) {
        Column(modifier = Modifier.fillMaxWidth().padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text(message, color = BuyWiseTheme.colors.danger, style = MaterialTheme.typography.bodyMedium)
            if (actionLabel != null && onAction != null) {
                Button(onClick = onAction) {
                    Text(actionLabel)
                }
            }
        }
    }
}

@Composable
private fun ProductHeader(product: Product, onRecordPurchase: () -> Unit) {
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
            Button(onClick = onRecordPurchase, modifier = Modifier.fillMaxWidth()) {
                Icon(Icons.Outlined.ShoppingBag, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text("记录购买")
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

private fun formatNumber(value: Double): String =
    if (value % 1.0 == 0.0) value.toInt().toString() else "%.1f".format(value)
