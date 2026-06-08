package com.buywise.android

import android.content.Context
import android.media.MediaRecorder
import java.io.File
import java.io.IOException

data class RecordedAudio(
    val filename: String,
    val contentType: String,
    val bytes: ByteArray,
)

class AudioRecorder(private val context: Context) {
    private var recorder: MediaRecorder? = null
    private var outputFile: File? = null

    val isRecording: Boolean
        get() = recorder != null

    @Throws(IOException::class)
    fun start() {
        if (isRecording) return

        val file = File(context.cacheDir, "buywise-recording-${System.currentTimeMillis()}.m4a")
        val nextRecorder = createRecorder()
        nextRecorder.setAudioSource(MediaRecorder.AudioSource.MIC)
        nextRecorder.setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
        nextRecorder.setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
        nextRecorder.setAudioSamplingRate(16_000)
        nextRecorder.setAudioEncodingBitRate(64_000)
        nextRecorder.setOutputFile(file.absolutePath)
        nextRecorder.prepare()
        nextRecorder.start()

        recorder = nextRecorder
        outputFile = file
    }

    @Throws(IOException::class)
    fun stop(): RecordedAudio? {
        val activeRecorder = recorder ?: return null
        val file = outputFile ?: return null
        recorder = null
        outputFile = null

        try {
            activeRecorder.stop()
        } catch (exc: RuntimeException) {
            file.delete()
            throw IOException("录音时间太短，请重新录制。", exc)
        } finally {
            activeRecorder.release()
        }

        return try {
            RecordedAudio(
                filename = file.name,
                contentType = "audio/mp4",
                bytes = file.readBytes(),
            )
        } finally {
            file.delete()
        }
    }

    fun cancel() {
        val activeRecorder = recorder
        val file = outputFile
        recorder = null
        outputFile = null
        runCatching { activeRecorder?.stop() }
        activeRecorder?.release()
        file?.delete()
    }

    @Suppress("DEPRECATION")
    private fun createRecorder(): MediaRecorder = MediaRecorder()
}
