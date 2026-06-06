package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.buywise.android.data.AccountState
import com.buywise.android.ui.BuyWiseIcons
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.components.AccountIdentityCard
import com.buywise.android.ui.components.AccountSettingEntryCard
import com.buywise.android.ui.components.TactileIconTone
import com.buywise.android.ui.components.guidePreferencesSummary

@Composable
fun AccountScreen(
    state: AccountState,
    onPhoneChange: (String) -> Unit,
    onCodeChange: (String) -> Unit,
    onRequestOtp: () -> Unit,
    onVerifyOtp: () -> Unit,
    onGuestMode: () -> Unit,
    onLogout: () -> Unit,
    onOpenGuidePreferences: () -> Unit,
    onOpenPersonalization: () -> Unit,
    onOpenGeneralSettings: () -> Unit,
    onOpenPrivacyData: () -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text("我的", style = MaterialTheme.typography.headlineSmall, color = BuyWiseTheme.colors.ink)
            Text("管理账号、导购偏好和后续个性化设置。", color = BuyWiseTheme.colors.muted)
        }
        AccountIdentityCard(
            state = state,
            onPhoneChange = onPhoneChange,
            onCodeChange = onCodeChange,
            onRequestOtp = onRequestOtp,
            onVerifyOtp = onVerifyOtp,
            onGuestMode = onGuestMode,
            onLogout = onLogout,
        )
        AccountSettingEntryCard(
            title = "导购偏好",
            summary = guidePreferencesSummary(state.guidePreferences),
            icon = BuyWiseIcons.Tune,
            tone = TactileIconTone.Primary,
            onClick = onOpenGuidePreferences,
        )
        AccountSettingEntryCard(
            title = "个性化设置",
            summary = "内容密度、解释显示和默认入口即将支持",
            icon = BuyWiseIcons.Favorite,
            tone = TactileIconTone.Success,
            onClick = onOpenPersonalization,
        )
        AccountSettingEntryCard(
            title = "通用设置",
            summary = "通知、语言和界面偏好即将支持",
            icon = BuyWiseIcons.Notifications,
            tone = TactileIconTone.Neutral,
            onClick = onOpenGeneralSettings,
        )
        AccountSettingEntryCard(
            title = "隐私与数据",
            summary = "偏好数据可管理",
            icon = BuyWiseIcons.Security,
            tone = TactileIconTone.Warm,
            onClick = onOpenPrivacyData,
        )
        state.preferencesError?.let { Text(it, color = BuyWiseTheme.colors.danger) }
        state.statusMessage?.let { Text(it, color = BuyWiseTheme.colors.primary) }
        state.errorMessage?.let { Text(it, color = BuyWiseTheme.colors.danger) }
    }
}
