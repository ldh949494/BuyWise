package com.buywise.android

import android.content.Context
import android.graphics.Bitmap
import android.net.Uri
import android.provider.OpenableColumns
import java.io.ByteArrayOutputStream

enum class MultimodalTarget {
    VisionTab,
    GuideChat,
}

data class SelectedImage(
    val filename: String,
    val contentType: String,
    val bytes: ByteArray,
)

fun Context.readSelectedImage(uri: Uri): SelectedImage? {
    val contentType = contentResolver.getType(uri) ?: "image/jpeg"
    val filename = contentResolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)?.use { cursor ->
        val index = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
        if (index >= 0 && cursor.moveToFirst()) cursor.getString(index) else null
    } ?: "selected-image.${contentType.substringAfter("/", "jpg")}"
    val bytes = contentResolver.openInputStream(uri)?.use { it.readBytes() } ?: return null
    return SelectedImage(filename = filename, contentType = contentType, bytes = bytes)
}

fun Bitmap.toPngBytes(): ByteArray =
    ByteArrayOutputStream().use { output ->
        compress(Bitmap.CompressFormat.PNG, 100, output)
        output.toByteArray()
    }
