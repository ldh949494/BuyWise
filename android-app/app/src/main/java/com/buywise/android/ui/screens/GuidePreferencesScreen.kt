package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.CloudOff
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.buywise.android.data.AccountState
import com.buywise.android.ui.BuyWiseIcons
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.components.FloatingGlassCard
import com.buywise.android.ui.components.FloatingGlassTone
import com.buywise.android.ui.components.GuidePreferencesPanel
import com.buywise.android.ui.components.ShowcaseTopBar

@Composable
fun GuidePreferencesScreen(
    state: AccountState,
    onBack: () -> Unit,
    onBudgetPolicyChange: (String) -> Unit,
    onPresentationStyleChange: (String) -> Unit,
    onPriorityTagToggle: (String) -> Unit,
    onExcludedTagToggle: (String) -> Unit,
    onOwnedCategoryToggle: (String) -> Unit,
    onBundleBudgetMaxChange: (String) -> Unit,
    onClearGuidePreferences: () -> Unit,
) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(18.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        item {
            ShowcaseTopBar(
                title = "导购偏好",
                onBack = onBack,
                actionIcon = BuyWiseIcons.Tune,
                actionDescription = "导购偏好",
            )
        }
        item {
            Text(
                "用于影响 AI 推荐、方案组合和回答呈现方式。",
                color = BuyWiseTheme.colors.muted,
                style = MaterialTheme.typography.bodyMedium,
            )
        }
        item {
            GuidePreferencesPanel(
                preferences = state.guidePreferences,
                enabled = !state.preferencesLoading,
                onBudgetPolicyChange = onBudgetPolicyChange,
                onPresentationStyleChange = onPresentationStyleChange,
                onPriorityTagToggle = onPriorityTagToggle,
                onExcludedTagToggle = onExcludedTagToggle,
                onOwnedCategoryToggle = onOwnedCategoryToggle,
                onBundleBudgetMaxChange = onBundleBudgetMaxChange,
                onClear = onClearGuidePreferences,
            )
        }
        state.preferencesError?.let { message ->
            item {
                PreferenceSyncNotice(message = message)
            }
        }
        state.statusMessage?.let { message ->
            item {
                Text(message, color = BuyWiseTheme.colors.primary, style = MaterialTheme.typography.bodyMedium)
            }
        }
        state.errorMessage?.let { message ->
            item {
                Text(message, color = BuyWiseTheme.colors.danger, style = MaterialTheme.typography.bodyMedium)
            }
        }
    }
}

@Composable
private fun PreferenceSyncNotice(message: String) {
    FloatingGlassCard(
        modifier = Modifier.fillMaxWidth(),
        tone = FloatingGlassTone.Neutral,
        contentPadding = 14.dp,
        elevated = false,
    ) {
        Row(
            horizontalArrangement = Arrangement.spacedBy(10.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(Icons.Outlined.CloudOff, contentDescription = null, tint = BuyWiseTheme.colors.muted, modifier = Modifier.size(20.dp))
            Text(
                "偏好暂未同步，将继续使用当前设置。",
                color = BuyWiseTheme.colors.muted,
                style = MaterialTheme.typography.bodyMedium,
                modifier = Modifier.weight(1f),
            )
        }
    }
}
