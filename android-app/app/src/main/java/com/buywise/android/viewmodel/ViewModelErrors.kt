package com.buywise.android.viewmodel

internal fun Throwable.userMessage(prefix: String): String =
    message?.takeIf { it.isNotBlank() }?.let { "$prefix：$it" } ?: prefix
