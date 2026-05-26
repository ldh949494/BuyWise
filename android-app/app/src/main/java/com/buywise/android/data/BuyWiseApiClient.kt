package com.buywise.android.data

import java.io.IOException
import okhttp3.MediaType
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject

internal class BuyWiseApiClient(
    private val httpClient: OkHttpClient,
    private val baseUrl: String,
    private val betaToken: String?,
    private val uploadToken: String?,
) {
    @Throws(IOException::class)
    fun getJson(path: String, requireAuth: Boolean = false): JSONObject {
        val request = authorized(Request.Builder().url("$baseUrl$path").get(), requireAuth).build()
        return executeJson(request)
    }

    @Throws(IOException::class)
    fun postJson(path: String, body: RequestBody, requireAuth: Boolean = false): JSONObject {
        val request = authorized(Request.Builder().url("$baseUrl$path").post(body), requireAuth).build()
        return executeJson(request)
    }

    @Throws(IOException::class)
    fun uploadDemoFile(filename: String, contentType: MediaType, bytes: ByteArray): UploadResult {
        val body = MultipartBody.Builder()
            .setType(MultipartBody.FORM)
            .addFormDataPart("file", filename, bytes.toRequestBody(contentType))
            .build()
        val request = Request.Builder()
            .url("$baseUrl/api/v1/upload")
            .apply {
                uploadToken?.let { header("Authorization", "Bearer $it") }
            }
            .post(body)
            .build()
        val json = executeJson(request)
        return UploadResult(
            url = json.optString("url"),
            filename = json.optString("filename"),
        )
    }

    private fun executeJson(request: Request): JSONObject {
        httpClient.newCall(request).execute().use { response ->
            val body = response.body?.string().orEmpty()
            if (!response.isSuccessful) {
                throw IOException("HTTP ${response.code}: ${body.ifBlank { response.message }}")
            }
            return JSONObject(body)
        }
    }

    private fun authorized(builder: Request.Builder, requireAuth: Boolean): Request.Builder {
        if (!requireAuth) {
            return builder
        }
        val token = betaToken ?: throw IOException("需要配置 BUYWISE_BETA_TOKEN 才能使用 beta 用户能力")
        return builder.header("Authorization", "Bearer $token")
    }
}

internal data class UploadResult(val url: String, val filename: String)
