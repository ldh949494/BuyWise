package com.buywise.android.viewmodel

internal fun Throwable.userMessage(prefix: String): String =
    message
        ?.takeIf { it.isNotBlank() }
        ?.let { "$prefix：${it.cleanBackendError()}" }
        ?: prefix

private fun String.cleanBackendError(): String {
    val normalized = lowercase()
    if (
        "failed to connect" in normalized ||
        "connection refused" in normalized ||
        "connect timed out" in normalized ||
        "timeout" in normalized ||
        "unable to resolve host" in normalized ||
        "no route to host" in normalized
    ) {
        return "暂时无法连接服务，请稍后重试"
    }
    if ("provider_circuit_open" in normalized) {
        return "外部识别服务暂时不可用，请稍后重试或改用文字输入"
    }
    if ("media_url_not_public" in normalized) {
        return "音频地址不能被识别服务访问，请检查上传公网地址"
    }
    if ("speech_provider_not_configured" in normalized) {
        return "语音识别服务未完成配置"
    }
    if ("provider_timeout" in normalized) {
        return "外部识别服务响应超时，请稍后重试"
    }
    if (startsWith("HTTP 500:")) {
        return "服务端暂时不可用，请稍后重试"
    }
    if (startsWith("HTTP 503:")) {
        return "服务端暂时不可用，请稍后重试"
    }
    if (contains("Traceback (most recent call last):")) {
        return "服务端返回异常，请稍后重试"
    }
    return lineSequence()
        .firstOrNull()
        ?.redactEndpointDetails()
        ?.take(140)
        .orEmpty()
        .ifBlank { "请求失败" }
}

private fun String.redactEndpointDetails(): String =
    replace(Regex("""/?(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?"""), "服务地址")
        .replace("10.0.2.2", "服务地址")
        .replace("127.0.0.1", "服务地址")
        .replace("localhost", "服务地址")
