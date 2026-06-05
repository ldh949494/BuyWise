package com.buywise.android.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.outlined.Check
import androidx.compose.material.icons.outlined.FavoriteBorder
import androidx.compose.material.icons.outlined.Search
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.buywise.android.data.Product
import com.buywise.android.ui.BuyWiseIcons
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.displayPrice
import com.buywise.android.ui.displayRating
import com.buywise.android.ui.shortName

@Composable
fun ShowcaseTopBar(
    title: String,
    modifier: Modifier = Modifier,
    onBack: (() -> Unit)? = null,
    leadingIcon: ImageVector? = null,
    actionIcon: ImageVector? = null,
    actionDescription: String? = null,
    onAction: (() -> Unit)? = null,
    extraAction: (@Composable () -> Unit)? = null,
) {
    Row(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(12.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        when {
            onBack != null -> TactileIconTile(
                icon = Icons.AutoMirrored.Outlined.ArrowBack,
                contentDescription = "返回",
                size = 42.dp,
                iconSize = 22.dp,
                rounded = true,
                tone = TactileIconTone.Neutral,
                onClick = onBack,
            )
            leadingIcon != null -> TactileIconTile(
                icon = leadingIcon,
                contentDescription = null,
                size = 42.dp,
                iconSize = 22.dp,
                rounded = true,
                tone = TactileIconTone.Primary,
            )
        }
        Text(
            title,
            modifier = Modifier.weight(1f),
            style = MaterialTheme.typography.titleLarge,
            color = BuyWiseTheme.colors.ink,
            fontWeight = FontWeight.Bold,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
        )
        if (actionIcon != null) {
            TactileIconTile(
                icon = actionIcon,
                contentDescription = actionDescription,
                size = 42.dp,
                iconSize = 21.dp,
                rounded = true,
                tone = TactileIconTone.Neutral,
                onClick = onAction,
            )
        }
        extraAction?.invoke()
    }
}

@Composable
fun SearchPill(
    text: String,
    modifier: Modifier = Modifier,
    trailingIcon: ImageVector = BuyWiseIcons.Speech,
    trailingTone: TactileIconTone = TactileIconTone.SolidPrimary,
    onTrailingClick: (() -> Unit)? = null,
) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(999.dp),
        color = BuyWiseTheme.colors.panel,
        border = BorderStroke(1.dp, BuyWiseTheme.colors.panelHighlight),
        shadowElevation = 6.dp,
    ) {
        Row(
            modifier = Modifier.padding(start = 14.dp, top = 8.dp, end = 8.dp, bottom = 8.dp),
            horizontalArrangement = Arrangement.spacedBy(10.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(Icons.Outlined.Search, contentDescription = null, tint = BuyWiseTheme.colors.muted)
            Text(
                text,
                modifier = Modifier.weight(1f),
                color = BuyWiseTheme.colors.muted,
                style = MaterialTheme.typography.bodyMedium,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
            TactileIconTile(
                icon = trailingIcon,
                contentDescription = null,
                size = 40.dp,
                iconSize = 20.dp,
                rounded = true,
                tone = trailingTone,
                onClick = onTrailingClick,
            )
        }
    }
}

@Composable
fun CategoryShortcut(
    label: String,
    icon: ImageVector,
    modifier: Modifier = Modifier,
    tone: TactileIconTone = TactileIconTone.Primary,
    onClick: (() -> Unit)? = null,
) {
    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(7.dp),
    ) {
        TactileIconTile(
            icon = icon,
            contentDescription = label,
            size = 56.dp,
            iconSize = 25.dp,
            tone = tone,
            onClick = onClick,
        )
        Text(
            label,
            color = BuyWiseTheme.colors.ink,
            style = MaterialTheme.typography.labelMedium,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
        )
    }
}

@Composable
fun FloatingAssetBadge(
    icon: ImageVector,
    contentDescription: String?,
    modifier: Modifier = Modifier,
    tone: TactileIconTone = TactileIconTone.Primary,
    size: Dp = 58.dp,
    iconSize: Dp = 28.dp,
) {
    Box(modifier = modifier.size(size + 8.dp), contentAlignment = Alignment.Center) {
        Surface(
            modifier = Modifier
                .matchParentSize()
                .offset(y = 4.dp),
            shape = RoundedCornerShape(18.dp),
            color = BuyWiseTheme.colors.primary.copy(alpha = 0.08f),
        ) {}
        TactileIconTile(
            icon = icon,
            contentDescription = contentDescription,
            size = size,
            iconSize = iconSize,
            tone = tone,
        )
    }
}

