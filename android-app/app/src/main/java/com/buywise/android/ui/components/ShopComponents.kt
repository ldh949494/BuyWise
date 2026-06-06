package com.buywise.android.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
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
                product.displayRecommendationReason(recommendationReason),
                color = BuyWiseTheme.colors.muted,
                style = MaterialTheme.typography.bodyMedium,
                maxLines = 3,
                overflow = TextOverflow.Ellipsis,
            )
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
                        Text("已加入对比")
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
