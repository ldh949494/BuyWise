package com.buywise.android.viewmodel

import android.os.Handler
import android.os.Looper
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import com.buywise.android.data.ChatStreamEvent
import com.buywise.android.data.CompareState
import com.buywise.android.data.GuideState
import com.buywise.android.data.HomeState
import com.buywise.android.data.Product
import com.buywise.android.data.ShopRepository
import com.buywise.android.data.VisionState
import okhttp3.sse.EventSource

class BuyWiseViewModel(
    private val repository: ShopRepository = ShopRepository(),
) : ViewModel() {
    private val mainHandler = Handler(Looper.getMainLooper())
    private var guideStream: EventSource? = null

    val homeState: HomeState = repository.homeState()
    val compareState: CompareState = repository.compareState()
    val visionState: VisionState = repository.visionState()

    var guideState by mutableStateOf(repository.guideState(""))
        private set

    fun updateGuideQuery(query: String) {
        guideState = guideState.copy(query = query)
    }

    fun submitGuideQuery() {
        val query = guideState.query.ifBlank { "300 元以内，适合宿舍使用的低噪音机械键盘" }
        guideStream?.cancel()
        guideState = guideState.copy(
            query = query,
            intentSummary = "Connecting to BuyWise...",
            recommendations = emptyList(),
            partialReply = "",
            isStreaming = true,
            errorMessage = null,
        )
        guideStream = repository.streamGuide(
            query = query,
            sessionId = guideState.sessionId,
            onEvent = { event ->
                mainHandler.post { applyChatEvent(event) }
            },
        )
    }

    fun product(productId: String?): Product? =
        guideState.recommendations.firstOrNull { it.product.id == productId }?.product
            ?: repository.product(productId)

    override fun onCleared() {
        guideStream?.cancel()
        super.onCleared()
    }

    private fun applyChatEvent(event: ChatStreamEvent) {
        guideState = when (event) {
            is ChatStreamEvent.Meta -> guideState.copy(sessionId = event.sessionId)
            is ChatStreamEvent.Status -> guideState.copy(intentSummary = event.message)
            is ChatStreamEvent.Token -> guideState.copy(partialReply = guideState.partialReply + event.text)
            is ChatStreamEvent.Products -> guideState.copy(
                intentSummary = event.intentSummary,
                recommendations = event.recommendations,
            )
            is ChatStreamEvent.Done -> guideState.copy(
                partialReply = event.reply.ifBlank { guideState.partialReply },
                isStreaming = false,
            )
            is ChatStreamEvent.Error -> guideState.copy(
                errorMessage = event.message,
                isStreaming = false,
            )
        }
    }
}
