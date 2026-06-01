package com.buywise.android.viewmodel

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import com.buywise.android.data.AccountState
import com.buywise.android.data.AuthRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class AccountViewModel(
    private val repository: AuthRepository?,
    private val scope: CoroutineScope,
) {
    var state by mutableStateOf(repository?.currentState() ?: AccountState())
        private set

    fun restoreSession() {
        val repo = repository ?: return
        state = state.copy(isLoading = true, errorMessage = null)
        scope.launch {
            state = runCatching { withContext(Dispatchers.IO) { repo.restoreSession() } }
                .getOrElse { repo.currentState() }
                .copy(isLoading = false)
        }
    }

    fun updatePhone(value: String) {
        state = state.copy(phoneInput = value, errorMessage = null, statusMessage = null)
    }

    fun updateCode(value: String) {
        state = state.copy(codeInput = value, errorMessage = null, statusMessage = null)
    }

    fun requestOtp() {
        val repo = repository ?: return
        state = state.copy(isLoading = true, errorMessage = null, statusMessage = null)
        scope.launch {
            runCatching { withContext(Dispatchers.IO) { repo.requestOtp(state.phoneInput) } }
                .onSuccess { debugOtp ->
                    state = state.copy(
                        isLoading = false,
                        debugOtp = debugOtp,
                        statusMessage = "验证码已发送",
                    )
                }
                .onFailure { state = state.copy(isLoading = false, errorMessage = it.userMessage("验证码发送失败")) }
        }
    }

    fun verifyOtp(onLoggedIn: () -> Unit) {
        val repo = repository ?: return
        state = state.copy(isLoading = true, errorMessage = null, statusMessage = null)
        scope.launch {
            runCatching { withContext(Dispatchers.IO) { repo.verifyOtp(state.phoneInput, state.codeInput) } }
                .onSuccess {
                    state = it.copy(isLoading = false)
                    onLoggedIn()
                }
                .onFailure { state = state.copy(isLoading = false, errorMessage = it.userMessage("登录失败")) }
        }
    }

    fun enterGuestMode(onEntered: () -> Unit) {
        val repo = repository ?: return
        state = repo.enterGuestMode()
        onEntered()
    }

    fun logout() {
        val repo = repository ?: return
        state = state.copy(isLoading = true, errorMessage = null, statusMessage = null)
        scope.launch {
            state = runCatching { withContext(Dispatchers.IO) { repo.logout() } }
                .getOrElse { repo.currentState().copy(errorMessage = it.userMessage("退出登录失败")) }
                .copy(isLoading = false)
        }
    }
}
