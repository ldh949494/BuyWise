package com.buywise.android

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.material3.SnackbarHostState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class AudioInputController internal constructor(
    private val isRecording: Boolean,
    private val activeTarget: MultimodalTarget,
    private val handleInput: (MultimodalTarget) -> Unit,
) {
    fun isRecording(target: MultimodalTarget): Boolean =
        isRecording && activeTarget == target

    fun handle(target: MultimodalTarget) {
        handleInput(target)
    }
}

@Composable
fun rememberAudioInputController(
    isBusy: Boolean,
    snackbarHostState: SnackbarHostState,
    onRecordedAudio: (RecordedAudio, MultimodalTarget) -> Unit,
): AudioInputController {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val audioRecorder = remember(context) { AudioRecorder(context.applicationContext) }
    var pendingTarget by remember { mutableStateOf(MultimodalTarget.GuideChat) }
    var activeTarget by remember { mutableStateOf(MultimodalTarget.GuideChat) }
    var isRecording by remember { mutableStateOf(false) }

    fun startRecording(target: MultimodalTarget) {
        if (isBusy) {
            scope.launch { snackbarHostState.showSnackbar("正在处理上一段输入") }
            return
        }
        activeTarget = target
        scope.launch {
            runCatching {
                withContext(Dispatchers.IO) { audioRecorder.start() }
            }.onSuccess {
                isRecording = true
                snackbarHostState.showSnackbar("开始录音，再点麦克风结束")
            }.onFailure { throwable ->
                isRecording = false
                snackbarHostState.showSnackbar(throwable.message ?: "录音启动失败")
            }
        }
    }

    fun stopRecording() {
        val target = activeTarget
        scope.launch {
            runCatching {
                withContext(Dispatchers.IO) { audioRecorder.stop() }
            }.onSuccess { audio ->
                isRecording = false
                if (audio == null) {
                    snackbarHostState.showSnackbar("没有可上传的录音")
                } else {
                    onRecordedAudio(audio, target)
                }
            }.onFailure { throwable ->
                isRecording = false
                snackbarHostState.showSnackbar(throwable.message ?: "录音失败")
            }
        }
    }

    val permissionLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (granted) {
            startRecording(pendingTarget)
        } else {
            scope.launch { snackbarHostState.showSnackbar("需要麦克风权限才能语音输入") }
        }
    }

    DisposableEffect(audioRecorder) {
        onDispose { audioRecorder.cancel() }
    }

    return AudioInputController(
        isRecording = isRecording,
        activeTarget = activeTarget,
        handleInput = { target ->
            if (isRecording) {
                stopRecording()
                return@AudioInputController
            }
            pendingTarget = target
            if (context.checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
                startRecording(target)
            } else {
                permissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
            }
        },
    )
}
