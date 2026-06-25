package com.buywise.android.data

import org.junit.Assert.assertEquals
import org.junit.Test

class GuideSessionMergeTest {
    @Test
    fun remoteSessionKeepsLocalAnonymousToken() {
        val merged = mergeGuideSessionSummaries(
            remoteSessions = listOf(
                GuideSessionSummary(
                    sessionId = "session-1",
                    title = "远端标题",
                    updatedAt = "2026-06-25T10:00:00",
                    lastMessage = "远端最后消息",
                ),
            ),
            localSessions = listOf(
                GuideSessionSummary(
                    sessionId = "session-1",
                    title = "本地标题",
                    updatedAt = null,
                    lastMessage = "本地最后消息",
                    sessionToken = "token-1",
                ),
            ),
        )

        assertEquals(1, merged.size)
        assertEquals("session-1", merged[0].sessionId)
        assertEquals("token-1", merged[0].sessionToken)
        assertEquals("远端标题", merged[0].title)
        assertEquals("远端最后消息", merged[0].lastMessage)
    }

    @Test
    fun localOnlySessionsRemainAvailable() {
        val merged = mergeGuideSessionSummaries(
            remoteSessions = listOf(
                GuideSessionSummary(
                    sessionId = "remote-session",
                    title = "远端会话",
                    updatedAt = "2026-06-25T10:00:00",
                    lastMessage = "远端消息",
                ),
            ),
            localSessions = listOf(
                GuideSessionSummary(
                    sessionId = "local-session",
                    title = "本地会话",
                    updatedAt = null,
                    lastMessage = "本地消息",
                    sessionToken = "local-token",
                ),
            ),
        )

        assertEquals(listOf("remote-session", "local-session"), merged.map { it.sessionId })
        assertEquals("local-token", merged[1].sessionToken)
    }
}
