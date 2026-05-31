package com.buywise.android.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.outlined.Image
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.CompareArrows
import androidx.compose.material.icons.outlined.AutoAwesome
import androidx.compose.material3.AssistChip
import androidx.compose.material3.AssistChipDefaults
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.Alignment
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.draw.scale
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import coil3.compose.AsyncImage
import com.buywise.android.data.Product
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
import kotlinx.coroutines.delay

@Composable
fun SectionTitle(title: String, subtitle: String? = null) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(title, style = MaterialTheme.typography.titleLarge, color = BuyWiseTheme.colors.ink)
        subtitle?.let {
            Text(it, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
        }
    }
}

@Composable
fun ProductCard(
    product: Product,
    onClick: () -> Unit,
    isInCompareBasket: Boolean = false,
    onToggleCompare: (() -> Unit)? = null,
    recommendationReason: String? = null,
) {
    var comparePressed by remember { mutableStateOf(false) }
    val compareScale by animateFloatAsState(
        targetValue = if (comparePressed) 0.94f else 1f,
        label = "productCompareButtonScale",
    )
    LaunchedEffect(comparePressed) {
        if (comparePressed) {
            delay(160)
            comparePressed = false
        }
    }
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        colors = CardDefaults.cardColors(containerColor = BuyWiseTheme.colors.panel),
        shape = RoundedCornerShape(BuyWiseDimens.CardRadius.dp),
        border = CardDefaults.outlinedCardBorder().copy(width = 1.dp, brush = SolidColor(BuyWiseTheme.colors.border)),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            Row(
                horizontalArrangement = Arrangement.spacedBy(16.dp),
                modifier = Modifier.fillMaxWidth(),
            ) {
                ProductImagePreview(
                    product = product,
                    modifier = Modifier.size(width = 112.dp, height = 112.dp),
                )
                Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                    Text(
                        product.displayBrandCategory(),
                        color = BuyWiseTheme.colors.secondary,
                        style = MaterialTheme.typography.labelMedium,
                        fontWeight = FontWeight.Bold,
                    )
                    Text(
                        product.name,
                        style = MaterialTheme.typography.titleMedium,
                        color = BuyWiseTheme.colors.ink,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis,
                    )
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                        Text("★", color = BuyWiseTheme.colors.accent, fontWeight = FontWeight.Bold)
                        Text(product.rating.displayRating(), color = BuyWiseTheme.colors.ink, fontWeight = FontWeight.Bold)
                        Text("|", color = BuyWiseTheme.colors.border)
                        Text(product.category ?: "精选商品", color = BuyWiseTheme.colors.muted)
                    }
                }
                Spacer(modifier = Modifier.width(12.dp))
                Surface(color = BuyWiseTheme.colors.primarySoft, shape = RoundedCornerShape(10.dp)) {
                    Text(
                        product.price.displayPrice(),
                        modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                        color = BuyWiseTheme.colors.primary,
                        fontWeight = FontWeight.Bold,
                    )
                }
            }
            ProductScoreBar(product = product)
            AiTagRow(product = product, reason = recommendationReason)
            Text(
                product.displayRecommendationReason(recommendationReason),
                color = BuyWiseTheme.colors.muted,
                style = MaterialTheme.typography.bodyMedium,
                maxLines = 3,
                overflow = TextOverflow.Ellipsis,
            )
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                product.displayFitTags(recommendationReason).take(3).forEach { tag ->
                    SoftTag(tag)
                }
            }
            Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                Text("● ${product.displayStockLabel()}", fontWeight = FontWeight.Bold, color = BuyWiseTheme.colors.secondary)
                ProductCommerceSignals(product = product)
            }
            if (onToggleCompare != null) {
                if (isInCompareBasket) {
                    Button(
                        onClick = {
                            comparePressed = true
                            onToggleCompare()
                        },
                        modifier = Modifier.fillMaxWidth().scale(compareScale),
                    ) {
                        Icon(Icons.AutoMirrored.Outlined.CompareArrows, contentDescription = null)
                        Spacer(modifier = Modifier.width(6.dp))
                        Text("已加入对比")
                    }
                } else {
                    OutlinedButton(
                        onClick = {
                            comparePressed = true
                            onToggleCompare()
                        },
                        modifier = Modifier.fillMaxWidth().scale(compareScale),
                    ) {
                        Icon(Icons.AutoMirrored.Outlined.CompareArrows, contentDescription = null)
                        Spacer(modifier = Modifier.width(6.dp))
                        Text("+ 加入对比")
                    }
                }
            }
        }
    }
}

