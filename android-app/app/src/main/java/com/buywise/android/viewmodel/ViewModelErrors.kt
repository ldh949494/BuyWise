package com.buywise.android.viewmodel

internal fun Throwable.userMessage(prefix: String): String =
    message
        ?.takeIf { it.isNotBlank() }
        ?.let { "$prefix：${it.cleanBackendError()}" }
        ?: prefix

private fun String.cleanBackendError(): String {
    if (startsWith("HTTP 500:")) {
        return "服务端暂时不可用，请稍后重试"
    }
    if (contains("Traceback (most recent call last):")) {
        return "服务端返回异常，请稍后重试"
    }
    return lineSequence().firstOrNull()?.take(140).orEmpty().ifBlank { "请求失败" }
}
