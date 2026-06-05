package com.buywise.android.ui.screens

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.Login
import androidx.compose.material.icons.outlined.Person
import androidx.compose.material.icons.outlined.Sms
import androidx.compose.material.icons.outlined.VerifiedUser
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.buywise.android.R
import com.buywise.android.data.AccountState
import com.buywise.android.ui.BuyWiseTheme

@Composable
fun LandingScreen(
    state: AccountState,
    onPhoneChange: (String) -> Unit,
    onCodeChange: (String) -> Unit,
    onRequestOtp: () -> Unit,
    onVerifyOtp: () -> Unit,
    onGuestMode: () -> Unit,
    onContinue: () -> Unit,
) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(BuyWiseTheme.colors.surface)
            .imePadding(),
    ) {
        Image(
            painter = painterResource(id = R.drawable.landing_login_top),
            contentDescription = null,
            modifier = Modifier.fillMaxWidth(),
            contentScale = ContentScale.FillWidth,
            alignment = Alignment.TopCenter,
        )
        LoginPanel(
            state = state,
            onPhoneChange = onPhoneChange,
            onCodeChange = onCodeChange,
            onRequestOtp = onRequestOtp,
            onVerifyOtp = onVerifyOtp,
            onGuestMode = onGuestMode,
            onContinue = onContinue,
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .fillMaxWidth()
                .navigationBarsPadding()
                .padding(horizontal = 20.dp, vertical = 22.dp),
        )
    }
}

@Composable
private fun LoginPanel(
    state: AccountState,
    onPhoneChange: (String) -> Unit,
    onCodeChange: (String) -> Unit,
    onRequestOtp: () -> Unit,
    onVerifyOtp: () -> Unit,
    onGuestMode: () -> Unit,
    onContinue: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(24.dp),
        color = BuyWiseTheme.colors.panel,
        shadowElevation = 10.dp,
        tonalElevation = 2.dp,
    ) {
        Column(
            modifier = Modifier.padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text(
                text = if (state.isLoggedIn) "欢迎回来" else "登录 BuyWise",
                style = MaterialTheme.typography.titleLarge,
                color = BuyWiseTheme.colors.ink,
                fontWeight = FontWeight.SemiBold,
            )
            Text(
                text = if (state.isLoggedIn) {
                    "已登录：${state.phoneMasked.orEmpty()}"
                } else {
                    "使用手机号验证码登录，继续获得智能购物建议。"
                },
                style = MaterialTheme.typography.bodyMedium,
                color = BuyWiseTheme.colors.muted,
            )

            if (state.isLoggedIn) {
                PrimaryLoginButton(
                    text = "进入 BuyWise",
                    enabled = !state.isLoading,
                    icon = { Icon(Icons.Outlined.VerifiedUser, contentDescription = null, modifier = Modifier.size(20.dp)) },
                    onClick = onContinue,
                )
            } else {
                OutlinedTextField(
                    value = state.phoneInput,
                    onValueChange = onPhoneChange,
                    label = { Text("手机号") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone),
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                    shape = RoundedCornerShape(16.dp),
                )
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(10.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    OutlinedTextField(
                        value = state.codeInput,
                        onValueChange = onCodeChange,
                        label = { Text("验证码") },
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                        modifier = Modifier.weight(1f),
                        singleLine = true,
                        shape = RoundedCornerShape(16.dp),
                    )
                    OutlinedButton(
                        onClick = onRequestOtp,
                        enabled = !state.isLoading,
                        modifier = Modifier.height(56.dp),
                        shape = RoundedCornerShape(16.dp),
                    ) {
                        Icon(Icons.Outlined.Sms, contentDescription = null, modifier = Modifier.size(18.dp))
                        Spacer(Modifier.width(6.dp))
                        Text("获取")
                    }
                }
                state.debugOtp?.let {
                    Text("测试验证码：$it", color = BuyWiseTheme.colors.primary, style = MaterialTheme.typography.bodyMedium)
                }
                PrimaryLoginButton(
                    text = "登录 / 注册",
                    enabled = !state.isLoading,
                    icon = {
                        Icon(
                            Icons.AutoMirrored.Outlined.Login,
                            contentDescription = null,
                            modifier = Modifier.size(20.dp),
                        )
                    },
                    onClick = onVerifyOtp,
                )
                OutlinedButton(
                    onClick = onGuestMode,
                    enabled = !state.isLoading && state.canUseGuestMode,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(52.dp),
                    shape = RoundedCornerShape(18.dp),
                ) {
                    Icon(Icons.Outlined.Person, contentDescription = null, modifier = Modifier.size(20.dp))
                    Spacer(Modifier.width(8.dp))
                    Text("游客体验")
                }
            }

            state.statusMessage?.let { Text(it, color = BuyWiseTheme.colors.primary, style = MaterialTheme.typography.bodyMedium) }
            state.errorMessage?.let { Text(it, color = BuyWiseTheme.colors.danger, style = MaterialTheme.typography.bodyMedium) }
        }
    }
}

@Composable
private fun PrimaryLoginButton(
    text: String,
    enabled: Boolean,
    icon: @Composable () -> Unit,
    onClick: () -> Unit,
) {
    Button(
        onClick = onClick,
        enabled = enabled,
        modifier = Modifier
            .fillMaxWidth()
            .height(56.dp),
        shape = RoundedCornerShape(18.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = BuyWiseTheme.colors.primary,
            contentColor = BuyWiseTheme.colors.panel,
            disabledContainerColor = BuyWiseTheme.colors.primarySoft,
            disabledContentColor = BuyWiseTheme.colors.muted,
        ),
        elevation = ButtonDefaults.buttonElevation(defaultElevation = 6.dp, pressedElevation = 2.dp),
    ) {
        icon()
        Spacer(Modifier.width(8.dp))
        Text(text, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
    }
}