@Composable
fun ProductImagePreview(product: Product, modifier: Modifier = Modifier) {
    val shape = RoundedCornerShape(12.dp)
    Box(
        modifier = modifier
            .clip(shape)
            .background(BuyWiseTheme.colors.panelAlt)
            .border(1.dp, BuyWiseTheme.colors.border, shape),
        contentAlignment = Alignment.Center,
    ) {
        val imageUrl = product.imageUrl?.takeIf { it.isNotBlank() }
        if (imageUrl == null) {
            ImagePlaceholder(product = product)
        } else {
            AsyncImage(
                model = imageUrl,
                contentDescription = product.name,
                modifier = Modifier.fillMaxSize(),
                contentScale = ContentScale.Crop,
            )
        }
    }
}

@Composable
private fun ImagePlaceholder(product: Product) {
    Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Icon(Icons.Outlined.Image, contentDescription = null, tint = BuyWiseTheme.colors.muted)
        Text(
            product.brand ?: product.category ?: "商品图片",
            color = BuyWiseTheme.colors.muted,
            style = MaterialTheme.typography.labelMedium,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
        )
    }
}

@Composable
private fun ProductScoreBar(product: Product) {
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
        MetricPill("推荐指数", product.displayMatchPercent(), modifier = Modifier.weight(1f))
        MetricPill("口碑评分", product.rating.displayRating(), modifier = Modifier.weight(1f))
    }
}

@Composable
private fun AiTagRow(product: Product, reason: String?) {
    val tags = product.displayFitTags(reason).take(3)
    if (tags.isEmpty()) return
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        tags.forEach { tag ->
            AssistChip(
                onClick = {},
                colors = AssistChipDefaults.assistChipColors(containerColor = BuyWiseTheme.colors.primarySoft),
                label = { Text(tag, maxLines = 1, overflow = TextOverflow.Ellipsis) },
                leadingIcon = {
                    Icon(Icons.Outlined.AutoAwesome, contentDescription = null)
                },
            )
        }
    }
}

@Composable
private fun ProductCommerceSignals(product: Product) {
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        SoftTag(product.displayPlatform())
        SoftTag(product.displaySales())
    }
}

@Composable
fun SoftTag(label: String, modifier: Modifier = Modifier) {
    Text(
        label,
        modifier = modifier
            .background(BuyWiseTheme.colors.primarySoft, RoundedCornerShape(BuyWiseDimens.ChipRadius.dp))
            .border(1.dp, BuyWiseTheme.colors.border, RoundedCornerShape(BuyWiseDimens.ChipRadius.dp))
            .padding(horizontal = 10.dp, vertical = 6.dp),
        color = BuyWiseTheme.colors.primary,
        style = MaterialTheme.typography.labelMedium,
        maxLines = 1,
        overflow = TextOverflow.Ellipsis,
    )
}

@Composable
fun MetricPill(label: String, value: String, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .defaultMinSize(minHeight = 68.dp)
            .background(Color.White, RoundedCornerShape(12.dp))
            .border(1.dp, BuyWiseTheme.colors.border, RoundedCornerShape(12.dp))
            .padding(horizontal = 14.dp, vertical = 12.dp),
    ) {
        Text(label, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.labelMedium)
        Spacer(modifier = Modifier.height(2.dp))
        Text(value, fontWeight = FontWeight.Bold, color = BuyWiseTheme.colors.ink)
    }
}
