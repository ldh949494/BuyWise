package com.buywise.android.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
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
import androidx.compose.material3.Button
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
import androidx.compose.ui.draw.scale
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.foundation.Image
import coil3.compose.AsyncImage
import com.buywise.android.data.Product
import com.buywise.android.ui.BuyWiseDimens
import com.buywise.android.ui.BuyWiseIcons
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.BuyWiseVisualAssets
import com.buywise.android.ui.displayPrice
import com.buywise.android.ui.displayRating
import com.buywise.android.ui.displayRecommendationReason
import kotlinx.coroutines.delay

@Composable
fun SectionTitle(title: String, subtitle: String? = null) {
    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
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
    isFeatured: Boolean = false,
) {
    var comparePressed by remember { mutableStateOf(false) }
    val motionEnabled = rememberBuyWiseMotionEnabled()
    val haptic = LocalHapticFeedback.current
    val compareScale by animateFloatAsState(
        targetValue = if (comparePressed && motionEnabled) 0.94f else 1f,
        label = "productCompareButtonScale",
    )
    LaunchedEffect(comparePressed) {
        if (comparePressed) {
            delay(160)
            comparePressed = false
        }
    }
    val cardTone = when {
        isInCompareBasket -> FloatingGlassTone.Success
        isFeatured -> FloatingGlassTone.Primary
        else -> FloatingGlassTone.Neutral
    }
    FloatingGlassCard(
        modifier = Modifier.fillMaxWidth(),
        tone = cardTone,
        elevated = isFeatured || isInCompareBasket,
        onClick = onClick,
    ) {
        Column(
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            if (isFeatured || isInCompareBasket) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    if (isFeatured) {
                        EvidenceTag("首推候选", tone = EvidenceTone.Info)
                    }
                    if (isInCompareBasket) {
                        EvidenceTag("已进入对比", tone = EvidenceTone.Success)
                    }
                }
            }
            Row(
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                modifier = Modifier.fillMaxWidth(),
            ) {
                ProductImagePreview(
                    product = product,
                    modifier = Modifier.size(width = 96.dp, height = 104.dp),
                )
                Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text(
                        product.name,
                        style = MaterialTheme.typography.titleMedium,
                        color = BuyWiseTheme.colors.ink,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis,
                    )
                    Row(
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Text(product.price.displayPrice(), color = BuyWiseTheme.colors.primary, style = MaterialTheme.typography.titleLarge)
                        Row(horizontalArrangement = Arrangement.spacedBy(4.dp), verticalAlignment = Alignment.CenterVertically) {
                            Text("★", color = BuyWiseTheme.colors.accent, fontWeight = FontWeight.Bold)
                            Text(product.rating.displayRating(), color = BuyWiseTheme.colors.ink, fontWeight = FontWeight.Bold)
                        }
                    }
                }
            }
            Text(
                if (isFeatured) "为什么先看：${product.displayRecommendationReason(recommendationReason)}"
                else product.displayRecommendationReason(recommendationReason),
                color = BuyWiseTheme.colors.muted,
                style = MaterialTheme.typography.bodyMedium,
                maxLines = 3,
                overflow = TextOverflow.Ellipsis,
            )
            ProductDecisionSignals(product = product)
            if (onToggleCompare != null) {
                if (isInCompareBasket) {
                    Button(
                        onClick = {
                            comparePressed = true
                            haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                            onToggleCompare()
                        },
                        modifier = Modifier.fillMaxWidth().scale(compareScale),
                    ) {
                        Icon(BuyWiseIcons.Compare, contentDescription = null)
                        Spacer(modifier = Modifier.width(6.dp))
                        Text("已选入对比")
                    }
                } else {
                    OutlinedButton(
                        onClick = {
                            comparePressed = true
                            haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                            onToggleCompare()
                        },
                        modifier = Modifier.fillMaxWidth().scale(compareScale),
                    ) {
                        Icon(BuyWiseIcons.Compare, contentDescription = null)
                        Spacer(modifier = Modifier.width(6.dp))
                        Text("加入对比")
                    }
                }
            }
        }
    }
}

@Composable
fun ProvisionalProductCard(
    product: Product,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    compact: Boolean = false,
) {
    FloatingGlassCard(
        modifier = modifier,
        tone = FloatingGlassTone.Neutral,
        radius = 12.dp,
        elevated = false,
        fillMaxWidth = !compact,
        contentPadding = if (compact) 10.dp else 14.dp,
        onClick = onClick,
    ) {
        if (compact) {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                ProductImagePreview(product = product, modifier = Modifier.size(width = 72.dp, height = 60.dp))
                EvidenceTag("相关商品", tone = EvidenceTone.Info)
                Text(
                    product.name,
                    color = BuyWiseTheme.colors.ink,
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.Bold,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis,
                )
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                    Text(product.price.displayPrice(), color = BuyWiseTheme.colors.primary, fontWeight = FontWeight.Bold)
                    Text("评分 ${product.rating.displayRating()}", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.labelMedium)
                }
                ProvisionalEvidenceTags(product = product, maxTags = 1)
            }
        } else {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {
                    ProductImagePreview(
                        product = product,
                        modifier = Modifier.size(width = 82.dp, height = 88.dp),
                    )
                    Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        EvidenceTag("相关商品", tone = EvidenceTone.Info)
                        Text(
                            product.name,
                            style = MaterialTheme.typography.titleMedium,
                            color = BuyWiseTheme.colors.ink,
                            maxLines = 2,
                            overflow = TextOverflow.Ellipsis,
                        )
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            Text(product.price.displayPrice(), color = BuyWiseTheme.colors.primary, style = MaterialTheme.typography.titleMedium)
                            Text("评分 ${product.rating.displayRating()}", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.labelMedium)
                        }
                    }
                }
                Text(
                    "方案生成中，推荐理由稍后补齐。",
                    color = BuyWiseTheme.colors.muted,
                    style = MaterialTheme.typography.bodyMedium,
                )
                ProvisionalEvidenceTags(product = product, maxTags = 2)
            }
        }
    }
}

