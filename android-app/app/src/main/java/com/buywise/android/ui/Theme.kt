package com.buywise.android.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.DeviceFontFamilyName
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

object BuyWiseTheme {
    val colors = AccentColors()
}

data class AccentColors(
    val surface: Color = Color(0xFFF7FAFF),
    val panel: Color = Color.White,
    val panelAlt: Color = Color(0xFFF3F7FF),
    val primary: Color = Color(0xFF245BFF),
    val primarySoft: Color = Color(0xFFEAF1FF),
    val primaryPressed: Color = Color(0xFF1743D2),
    val secondary: Color = Color(0xFF059669),
    val secondarySoft: Color = Color(0xFFE8FAF2),
    val accent: Color = Color(0xFFD97706),
    val accentSoft: Color = Color(0xFFFFF7ED),
    val ink: Color = Color(0xFF111827),
    val muted: Color = Color(0xFF64748B),
    val border: Color = Color(0xFFDCE5F5),
    val dangerSoft: Color = Color(0xFFFEF2F2),
    val danger: Color = Color(0xFFB91C1C),
)

private val RoundedFontFamily = FontFamily(
    Font(DeviceFontFamilyName("sans-serif-rounded"), FontWeight.Normal),
    Font(DeviceFontFamilyName("sans-serif-rounded"), FontWeight.Medium),
    Font(DeviceFontFamilyName("sans-serif-rounded"), FontWeight.SemiBold),
    Font(DeviceFontFamilyName("sans-serif-rounded"), FontWeight.Bold),
    Font(DeviceFontFamilyName("sans-serif"), FontWeight.Normal),
    Font(DeviceFontFamilyName("sans-serif"), FontWeight.Medium),
    Font(DeviceFontFamilyName("sans-serif"), FontWeight.SemiBold),
    Font(DeviceFontFamilyName("sans-serif"), FontWeight.Bold),
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
                fontFamily = RoundedFontFamily,
                fontSize = 28.sp,
                lineHeight = 36.sp,
                fontWeight = FontWeight.SemiBold,
                letterSpacing = 0.sp,
            ),
            titleLarge = TextStyle(
                fontFamily = RoundedFontFamily,
                fontSize = 21.sp,
                lineHeight = 28.sp,
                fontWeight = FontWeight.SemiBold,
                letterSpacing = 0.sp,
            ),
            titleMedium = TextStyle(
                fontFamily = RoundedFontFamily,
                fontSize = 17.sp,
                lineHeight = 24.sp,
                fontWeight = FontWeight.SemiBold,
                letterSpacing = 0.sp,
            ),
            bodyMedium = TextStyle(
                fontFamily = RoundedFontFamily,
                fontSize = 14.sp,
                lineHeight = 22.sp,
                letterSpacing = 0.sp,
            ),
            labelMedium = TextStyle(
                fontFamily = RoundedFontFamily,
                fontSize = 12.sp,
                lineHeight = 16.sp,
                fontWeight = FontWeight.Medium,
                letterSpacing = 0.sp,
            ),
        ),
        content = content,
    )
}
