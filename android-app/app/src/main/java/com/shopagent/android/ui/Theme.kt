package com.shopagent.android.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

object ShopAgentTheme {
    val colors = AccentColors()
}

data class AccentColors(
    val surface: Color = Color(0xFFF8FAFC),
    val panel: Color = Color.White,
    val primary: Color = Color(0xFF2563EB),
    val secondary: Color = Color(0xFF0F766E),
    val accent: Color = Color(0xFFF59E0B),
    val ink: Color = Color(0xFF0F172A),
    val muted: Color = Color(0xFF475569),
)

@Composable
fun ShopAgentTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = lightColorScheme(
            primary = ShopAgentTheme.colors.primary,
            secondary = ShopAgentTheme.colors.secondary,
            tertiary = ShopAgentTheme.colors.accent,
            surface = ShopAgentTheme.colors.surface,
            background = ShopAgentTheme.colors.surface,
        ),
        content = content,
    )
}
