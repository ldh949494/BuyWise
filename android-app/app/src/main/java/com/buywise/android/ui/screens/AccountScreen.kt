package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.CloudOff
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.ErrorOutline
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
import com.buywise.android.ui.components.AccountIdentityCard
import com.buywise.android.ui.components.AccountSettingEntryCard
import com.buywise.android.ui.components.FloatingGlassCard
import com.buywise.android.ui.components.FloatingGlassTone
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
        state.preferencesError?.let {
            AccountStatusPanel(
                message = "导购偏好暂未同步，将继续使用本机偏好。",
                type = AccountStatusType.Warning,
            )
        }
        state.statusMessage?.let { message ->
            AccountStatusPanel(message = message, type = AccountStatusType.Success)
        }
        state.errorMessage?.let { message ->
            AccountStatusPanel(message = message, type = AccountStatusType.Error)
        }
    }
}

@Composable
private fun AccountStatusPanel(message: String, type: AccountStatusType) {
    val (icon, iconColor, tone) = when (type) {
        AccountStatusType.Success -> Triple(Icons.Outlined.CheckCircle, BuyWiseTheme.colors.primary, FloatingGlassTone.Success)
        AccountStatusType.Warning -> Triple(Icons.Outlined.CloudOff, BuyWiseTheme.colors.muted, FloatingGlassTone.Neutral)
        AccountStatusType.Error -> Triple(Icons.Outlined.ErrorOutline, BuyWiseTheme.colors.danger, FloatingGlassTone.Warm)
    }
    FloatingGlassCard(
        modifier = Modifier.fillMaxWidth(),
        tone = tone,
        contentPadding = 14.dp,
        elevated = false,
    ) {
        Row(
            horizontalArrangement = Arrangement.spacedBy(10.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(icon, contentDescription = null, tint = iconColor, modifier = Modifier.size(20.dp))
            Text(message, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
        }
    }
}

private enum class AccountStatusType {
    Success,
    Warning,
    Error,
}
