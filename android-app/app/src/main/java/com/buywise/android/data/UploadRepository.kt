package com.buywise.android.data

import java.io.IOException

class UploadRepository internal constructor(
    private val apiClient: BuyWiseApiClient,
) {
    @Throws(IOException::class)
    fun runVisionDemo(): VisionResult {
        return recognizeImage(
            filename = "buywise-demo.png",
            contentType = mediaType("image/png"),
            bytes = DEMO_PNG_BYTES,
        )
    }

    @Throws(IOException::class)
    fun recognizeImage(filename: String, contentType: okhttp3.MediaType, bytes: ByteArray): VisionResult {
        val upload = apiClient.uploadFile(
            filename = filename,
            contentType = contentType,
            bytes = bytes,
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
        return transcribeAudio(
            filename = "buywise-demo.wav",
            contentType = mediaType("audio/wav"),
            bytes = DEMO_WAV_BYTES,
        )
    }

    @Throws(IOException::class)
    fun transcribeAudio(filename: String, contentType: okhttp3.MediaType, bytes: ByteArray): String {
        val upload = apiClient.uploadFile(
            filename = filename,
            contentType = contentType,
            bytes = bytes,
        )
        val response: SpeechResponseDto = apiClient.post("/api/v1/speech/asr", SpeechRequestDto(upload.url))
        return response.text.takeIf { it.isNotBlank() }
            ?: throw IOException("没有识别到文本，请换个更清晰的录音再试")
    }

    private fun listOfNotBlank(value: String?): List<String> =
        if (value.isNullOrBlank()) emptyList() else listOf(value)
}
