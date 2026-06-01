package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.Login
import androidx.compose.material.icons.automirrored.outlined.Logout
import androidx.compose.material.icons.outlined.Person
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.ui.unit.dp
import com.buywise.android.data.AccountState

@Composable
fun AccountScreen(
    state: AccountState,
    onPhoneChange: (String) -> Unit,
    onCodeChange: (String) -> Unit,
    onRequestOtp: () -> Unit,
    onVerifyOtp: () -> Unit,
    onGuestMode: () -> Unit,
    onLogout: () -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        Text("我的账号", style = MaterialTheme.typography.headlineSmall)
        if (state.isLoggedIn) {
            Text("已登录：${state.phoneMasked.orEmpty()}", style = MaterialTheme.typography.bodyLarge)
            Button(onClick = onLogout, enabled = !state.isLoading, modifier = Modifier.fillMaxWidth()) {
                Icon(Icons.AutoMirrored.Outlined.Logout, contentDescription = null)
                Spacer(Modifier.height(1.dp))
                Text("退出登录")
            }
        } else {
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
            state.debugOtp?.let { Text("测试验证码：$it", color = MaterialTheme.colorScheme.primary) }
            OutlinedButton(onClick = onRequestOtp, enabled = !state.isLoading, modifier = Modifier.fillMaxWidth()) {
                Text("获取验证码")
            }
            Button(onClick = onVerifyOtp, enabled = !state.isLoading, modifier = Modifier.fillMaxWidth()) {
                Icon(Icons.AutoMirrored.Outlined.Login, contentDescription = null)
                Text("登录 / 注册")
            }
            OutlinedButton(
                onClick = onGuestMode,
                enabled = !state.isLoading && state.canUseGuestMode,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Icon(Icons.Outlined.Person, contentDescription = null)
                Text("游客体验")
            }
        }
        state.statusMessage?.let { Text(it, color = MaterialTheme.colorScheme.primary) }
        state.errorMessage?.let { Text(it, color = MaterialTheme.colorScheme.error) }
    }
}