@Composable
private fun ProductDecisionSignals(product: Product) {
    val caution = product.cautions.firstOrNull { it.isNotBlank() }
    val hasEvidence = product.productUrl?.isNotBlank() == true ||
        product.reviewSummary?.isNotBlank() == true ||
        product.price != null ||
        product.stockStatus?.isNotBlank() == true
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
        product.stockStatus?.takeIf { it.isNotBlank() }?.let {
            EvidenceTag(it, tone = EvidenceTone.Success)
        }
        product.tags.take(2).forEach { tag ->
            EvidenceTag(tag, tone = EvidenceTone.Info)
        }
        if (!hasEvidence) {
            EvidenceTag("证据较少，建议核实", tone = EvidenceTone.Warning)
        }
    }
    caution?.let {
        Text(
            "购买前注意：$it",
            color = BuyWiseTheme.colors.danger,
            style = MaterialTheme.typography.bodySmall,
            maxLines = 2,
            overflow = TextOverflow.Ellipsis,
        )
    }
}

@Composable
private fun ProvisionalEvidenceTags(product: Product, maxTags: Int) {
    val labels = buildList {
        if (product.price != null || product.stockStatus?.isNotBlank() == true) {
            add("价格/库存快照" to EvidenceTone.Success)
        }
        product.productUrl?.takeIf { it.isNotBlank() }?.let {
            add("真实商品页" to EvidenceTone.Info)
        }
        product.reviewSummary?.takeIf { it.isNotBlank() }?.let {
            add("评价摘要" to EvidenceTone.Info)
        }
        product.tags.take(2).forEach { tag ->
            add(tag to EvidenceTone.Info)
        }
    }.take(maxTags)
    if (labels.isEmpty()) {
        return
    }
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        labels.forEach { (label, tone) ->
            EvidenceTag(label, tone = tone)
        }
    }
}

@Composable
fun ProductImagePreview(product: Product, modifier: Modifier = Modifier) {
    val shape = RoundedCornerShape(12.dp)
    val imageUrl = product.imageUrl?.takeIf { it.isNotBlank() }
    var imageLoadFailed by remember(imageUrl) { mutableStateOf(false) }
    Box(
        modifier = modifier
            .clip(shape)
            .background(BuyWiseTheme.colors.panelAlt)
            .border(1.dp, BuyWiseTheme.colors.border, shape),
        contentAlignment = Alignment.Center,
    ) {
        if (imageUrl == null || imageLoadFailed) {
            ImagePlaceholder(product = product)
        } else {
            AsyncImage(
                model = imageUrl,
                contentDescription = product.name,
                modifier = Modifier.fillMaxSize(),
                contentScale = ContentScale.Crop,
                onError = { imageLoadFailed = true },
            )
        }
    }
}

@Composable
private fun ImagePlaceholder(product: Product) {
    Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Image(
            painter = painterResource(id = BuyWiseVisualAssets.Keyboard),
            contentDescription = null,
            modifier = Modifier.size(width = 56.dp, height = 40.dp),
            contentScale = ContentScale.Fit,
        )
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

enum class EvidenceTone {
    Info,
    Success,
    Warning,
    Danger,
}

@Composable
fun EvidenceTag(label: String, modifier: Modifier = Modifier, tone: EvidenceTone = EvidenceTone.Info) {
    val background = when (tone) {
        EvidenceTone.Info -> BuyWiseTheme.colors.primarySoft
        EvidenceTone.Success -> BuyWiseTheme.colors.secondarySoft
        EvidenceTone.Warning -> BuyWiseTheme.colors.accentSoft
        EvidenceTone.Danger -> BuyWiseTheme.colors.dangerSoft
    }
    val foreground = when (tone) {
        EvidenceTone.Info -> BuyWiseTheme.colors.primary
        EvidenceTone.Success -> BuyWiseTheme.colors.secondary
        EvidenceTone.Warning -> BuyWiseTheme.colors.accent
        EvidenceTone.Danger -> BuyWiseTheme.colors.danger
    }
    Text(
        label,
        modifier = modifier
            .background(background, RoundedCornerShape(BuyWiseDimens.ChipRadius.dp))
            .padding(horizontal = 10.dp, vertical = 6.dp),
        color = foreground,
        style = MaterialTheme.typography.labelMedium,
        fontWeight = FontWeight.Bold,
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
