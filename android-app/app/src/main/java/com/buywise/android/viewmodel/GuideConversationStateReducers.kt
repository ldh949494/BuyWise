package com.buywise.android.viewmodel

import com.buywise.android.data.GuideChatRole
import com.buywise.android.data.GuideResultStatus
import com.buywise.android.data.GuideSessionDetail
import com.buywise.android.data.GuideState

internal fun GuideState.newGuideConversationState(): GuideState =
    copy(
        query = "",
        intentSummary = "",
        recommendations = emptyList(),
        bundlePlans = emptyList(),
        resultStatus = GuideResultStatus.Idle,
        clarificationMessage = null,
        fallbackMessage = null,
        hasProvisionalResults = false,
        pendingRefreshMessage = null,
        partialReply = "",
        chatDraft = "",
        chatMessages = emptyList(),
        isStreaming = false,
        errorMessage = null,
        sessionId = null,
        sessionToken = null,
        compareChatContext = null,
    )

internal fun GuideState.restoreGuideSessionState(detail: GuideSessionDetail, token: String?): GuideState =
    copy(
        sessionId = detail.sessionId,
        sessionToken = token,
        query = detail.messages.lastOrNull { it.role == GuideChatRole.USER }?.text.orEmpty(),
        chatMessages = detail.messages,
        recommendations = detail.messages.lastOrNull { it.recommendations.isNotEmpty() }?.recommendations.orEmpty(),
        bundlePlans = detail.messages.lastOrNull { it.bundlePlans.isNotEmpty() }?.bundlePlans.orEmpty(),
        partialReply = detail.messages.lastOrNull { it.role == GuideChatRole.ASSISTANT }?.text.orEmpty(),
        isStreaming = false,
        errorMessage = null,
        sessionHistory = sessionHistory.copy(isLoading = false),
    )
