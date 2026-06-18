package com.buywise.android.viewmodel

import com.buywise.android.data.Product
import com.buywise.android.data.VisionResult
import com.buywise.android.data.VisionState
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class UploadViewModelStateTest {
    @Test
    fun startImageRecognitionClearsPreviousResult() {
        val previous = VisionState(
            result = previousResult(),
            isLoading = false,
            errorMessage = "上一轮错误",
            recognizedQuery = "旧键盘",
            speechText = "旧语音",
            selectedImageName = "old.png",
        )

        val next = previous.startImageRecognition("camera-photo-123.png")

        assertEquals(VisionResult.Empty, next.result)
        assertTrue(next.isLoading)
        assertNull(next.errorMessage)
        assertNull(next.recognizedQuery)
        assertNull(next.speechText)
        assertEquals("camera-photo-123.png", next.selectedImageName)
    }

    @Test
    fun failRecognitionClearsPreviousResult() {
        val previous = VisionState(
            result = previousResult(),
            isLoading = true,
            errorMessage = null,
            recognizedQuery = "旧键盘",
            speechText = null,
            selectedImageName = "camera-photo-123.png",
        )

        val next = previous.failRecognition("图片识别失败")

        assertEquals(VisionResult.Empty, next.result)
        assertFalse(next.isLoading)
        assertEquals("图片识别失败", next.errorMessage)
        assertNull(next.recognizedQuery)
        assertNull(next.speechText)
        assertEquals("camera-photo-123.png", next.selectedImageName)
    }

    @Test
    fun startSpeechRecognitionClearsPreviousTranscript() {
        val previous = VisionState(
            result = previousResult(),
            isLoading = false,
            errorMessage = "上一轮错误",
            recognizedQuery = "旧语音",
            speechText = "旧语音",
            selectedImageName = "old.m4a",
        )

        val next = previous.startSpeechRecognition("voice-123.m4a")

        assertEquals(previous.result, next.result)
        assertTrue(next.isLoading)
        assertNull(next.errorMessage)
        assertNull(next.recognizedQuery)
        assertNull(next.speechText)
        assertEquals("voice-123.m4a", next.selectedImageName)
    }

    @Test
    fun failSpeechRecognitionClearsPreviousTranscript() {
        val previous = VisionState(
            result = previousResult(),
            isLoading = true,
            errorMessage = null,
            recognizedQuery = "旧语音",
            speechText = "旧语音",
            selectedImageName = "voice-123.m4a",
        )

        val next = previous.failSpeechRecognition("语音识别失败")

        assertEquals(previous.result, next.result)
        assertFalse(next.isLoading)
        assertEquals("语音识别失败", next.errorMessage)
        assertNull(next.recognizedQuery)
        assertNull(next.speechText)
        assertEquals("voice-123.m4a", next.selectedImageName)
    }

    private fun previousResult(): VisionResult =
        VisionResult(
            title = "旧键盘",
            confidence = 92,
            labels = listOf("旧标签"),
            similarProducts = listOf(
                Product(
                    id = "old-product",
                    name = "旧商品",
                    brand = null,
                    category = null,
                    price = null,
                    rating = null,
                    headline = "",
                    tags = emptyList(),
                    advantages = emptyList(),
                    cautions = emptyList(),
                ),
            ),
        )
}
