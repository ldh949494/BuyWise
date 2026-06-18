package com.buywise.android.viewmodel

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.buywise.android.data.ShopRepository
import com.buywise.android.data.UploadRecognitionRepository
import com.buywise.android.data.VisionResult
import com.buywise.android.data.VisionState
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class UploadViewModel(
    private val repository: UploadRecognitionRepository,
    initialState: VisionState,
) : ViewModel() {
    var state by mutableStateOf(initialState)
        private set

    fun runVisionDemo(
        onRecognized: ((VisionResult) -> Unit)? = null,
        onError: ((String) -> Unit)? = null,
    ) {
        state = state.startImageRecognition("buywise-demo.png")
        viewModelScope.launch {
            runCatching {
                withContext(Dispatchers.IO) { repository.runVisionDemo() }
            }.onSuccess { result ->
                state = state.copy(result = result, recognizedQuery = result.title, isLoading = false)
                onRecognized?.invoke(result)
            }.onFailure { throwable ->
                val message = throwable.userMessage("图片识别失败")
                state = state.failRecognition(message)
                onError?.invoke(message)
            }
        }
    }

    fun recognizeImage(
        filename: String,
        contentType: String,
        bytes: ByteArray,
        onRecognized: ((VisionResult) -> Unit)? = null,
        onError: ((String) -> Unit)? = null,
    ) {
        state = state.startImageRecognition(filename)
        viewModelScope.launch {
            runCatching {
                withContext(Dispatchers.IO) {
                    repository.recognizeImage(filename, com.buywise.android.data.mediaType(contentType), bytes)
                }
            }.onSuccess { result ->
                state = state.copy(result = result, recognizedQuery = result.title, isLoading = false)
                onRecognized?.invoke(result)
            }.onFailure { throwable ->
                val message = throwable.userMessage("图片识别失败")
                state = state.failRecognition(message)
                onError?.invoke(message)
            }
        }
    }

    fun runSpeechDemo(
        onRecognized: ((String) -> Unit)? = null,
        onError: ((String) -> Unit)? = null,
    ) {
        state = state.startSpeechRecognition()
        viewModelScope.launch {
            runCatching {
                withContext(Dispatchers.IO) { repository.runSpeechDemo() }
            }.onSuccess { text ->
                state = state.copy(speechText = text, recognizedQuery = text, isLoading = false)
                onRecognized?.invoke(text)
            }.onFailure { throwable ->
                val message = throwable.userMessage("语音识别失败")
                state = state.failSpeechRecognition(message)
                onError?.invoke(message)
            }
        }
    }

    fun transcribeAudio(
        filename: String,
        contentType: String,
        bytes: ByteArray,
        onRecognized: ((String) -> Unit)? = null,
        onError: ((String) -> Unit)? = null,
    ) {
        state = state.startSpeechRecognition(filename)
        viewModelScope.launch {
            runCatching {
                withContext(Dispatchers.IO) {
                    repository.transcribeAudio(filename, com.buywise.android.data.mediaType(contentType), bytes)
                }
            }.onSuccess { text ->
                state = state.copy(speechText = text, recognizedQuery = text, isLoading = false)
                onRecognized?.invoke(text)
            }.onFailure { throwable ->
                val message = throwable.userMessage("语音识别失败")
                state = state.failSpeechRecognition(message)
                onError?.invoke(message)
            }
        }
    }

    fun product(productId: String?): com.buywise.android.data.Product? =
        state.result.similarProducts.firstOrNull { it.id == productId }

    fun clear() {
        onCleared()
    }

    companion object {
        fun from(shopRepository: ShopRepository): UploadViewModel =
            UploadViewModel(shopRepository.uploadRepository, shopRepository.visionState())
    }
}

fun VisionState.startImageRecognition(filename: String): VisionState =
    copy(
        result = VisionResult.Empty,
        isLoading = true,
        errorMessage = null,
        recognizedQuery = null,
        speechText = null,
        selectedImageName = filename,
    )

fun VisionState.failRecognition(message: String): VisionState =
    copy(
        result = VisionResult.Empty,
        isLoading = false,
        errorMessage = message,
        recognizedQuery = null,
        speechText = null,
    )

fun VisionState.startSpeechRecognition(filename: String? = selectedImageName): VisionState =
    copy(
        isLoading = true,
        errorMessage = null,
        recognizedQuery = null,
        speechText = null,
        selectedImageName = filename,
    )

fun VisionState.failSpeechRecognition(message: String): VisionState =
    copy(
        isLoading = false,
        errorMessage = message,
        recognizedQuery = null,
        speechText = null,
    )
