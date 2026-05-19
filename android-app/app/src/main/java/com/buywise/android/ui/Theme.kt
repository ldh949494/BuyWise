package com.buywise.android.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

object BuyWiseTheme {
    val colors = AccentColors()
}

data class AccentColors(
    val surface: Color = Color(0xFFF4F7FA),
    val panel: Color = Color.White,
    val panelAlt: Color = Color(0xFFF8FAFC),
    val primary: Color = Color(0xFF1D4ED8),
    val primarySoft: Color = Color(0xFFEFF6FF),
    val secondary: Color = Color(0xFF047857),
    val secondarySoft: Color = Color(0xFFECFDF5),
    val accent: Color = Color(0xFFD97706),
    val accentSoft: Color = Color(0xFFFFF7ED),
    val ink: Color = Color(0xFF111827),
    val muted: Color = Color(0xFF64748B),
    val border: Color = Color(0xFFE2E8F0),
    val dangerSoft: Color = Color(0xFFFEF2F2),
    val danger: Color = Color(0xFFB91C1C),
)

@Composable
fun BuyWiseTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = lightColorScheme(
            primary = BuyWiseTheme.colors.primary,
            secondary = BuyWiseTheme.colors.secondary,
            tertiary = BuyWiseTheme.colors.accent,
            surface = BuyWiseTheme.colors.surface,
            surfaceVariant = BuyWiseTheme.colors.panelAlt,
            background = BuyWiseTheme.colors.surface,
            outline = BuyWiseTheme.colors.border,
            onSurface = BuyWiseTheme.colors.ink,
            onSurfaceVariant = BuyWiseTheme.colors.muted,
        ),
        typography = Typography(
            headlineMedium = TextStyle(
                fontSize = 28.sp,
                lineHeight = 34.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 0.sp,
            ),
            titleLarge = TextStyle(
                fontSize = 21.sp,
                lineHeight = 27.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 0.sp,
            ),
            titleMedium = TextStyle(
                fontSize = 17.sp,
                lineHeight = 23.sp,
                fontWeight = FontWeight.SemiBold,
                letterSpacing = 0.sp,
            ),
            bodyMedium = TextStyle(
                fontSize = 14.sp,
                lineHeight = 21.sp,
                letterSpacing = 0.sp,
            ),
            labelMedium = TextStyle(
                fontSize = 12.sp,
                lineHeight = 16.sp,
                fontWeight = FontWeight.Medium,
                letterSpacing = 0.sp,
            ),
        ),
        content = content,
    )
}
