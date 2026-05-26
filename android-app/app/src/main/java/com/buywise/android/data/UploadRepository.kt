package com.buywise.android.data

import java.io.IOException

class UploadRepository internal constructor(
    private val apiClient: BuyWiseApiClient,
) {
    @Throws(IOException::class)
    fun runVisionDemo(): VisionResult {
        val upload = apiClient.uploadDemoFile(
            filename = "buywise-demo.png",
            contentType = mediaType("image/png"),
            bytes = DEMO_PNG_BYTES,
        )
        val response: VisionResponseDto = apiClient.post("/api/v1/vision/recognize", VisionRequestDto(upload.url))
        val category = response.category ?: "识别结果"
        val query = response.query ?: listOf(response.features.joinToString(" "), category).joinToString(" ").trim()
        return VisionResult(
            title = query.ifBlank { category },
            confidence = 100,
            labels = listOfNotBlank(category) + response.features,
            similarProducts = emptyList(),
        )
    }

    @Throws(IOException::class)
    fun runSpeechDemo(): String {
        val upload = apiClient.uploadDemoFile(
            filename = "buywise-demo.wav",
            contentType = mediaType("audio/wav"),
            bytes = DEMO_WAV_BYTES,
        )
        val response: SpeechResponseDto = apiClient.post("/api/v1/speech/asr", SpeechRequestDto(upload.url))
        return response.text
    }

    private fun listOfNotBlank(value: String?): List<String> =
        if (value.isNullOrBlank()) emptyList() else listOf(value)
}