@Composable
fun ShowcaseProductCard(
    product: Product,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    selected: Boolean = false,
    score: Int? = null,
    showFavorite: Boolean = true,
) {
    FloatingGlassCard(
        modifier = modifier,
        tone = if (selected) FloatingGlassTone.Primary else FloatingGlassTone.Neutral,
        radius = 14.dp,
        fillMaxWidth = false,
        contentPadding = 10.dp,
        elevated = selected,
        onClick = onClick,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
                if (showFavorite) {
                    Icon(
                        Icons.Outlined.FavoriteBorder,
                        contentDescription = null,
                        tint = BuyWiseTheme.colors.muted,
                        modifier = Modifier.size(20.dp),
                    )
                }
            }
            ProductImagePreview(product = product, modifier = Modifier.fillMaxWidth().height(74.dp))
            Text(
                product.shortName(),
                color = BuyWiseTheme.colors.ink,
                style = MaterialTheme.typography.labelMedium,
                fontWeight = FontWeight.Bold,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
            )
            Text(
                product.price.displayPrice(),
                color = BuyWiseTheme.colors.ink,
                style = MaterialTheme.typography.labelMedium,
                fontWeight = FontWeight.Bold,
            )
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                RatingPill(product.rating.displayRating())
                score?.let { ScoreBadge(it, size = 40.dp) }
            }
        }
    }
}

@Composable
fun RatingPill(value: String, modifier: Modifier = Modifier) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(999.dp),
        color = BuyWiseTheme.colors.secondarySoft,
    ) {
        Text(
            "★ $value",
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
            color = BuyWiseTheme.colors.secondary,
            style = MaterialTheme.typography.labelMedium,
            fontWeight = FontWeight.Bold,
        )
    }
}

@Composable
fun ScoreBadge(score: Int, modifier: Modifier = Modifier, size: Dp = 52.dp) {
    val tone = when {
        score >= 85 -> BuyWiseTheme.colors.secondary
        score >= 75 -> BuyWiseTheme.colors.accent
        else -> BuyWiseTheme.colors.danger
    }
    val label = when {
        score >= 85 -> "优秀"
        score >= 75 -> "良好"
        else -> "留意"
    }
    Surface(
        modifier = modifier.size(size),
        shape = CircleShape,
        color = tone.copy(alpha = 0.12f),
        border = BorderStroke(1.dp, tone.copy(alpha = 0.22f)),
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
        ) {
            Text(score.toString(), color = tone, fontWeight = FontWeight.Bold)
            Text(label, color = tone, style = MaterialTheme.typography.labelMedium)
        }
    }
}

@Composable
fun StatusChecklistRow(label: String, status: String, done: Boolean, modifier: Modifier = Modifier) {
    Row(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Surface(
            shape = CircleShape,
            color = if (done) BuyWiseTheme.colors.secondarySoft else BuyWiseTheme.colors.primarySoft,
            modifier = Modifier.size(24.dp),
        ) {
            Box(contentAlignment = Alignment.Center) {
                Icon(
                    if (done) Icons.Outlined.Check else BuyWiseIcons.Guide,
                    contentDescription = null,
                    tint = if (done) BuyWiseTheme.colors.secondary else BuyWiseTheme.colors.primary,
                    modifier = Modifier.size(14.dp),
                )
            }
        }
        Text(
            label,
            modifier = Modifier.weight(1f),
            color = BuyWiseTheme.colors.ink,
            style = MaterialTheme.typography.bodyMedium,
        )
        Text(status, color = BuyWiseTheme.colors.primary, style = MaterialTheme.typography.labelMedium)
    }
}

@Composable
fun AdvicePanel(title: String, body: String, modifier: Modifier = Modifier) {
    FloatingGlassCard(
        modifier = modifier,
        tone = FloatingGlassTone.Success,
        radius = 14.dp,
        contentPadding = 14.dp,
    ) {
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp), verticalAlignment = Alignment.CenterVertically) {
            TactileIconTile(
                icon = BuyWiseIcons.Guide,
                contentDescription = null,
                size = 40.dp,
                iconSize = 20.dp,
                tone = TactileIconTone.Success,
            )
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text(title, color = BuyWiseTheme.colors.secondary, fontWeight = FontWeight.Bold)
                Text(
                    body,
                    color = BuyWiseTheme.colors.ink,
                    style = MaterialTheme.typography.bodyMedium,
                    maxLines = 3,
                    overflow = TextOverflow.Ellipsis,
                )
            }
        }
    }
}

@Composable
fun SoftDivider(modifier: Modifier = Modifier) {
    Spacer(
        modifier = modifier
            .fillMaxWidth()
            .height(1.dp)
            .background(BuyWiseTheme.colors.border.copy(alpha = 0.55f)),
    )
}
