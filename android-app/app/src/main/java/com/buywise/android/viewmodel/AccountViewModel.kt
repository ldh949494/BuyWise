package com.buywise.android.viewmodel

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import com.buywise.android.data.AccountState
import com.buywise.android.data.AuthRepository
import com.buywise.android.data.BudgetRange
import com.buywise.android.data.GuidePreferences
import com.buywise.android.data.GuidePreferencesRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class AccountViewModel(
    private val repository: AuthRepository?,
    private val preferencesRepository: GuidePreferencesRepository?,
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
            loadGuidePreferences()
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
                    loadGuidePreferences()
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

    fun loadGuidePreferences() {
        val repo = preferencesRepository ?: return
        if (!state.isLoggedIn) {
            return
        }
        state = state.copy(preferencesLoading = true, preferencesError = null)
        scope.launch {
            runCatching { withContext(Dispatchers.IO) { repo.load() } }
                .onSuccess { preferences -> state = state.copy(guidePreferences = preferences, preferencesLoading = false) }
                .onFailure { state = state.copy(preferencesLoading = false, preferencesError = it.userMessage("导购偏好加载失败")) }
        }
    }

    fun updateBudgetPolicy(value: String) {
        savePreferences(state.guidePreferences.copy(budgetPolicy = value))
    }

    fun updatePresentationStyle(value: String) {
        savePreferences(state.guidePreferences.copy(presentationStyle = value))
    }

    fun togglePriorityTag(tag: String) {
        val current = state.guidePreferences.priorityTags
        val next = if (tag in current) current - tag else current + tag
        savePreferences(state.guidePreferences.copy(priorityTags = next))
    }

    fun toggleExcludedTag(tag: String) {
        val current = state.guidePreferences.excludedTags
        val next = if (tag in current) current - tag else current + tag
        savePreferences(state.guidePreferences.copy(excludedTags = next))
    }

    fun toggleOwnedCategory(category: String) {
        val current = state.guidePreferences.ownedCategories
        val next = if (category in current) current - category else current + category
        savePreferences(state.guidePreferences.copy(ownedCategories = next))
    }

    fun updateBundleBudgetMax(value: String) {
        val max = value.toDoubleOrNull()
        val budget = state.guidePreferences.bundleBudgetRange ?: BudgetRange()
        savePreferences(state.guidePreferences.copy(bundleBudgetRange = budget.copy(max = max)))
    }

    fun clearGuidePreferences() {
        val repo = preferencesRepository ?: return
        if (!state.isLoggedIn) {
            state = state.copy(guidePreferences = GuidePreferences())
            return
        }
        state = state.copy(preferencesLoading = true, preferencesError = null)
        scope.launch {
            runCatching { withContext(Dispatchers.IO) { repo.clear() } }
                .onSuccess {
                    state = state.copy(
                        guidePreferences = GuidePreferences(),
                        preferencesLoading = false,
                        statusMessage = "导购偏好已清除",
                    )
                }
                .onFailure { state = state.copy(preferencesLoading = false, preferencesError = it.userMessage("导购偏好清除失败")) }
        }
    }

    private fun savePreferences(preferences: GuidePreferences) {
        val repo = preferencesRepository ?: return
        if (!state.isLoggedIn) {
            state = state.copy(guidePreferences = preferences)
            return
        }
        state = state.copy(guidePreferences = preferences, preferencesLoading = true, preferencesError = null)
        scope.launch {
            runCatching { withContext(Dispatchers.IO) { repo.save(preferences) } }
                .onSuccess { saved -> state = state.copy(guidePreferences = saved, preferencesLoading = false, statusMessage = "导购偏好已保存") }
                .onFailure { state = state.copy(preferencesLoading = false, preferencesError = it.userMessage("导购偏好保存失败")) }
        }
    }
}
