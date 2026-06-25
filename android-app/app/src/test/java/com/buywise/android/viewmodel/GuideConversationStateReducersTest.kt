package com.buywise.android.viewmodel

import com.buywise.android.data.GuideChatMessage
import com.buywise.android.data.GuideChatRole
import com.buywise.android.data.GuideSessionDetail
import com.buywise.android.data.GuideState
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Test

class GuideConversationStateReducersTest {
    @Test
    fun restoreGuideSessionKeepsTokenAndMessages() {
        val detail = GuideSessionDetail(
            sessionId = "history-session",
            title = "历史会话",
            messages = listOf(
                GuideChatMessage(
                    id = "history-1",
                    role = GuideChatRole.USER,
                    text = "推荐一个键盘",
                ),
                GuideChatMessage(
                    id = "history-2",
                    role = GuideChatRole.ASSISTANT,
                    text = "推荐：History K87",
                ),
            ),
        )

        val restored = GuideState(
            query = "",
            intentSummary = "",
            recommendations = emptyList(),
            isStreaming = true,
        ).restoreGuideSessionState(detail, token = "history-token")

        assertEquals("history-session", restored.sessionId)
        assertEquals("history-token", restored.sessionToken)
        assertEquals("推荐一个键盘", restored.query)
        assertEquals(detail.messages, restored.chatMessages)
        assertEquals("推荐：History K87", restored.partialReply)
        assertFalse(restored.isStreaming)
    }
}
