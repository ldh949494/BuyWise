package com.buywise.android.viewmodel

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.buywise.android.data.BetaCapability
import com.buywise.android.data.FeedbackDraft
import com.buywise.android.data.FeedbackPrompt
import com.buywise.android.data.FeedbackRepository
import com.buywise.android.data.FeedbackUiState
import com.buywise.android.data.ShopRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class FeedbackViewModel(
    private val repository: FeedbackRepository,
    private val capability: BetaCapability,
) : ViewModel() {
    var state by mutableStateOf(FeedbackUiState(
        canUseFeedback = capability.canUseUserFeatures,
        tokenRequiredMessage = capability.message,
    ))
        private set

    fun refreshPrompts(onLoaded: (List<FeedbackPrompt>) -> Unit) {
        if (!capability.canUseUserFeatures) {
            onLoaded(emptyList())
            return
        }
        viewModelScope.launch {
            runCatching {
                withContext(Dispatchers.IO) { repository.fetchFeedbackPrompts() }
            }.onSuccess(onLoaded)
        }
    }

    fun toggleForm(prompt: FeedbackPrompt) {
        state = state.copy(
            activePromptId = if (state.activePromptId == prompt.orderItemId) null else prompt.orderItemId,
            submitErrors = state.submitErrors - prompt.orderItemId,
            successMessage = null,
        )
    }

    fun updateDraft(prompt: FeedbackPrompt, draft: FeedbackDraft) {
        state = state.copy(drafts = state.drafts + (prompt.orderItemId to draft))
    }

    fun submitFeedback(prompt: FeedbackPrompt, onSubmitted: () -> Unit) {
        if (!capability.canUseUserFeatures) {
            state = state.copy(submitErrors = state.submitErrors + (prompt.orderItemId to (capability.message ?: "")))
            return
        }
        val draft = state.draftFor(prompt)
        state = state.copy(
            submittingIds = state.submittingIds + prompt.orderItemId,
            submitErrors = state.submitErrors - prompt.orderItemId,
            successMessage = null,
        )
        viewModelScope.launch {
            runCatching {
                withContext(Dispatchers.IO) { repository.submitFeedback(prompt, draft) }
            }.onSuccess {
                state = state.copy(
                    activePromptId = null,
                    drafts = state.drafts - prompt.orderItemId,
                    submittingIds = state.submittingIds - prompt.orderItemId,
                    submitErrors = state.submitErrors - prompt.orderItemId,
                    successMessage = "反馈已提交",
                )
                onSubmitted()
            }.onFailure { throwable ->
                state = state.copy(
                    submittingIds = state.submittingIds - prompt.orderItemId,
                    submitErrors = state.submitErrors + (prompt.orderItemId to throwable.userMessage("评价提交失败")),
                )
            }
        }
    }

    fun clear() {
        onCleared()
    }

    companion object {
        fun from(shopRepository: ShopRepository): FeedbackViewModel =
            FeedbackViewModel(shopRepository.feedbackRepository, shopRepository.betaCapability)
    }
}
