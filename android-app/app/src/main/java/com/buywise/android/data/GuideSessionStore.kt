package com.buywise.android.data

import android.content.Context

class GuideSessionStore(context: Context) {
    private val preferences = context.getSharedPreferences("buywise-guide-sessions", Context.MODE_PRIVATE)

    fun remember(sessionId: String?, sessionToken: String?, title: String?) {
        if (sessionId.isNullOrBlank()) return
        val existing = load().filterNot { it.sessionId == sessionId }
        val next = listOf(GuideSessionSummary(sessionId, title, null, title, sessionToken)) + existing
        preferences.edit().putString("items", next.take(20).joinToString("\n") { encode(it) }).apply()
    }

    fun load(): List<GuideSessionSummary> =
        preferences.getString("items", null)
            ?.lines()
            ?.mapNotNull(::decode)
            ?: emptyList()

    private fun encode(summary: GuideSessionSummary): String =
        listOf(summary.sessionId, summary.sessionToken.orEmpty(), summary.title.orEmpty(), summary.lastMessage.orEmpty())
            .joinToString("\t") { it.replace("\t", " ").replace("\n", " ") }

    private fun decode(line: String): GuideSessionSummary? {
        val parts = line.split("\t")
        if (parts.isEmpty() || parts[0].isBlank()) return null
        return GuideSessionSummary(
            sessionId = parts[0],
            sessionToken = parts.getOrNull(1)?.takeIf { it.isNotBlank() },
            title = parts.getOrNull(2)?.takeIf { it.isNotBlank() },
            updatedAt = null,
            lastMessage = parts.getOrNull(3)?.takeIf { it.isNotBlank() },
        )
    }
}
