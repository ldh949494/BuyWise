package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.Icon
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.buywise.android.ui.BuyWiseIcons
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.components.AccountSettingEntryCard
import com.buywise.android.ui.components.SettingPlaceholderCard
import com.buywise.android.ui.components.ShowcaseTopBar
import com.buywise.android.ui.components.TactileIconTone

@Composable
fun SettingsPlaceholderScreen(
    title: String,
    body: String,
    onBack: () -> Unit,
) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(18.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        item {
            ShowcaseTopBar(
                title = title,
                onBack = onBack,
                actionIcon = BuyWiseIcons.Tune,
                actionDescription = title,
            )
        }
        item {
            SettingPlaceholderCard(
                title = title,
                body = body,
                icon = BuyWiseIcons.Tune,
            )
        }
    }
}

@Composable
fun PrivacyDataScreen(
    onBack: () -> Unit,
    onClearGuidePreferences: () -> Unit,
) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(18.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        item {
            ShowcaseTopBar(
                title = "隐私与数据",
                onBack = onBack,
                actionIcon = BuyWiseIcons.Security,
                actionDescription = "隐私与数据",
            )
        }
        item {
            AccountSettingEntryCard(
                title = "导购偏好数据",
                summary = "清除预算策略、偏好标签、排除项和已有设备。",
                icon = BuyWiseIcons.Tune,
                tone = TactileIconTone.Warm,
                onClick = onClearGuidePreferences,
            )
        }
        item {
            OutlinedButton(onClick = onClearGuidePreferences) {
                Icon(BuyWiseIcons.Clear, contentDescription = null)
                Text("清除导购偏好")
            }
        }
        item {
            SettingPlaceholderCard(
                title = "更多数据管理",
                body = "浏览记录、对比记录、识图记录和反馈记录会在后续版本集中管理。",
                icon = BuyWiseIcons.Security,
            )
        }
    }
}
