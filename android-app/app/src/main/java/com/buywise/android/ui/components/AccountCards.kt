package com.buywise.android.ui.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.Login
import androidx.compose.material.icons.automirrored.outlined.Logout
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.buywise.android.data.AccountState
import com.buywise.android.data.GuidePreferences
import com.buywise.android.ui.BuyWiseDimens
import com.buywise.android.ui.BuyWiseIcons
import com.buywise.android.ui.BuyWiseTheme

@Composable
fun AccountIdentityCard(
    state: AccountState,
    onPhoneChange: (String) -> Unit,
    onCodeChange: (String) -> Unit,
    onRequestOtp: () -> Unit,
    onVerifyOtp: () -> Unit,
    onGuestMode: () -> Unit,
    onLogout: () -> Unit,
    modifier: Modifier = Modifier,
) {
    FloatingGlassCard(
        modifier = modifier,
        tone = if (state.isLoggedIn) FloatingGlassTone.Success else FloatingGlassTone.Neutral,
        radius = BuyWiseDimens.CardRadius.dp,
        contentPadding = 18.dp,
    ) {
        if (state.isLoggedIn) {
            LoggedInAccountContent(state = state, onLogout = onLogout)
        } else {
            GuestAccountContent(
                state = state,
                onPhoneChange = onPhoneChange,
                onCodeChange = onCodeChange,
                onRequestOtp = onRequestOtp,
                onVerifyOtp = onVerifyOtp,
                onGuestMode = onGuestMode,
            )
        }
    }
}

@Composable
fun AccountSettingEntryCard(
    title: String,
    summary: String,
    icon: ImageVector,
    tone: TactileIconTone,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    FloatingGlassCard(
        modifier = modifier,
        tone = FloatingGlassTone.Neutral,
        radius = BuyWiseDimens.CardRadius.dp,
        elevated = false,
        contentPadding = 16.dp,
        onClick = onClick,
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            TactileIconTile(
                icon = icon,
                contentDescription = null,
                size = 48.dp,
                iconSize = 22.dp,
                tone = tone,
            )
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text(title, color = BuyWiseTheme.colors.ink, style = MaterialTheme.typography.titleMedium)
                Text(
                    summary,
                    color = BuyWiseTheme.colors.muted,
                    style = MaterialTheme.typography.bodyMedium,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
            }
            Text("›", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.titleLarge)
        }
    }
}

fun guidePreferencesSummary(preferences: GuidePreferences): String {
    val deviceCount = preferences.ownedCategories.size
    val parts = listOf(
        budgetPolicyLabel(preferences.budgetPolicy),
        presentationStyleLabel(preferences.presentationStyle),
        if (deviceCount > 0) "已有设备 $deviceCount 项" else "未设置已有设备",
    )
    return parts.joinToString(" · ")
}

@Composable
private fun LoggedInAccountContent(state: AccountState, onLogout: () -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            TactileIconTile(
                icon = BuyWiseIcons.Account,
                contentDescription = null,
                tone = TactileIconTone.Success,
            )
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text("账号", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.labelMedium)
                Text(
                    state.phoneMasked.orEmpty(),
                    color = BuyWiseTheme.colors.ink,
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold,
                )
            }
            EvidenceTag("已登录", tone = EvidenceTone.Success)
        }
        OutlinedButton(onClick = onLogout, enabled = !state.isLoading, modifier = Modifier.fillMaxWidth()) {
            Icon(Icons.AutoMirrored.Outlined.Logout, contentDescription = null)
            Spacer(Modifier.width(8.dp))
            Text("退出登录")
        }
    }
}

@Composable
private fun GuestAccountContent(
    state: AccountState,
    onPhoneChange: (String) -> Unit,
    onCodeChange: (String) -> Unit,
    onRequestOtp: () -> Unit,
    onVerifyOtp: () -> Unit,
    onGuestMode: () -> Unit,
) {
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
            TactileIconTile(
                icon = BuyWiseIcons.Account,
                contentDescription = null,
                tone = TactileIconTone.Primary,
            )
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text("登录账号", style = MaterialTheme.typography.titleLarge, color = BuyWiseTheme.colors.ink)
                Text("同步导购偏好、反馈记录和后续购物设置。", color = BuyWiseTheme.colors.muted)
            }
        }
        OutlinedTextField(
            value = state.phoneInput,
            onValueChange = onPhoneChange,
            label = { Text("手机号") },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone),
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
        )
        OutlinedTextField(
            value = state.codeInput,
            onValueChange = onCodeChange,
            label = { Text("验证码") },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
        )
        state.debugOtp?.let { Text("测试验证码：$it", color = BuyWiseTheme.colors.primary) }
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.fillMaxWidth()) {
            OutlinedButton(onClick = onRequestOtp, enabled = !state.isLoading, modifier = Modifier.weight(1f)) {
                Text("获取验证码")
            }
            Button(onClick = onVerifyOtp, enabled = !state.isLoading, modifier = Modifier.weight(1f)) {
                Icon(Icons.AutoMirrored.Outlined.Login, contentDescription = null)
                Spacer(Modifier.width(6.dp))
                Text("登录")
            }
        }
        OutlinedButton(
            onClick = onGuestMode,
            enabled = !state.isLoading && state.canUseGuestMode,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Icon(BuyWiseIcons.Account, contentDescription = null)
            Spacer(Modifier.width(8.dp))
            Text("游客体验")
        }
    }
}

@Composable
fun SettingPlaceholderCard(
    title: String,
    body: String,
    icon: ImageVector,
    modifier: Modifier = Modifier,
) {
    FloatingGlassCard(
        modifier = modifier,
        tone = FloatingGlassTone.Primary,
        radius = BuyWiseDimens.CardRadius.dp,
        contentPadding = 18.dp,
    ) {
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
            TactileIconTile(icon = icon, contentDescription = null, tone = TactileIconTone.Primary)
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(5.dp)) {
                Text(title, color = BuyWiseTheme.colors.ink, style = MaterialTheme.typography.titleLarge)
                Text(body, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
            }
        }
        Spacer(Modifier.height(12.dp))
        EvidenceTag("即将支持", tone = EvidenceTone.Info)
    }
}

private fun budgetPolicyLabel(value: String): String = when (value) {
    "strict" -> "严格预算"
    "quality_first" -> "品质优先"
    else -> "小幅超预算"
}

private fun presentationStyleLabel(value: String): String = when (value) {
    "direct_answer" -> "直接结论"
    "detailed_explanation" -> "解释详细"
    else -> "多方案对比"
}
