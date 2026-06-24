package com.buywise.android.data

data class GuideSessionSummary(
    val sessionId: String,
    val title: String?,
    val updatedAt: String?,
    val lastMessage: String?,
    val sessionToken: String? = null,
)

data class GuideSessionHistoryState(
    val items: List<GuideSessionSummary> = emptyList(),
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
)

data class GuideSessionDetail(
    val sessionId: String,
    val title: String?,
    val messages: List<GuideChatMessage>,
)

data class GuideSessionIdentity(
    val sessionId: String,
    val sessionToken: String? = null,
)
