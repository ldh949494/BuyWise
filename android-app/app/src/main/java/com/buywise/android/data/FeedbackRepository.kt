package com.buywise.android.data

import java.io.IOException

class FeedbackRepository internal constructor(
    private val apiClient: BuyWiseApiClient,
) {
    val capability: BetaCapability
        get() = apiClient.betaCapability

    @Throws(IOException::class)
    fun fetchFeedbackPrompts(): List<FeedbackPrompt> {
        val response: FeedbackPromptListResponseDto = apiClient.get("/api/v1/feedback/prompts", requireAuth = true)
        return response.items.map { it.toPrompt() }
    }

    @Throws(IOException::class)
    fun submitFeedback(prompt: FeedbackPrompt, draft: FeedbackDraft) {
        apiClient.postUnit(
            "/api/v1/reviews/from-order-item",
            FeedbackSubmitRequestDto(
                orderItemId = prompt.orderItemId.toInt(),
                rating = draft.rating,
                content = draft.content.ifBlank { "收货后体验符合预期。" },
                prosTags = draft.prosTags,
                consTags = draft.consTags,
                metExpectation = draft.metExpectation,
            ),
            requireAuth = true,
        )
    }
}
