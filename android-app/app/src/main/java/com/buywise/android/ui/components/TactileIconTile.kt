package com.buywise.android.ui.components

import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.animateDpAsState
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Icon
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.draw.clip
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.annotation.DrawableRes
import androidx.compose.foundation.Image
import com.buywise.android.ui.BuyWiseTheme

enum class TactileIconTone {
    Neutral,
    Primary,
    Warm,
    Success,
    SolidPrimary,
}

@Composable
fun TactileIconTile(
    icon: ImageVector,
    contentDescription: String?,
    modifier: Modifier = Modifier,
    tone: TactileIconTone = TactileIconTone.Primary,
    size: Dp = 52.dp,
    iconSize: Dp = 24.dp,
    rounded: Boolean = false,
    selected: Boolean = false,
    enabled: Boolean = true,
    onClick: (() -> Unit)? = null,
) {
    val interactionSource = remember { MutableInteractionSource() }
    val isPressed by interactionSource.collectIsPressedAsState()
    val motionEnabled = rememberBuyWiseMotionEnabled()
    val haptic = LocalHapticFeedback.current
    val activePress = enabled && onClick != null && isPressed
    val scale by animateFloatAsState(
        targetValue = if (activePress && motionEnabled) 0.92f else 1f,
        animationSpec = tween(durationMillis = if (activePress) 90 else 170, easing = FastOutSlowInEasing),
        label = "tactileIconScale",
    )
    val elevation by animateDpAsState(
        targetValue = when {
            !enabled -> 0.dp
            activePress -> 2.dp
            selected -> 9.dp
            else -> 6.dp
        },
        animationSpec = tween(durationMillis = if (activePress) 90 else 170, easing = FastOutSlowInEasing),
        label = "tactileIconElevation",
    )
    val colors = tactileIconColors(tone, enabled)
    val shape: Shape = if (rounded) CircleShape else RoundedCornerShape(14.dp)
    val clickModifier = if (onClick == null) {
        Modifier
    } else {
        Modifier.clickable(
            enabled = enabled,
            interactionSource = interactionSource,
            indication = null,
            onClick = {
                haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                onClick()
            },
        )
    }

    Surface(
        modifier = modifier
            .size(size)
            .graphicsLayer {
                scaleX = scale
                scaleY = scale
                translationY = if (activePress && motionEnabled) 1.5.dp.toPx() else 0f
            }
            .then(clickModifier),
        shape = shape,
        color = colors.container,
        border = BorderStroke(1.dp, colors.border),
        shadowElevation = elevation,
        tonalElevation = 0.dp,
    ) {
        Box(contentAlignment = Alignment.Center) {
            Icon(
                icon,
                contentDescription = contentDescription,
                tint = colors.foreground,
                modifier = Modifier.size(iconSize).padding(0.dp),
            )
        }
    }
}

@Composable
fun TactileIconTile(
    @DrawableRes assetRes: Int,
    contentDescription: String?,
    modifier: Modifier = Modifier,
    tone: TactileIconTone = TactileIconTone.Primary,
    size: Dp = 52.dp,
    iconSize: Dp = 34.dp,
    rounded: Boolean = false,
    selected: Boolean = false,
    enabled: Boolean = true,
    onClick: (() -> Unit)? = null,
) {
    val interactionSource = remember { MutableInteractionSource() }
    val isPressed by interactionSource.collectIsPressedAsState()
    val motionEnabled = rememberBuyWiseMotionEnabled()
    val haptic = LocalHapticFeedback.current
    val activePress = enabled && onClick != null && isPressed
    val scale by animateFloatAsState(
        targetValue = if (activePress && motionEnabled) 0.92f else 1f,
        animationSpec = tween(durationMillis = if (activePress) 90 else 170, easing = FastOutSlowInEasing),
        label = "tactileAssetScale",
    )
    val elevation by animateDpAsState(
        targetValue = when {
            !enabled -> 0.dp
            activePress -> 2.dp
            selected -> 9.dp
            else -> 6.dp
        },
        animationSpec = tween(durationMillis = if (activePress) 90 else 170, easing = FastOutSlowInEasing),
        label = "tactileAssetElevation",
    )
    val colors = tactileIconColors(tone, enabled)
    val shape: Shape = if (rounded) CircleShape else RoundedCornerShape(14.dp)
    val clickModifier = if (onClick == null) {
        Modifier
    } else {
        Modifier.clickable(
            enabled = enabled,
            interactionSource = interactionSource,
            indication = null,
            onClick = {
                haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                onClick()
            },
        )
    }

    Surface(
        modifier = modifier
            .size(size)
            .graphicsLayer {
                scaleX = scale
                scaleY = scale
                translationY = if (activePress && motionEnabled) 1.5.dp.toPx() else 0f
            }
            .then(clickModifier),
        shape = shape,
        color = colors.container,
        border = BorderStroke(1.dp, colors.border),
        shadowElevation = elevation,
        tonalElevation = 0.dp,
    ) {
        Box(contentAlignment = Alignment.Center) {
            Image(
                painter = painterResource(id = assetRes),
                contentDescription = contentDescription,
                contentScale = ContentScale.Fit,
                modifier = Modifier.size(iconSize).clip(shape),
            )
        }
    }
}

@Composable
private fun tactileIconColors(tone: TactileIconTone, enabled: Boolean): TactileIconColors {
    if (!enabled) {
        return TactileIconColors(
            container = BuyWiseTheme.colors.panelAlt,
            foreground = BuyWiseTheme.colors.muted,
            border = BuyWiseTheme.colors.border.copy(alpha = 0.72f),
        )
    }
    return when (tone) {
        TactileIconTone.Neutral -> TactileIconColors(
            container = BuyWiseTheme.colors.panelRaised,
            foreground = BuyWiseTheme.colors.ink,
            border = BuyWiseTheme.colors.panelHighlight,
        )
        TactileIconTone.Primary -> TactileIconColors(
            container = BuyWiseTheme.colors.primarySoft,
            foreground = BuyWiseTheme.colors.primary,
            border = BuyWiseTheme.colors.panelHighlight,
        )
        TactileIconTone.Warm -> TactileIconColors(
            container = BuyWiseTheme.colors.accentSoft,
            foreground = BuyWiseTheme.colors.accent,
            border = BuyWiseTheme.colors.panelHighlight,
        )
        TactileIconTone.Success -> TactileIconColors(
            container = BuyWiseTheme.colors.secondarySoft,
            foreground = BuyWiseTheme.colors.secondary,
            border = BuyWiseTheme.colors.panelHighlight,
        )
        TactileIconTone.SolidPrimary -> TactileIconColors(
            container = BuyWiseTheme.colors.primary,
            foreground = Color.White,
            border = Color.White.copy(alpha = 0.48f),
        )
    }
}

private data class TactileIconColors(
    val container: Color,
    val foreground: Color,
    val border: Color,
)
