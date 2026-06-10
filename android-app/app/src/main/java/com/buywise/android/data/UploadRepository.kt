package com.buywise.android.data

import java.io.IOException
import okhttp3.MediaType

interface UploadRecognitionRepository {
    fun runVisionDemo(): VisionResult
    fun recognizeImage(filename: String, contentType: MediaType, bytes: ByteArray): VisionResult
    fun runSpeechDemo(): String
    fun transcribeAudio(filename: String, contentType: MediaType, bytes: ByteArray): String
}

class UploadRepository internal constructor(
    private val apiClient: BuyWiseApiClient,
) : UploadRecognitionRepository {
    @Throws(IOException::class)
    override fun runVisionDemo(): VisionResult {
        return recognizeImage(
            filename = "buywise-demo.png",
            contentType = mediaType("image/png"),
            bytes = DEMO_PNG_BYTES,
        )
    }

    @Throws(IOException::class)
    override fun recognizeImage(filename: String, contentType: MediaType, bytes: ByteArray): VisionResult {
        val upload = apiClient.uploadFile(
            filename = filename,
            contentType = contentType,
            bytes = bytes,
        )
        val response: VisualSearchResponseDto = apiClient.post(
            "/api/v1/visual-search",
            VisualSearchRequestDto(
                imageUrl = upload.url,
                message = "我想要同款或相似商品",
            ),
        )
        val recognized = response.recognized
        val category = recognized.category ?: recognized.detectedObjects.firstOrNull() ?: "识别结果"
        val labelQuery = recognizedLabels(recognized).joinToString(" ").trim()
        val query = recognized.query
            ?.takeIf { it.isNotBlank() }
            ?: labelQuery.takeIf { it.isNotBlank() }
            ?: category
        val products = response.products.map {
            it.toProduct(category = category, fallbackReason = "与图片特征相似")
        }
        return VisionResult(
            title = query.ifBlank { category },
            confidence = recognized.confidence.toPercent(),
            labels = recognizedLabels(recognized),
            similarProducts = products,
            fallbackUsed = response.fallbackUsed,
        )
    }

    @Throws(IOException::class)
    override fun runSpeechDemo(): String {
        return transcribeAudio(
            filename = "buywise-demo.wav",
            contentType = mediaType("audio/wav"),
            bytes = DEMO_WAV_BYTES,
        )
    }

    @Throws(IOException::class)
    override fun transcribeAudio(filename: String, contentType: MediaType, bytes: ByteArray): String {
        val upload = apiClient.uploadFile(
            filename = filename,
            contentType = contentType,
            bytes = bytes,
        )
        val response: SpeechResponseDto = apiClient.post("/api/v1/speech/asr", SpeechRequestDto(upload.url))
        return response.text.takeIf { it.isNotBlank() }
            ?: throw IOException("没有识别到文本，请换个更清晰的录音再试")
    }

    private fun recognizedLabels(response: VisionResponseDto): List<String> =
        (
            listOfNotBlank(response.category, response.style, response.shape) +
                response.features +
                response.detectedObjects +
                response.colors +
                response.materials +
                response.brandCues
        ).distinct()

    private fun listOfNotBlank(vararg values: String?): List<String> =
        values.mapNotNull { it?.takeIf(String::isNotBlank) }

    private fun Double?.toPercent(): Int {
        if (this == null) {
            return 100
        }
        return if (this <= 1.0) {
            (this * 100).toInt()
        } else {
            toInt()
        }.coerceIn(0, 100)
    }
}
