package com.buywise.android.ui.components

import android.provider.Settings
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.animateDpAsState
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.buywise.android.ui.BuyWiseDimens
import com.buywise.android.ui.BuyWiseTheme

enum class FloatingGlassTone {
    Neutral,
    Primary,
    Warm,
    Success,
    SolidPrimary,
}

@Composable
fun FloatingGlassCard(
    modifier: Modifier = Modifier,
    tone: FloatingGlassTone = FloatingGlassTone.Neutral,
    radius: Dp = BuyWiseDimens.CardRadius.dp,
    elevated: Boolean = true,
    fillMaxWidth: Boolean = true,
    contentPadding: Dp = 16.dp,
    onClick: (() -> Unit)? = null,
    content: @Composable ColumnScope.() -> Unit,
) {
    val interactionSource = remember { MutableInteractionSource() }
    val isPressed by interactionSource.collectIsPressedAsState()
    val motionEnabled = rememberBuyWiseMotionEnabled()
    val haptic = LocalHapticFeedback.current
    val activePress = isPressed && onClick != null
    val scale by animateFloatAsState(
        targetValue = if (activePress && motionEnabled) 0.965f else 1f,
        animationSpec = tween(durationMillis = if (activePress) 105 else 165, easing = FastOutSlowInEasing),
        label = "floatingGlassScale",
    )
    val shadowElevation by animateDpAsState(
        targetValue = when {
            activePress -> 4.dp
            elevated -> 9.dp
            else -> 3.dp
        },
        animationSpec = tween(durationMillis = if (activePress) 105 else 165, easing = FastOutSlowInEasing),
        label = "floatingGlassElevation",
    )
    val shape = RoundedCornerShape(radius)
    val colors = floatingGlassColors(tone)
    val pressModifier = if (onClick == null) {
        Modifier
    } else {
        Modifier.clickable(
            interactionSource = interactionSource,
            indication = null,
            onClick = {
                haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                onClick()
            },
        )
    }

    val widthModifier = if (fillMaxWidth) Modifier.fillMaxWidth() else Modifier

    Surface(
        modifier = modifier
            .then(widthModifier)
            .graphicsLayer {
                scaleX = scale
                scaleY = scale
                translationY = if (activePress && motionEnabled) 2.dp.toPx() else 0f
            }
            .then(pressModifier),
        shape = shape,
        color = colors.container,
        contentColor = BuyWiseTheme.colors.ink,
        border = BorderStroke(1.dp, colors.border),
        shadowElevation = shadowElevation,
        tonalElevation = 0.dp,
    ) {
        Column(
            modifier = Modifier.padding(contentPadding),
            content = content,
        )
    }
}

@Composable
private fun floatingGlassColors(tone: FloatingGlassTone): FloatingGlassColors =
    when (tone) {
        FloatingGlassTone.Neutral -> FloatingGlassColors(
            container = BuyWiseTheme.colors.panelRaised.copy(alpha = 0.99f),
            border = BuyWiseTheme.colors.border.copy(alpha = 0.72f),
        )
        FloatingGlassTone.Primary -> FloatingGlassColors(
            container = BuyWiseTheme.colors.primarySoft.copy(alpha = 0.96f),
            border = BuyWiseTheme.colors.primary.copy(alpha = 0.16f),
        )
        FloatingGlassTone.Warm -> FloatingGlassColors(
            container = BuyWiseTheme.colors.accentSoft.copy(alpha = 0.97f),
            border = BuyWiseTheme.colors.accent.copy(alpha = 0.16f),
        )
        FloatingGlassTone.Success -> FloatingGlassColors(
            container = BuyWiseTheme.colors.secondarySoft.copy(alpha = 0.97f),
            border = BuyWiseTheme.colors.secondary.copy(alpha = 0.16f),
        )
        FloatingGlassTone.SolidPrimary -> FloatingGlassColors(
            container = BuyWiseTheme.colors.primary,
            border = Color.White.copy(alpha = 0.46f),
        )
    }

private data class FloatingGlassColors(
    val container: Color,
    val border: Color,
)

@Composable
fun rememberBuyWiseMotionEnabled(): Boolean {
    val context = LocalContext.current
    return remember(context) {
        runCatching {
            Settings.Global.getFloat(
                context.contentResolver,
                Settings.Global.ANIMATOR_DURATION_SCALE,
                1f,
            ) != 0f
        }.getOrDefault(true)
    }
}
