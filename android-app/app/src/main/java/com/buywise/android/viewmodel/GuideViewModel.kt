package com.buywise.android.viewmodel

import android.os.Handler
import android.os.Looper
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import com.buywise.android.data.ChatStreamEvent
import com.buywise.android.data.GuideRepository
import com.buywise.android.data.GuideState
import com.buywise.android.data.ShopRepository
import okhttp3.sse.EventSource

class GuideViewModel(
    private val repository: GuideRepository,
    initialState: GuideState,
) : ViewModel() {
    private val mainHandler = Handler(Looper.getMainLooper())
    private var guideStream: EventSource? = null

    var state by mutableStateOf(initialState)
        private set

    fun updateQuery(query: String) {
        state = state.copy(query = query)
    }

    fun submitQuery() {
        val query = state.query.ifBlank { "300 元以内，适合宿舍写代码的低噪音机械键盘" }
        guideStream?.cancel()
        state = state.copy(
            query = query,
            intentSummary = "正在理解预算、场景和偏好...",
            recommendations = emptyList(),
            partialReply = "",
            isStreaming = true,
            errorMessage = null,
        )
        guideStream = repository.streamGuide(
            query = query,
            sessionId = state.sessionId,
            onEvent = { event -> mainHandler.post { applyChatEvent(event) } },
        )
    }

    fun useQuery(query: String) {
        updateQuery(query)
    }

    fun clearStream() {
        guideStream?.cancel()
    }

    fun clear() {
        onCleared()
    }

    override fun onCleared() {
        clearStream()
        super.onCleared()
    }

    private fun applyChatEvent(event: ChatStreamEvent) {
        state = when (event) {
            is ChatStreamEvent.Meta -> state.copy(sessionId = event.sessionId)
            is ChatStreamEvent.Status -> state.copy(intentSummary = event.message)
            is ChatStreamEvent.Token -> state.copy(partialReply = state.partialReply + event.text)
            is ChatStreamEvent.Products -> state.copy(intentSummary = event.intentSummary, recommendations = event.recommendations)
            is ChatStreamEvent.Done -> state.copy(partialReply = event.reply.ifBlank { state.partialReply }, isStreaming = false)
            is ChatStreamEvent.Error -> state.copy(errorMessage = event.message, isStreaming = false)
        }
    }

    companion object {
        fun from(shopRepository: ShopRepository): GuideViewModel =
            GuideViewModel(shopRepository.guideRepository, shopRepository.guideState(""))
    }
}
