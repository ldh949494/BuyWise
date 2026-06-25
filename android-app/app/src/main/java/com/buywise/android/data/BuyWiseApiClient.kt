package com.buywise.android.data

import com.buywise.android.BuildConfig
import java.io.IOException
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import okhttp3.MediaType
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject

internal class BuyWiseApiClient(
    private val httpClient: OkHttpClient,
    private val baseUrl: String,
    private val betaToken: String?,
    private val uploadToken: String?,
) {
    private var accessToken: String? = null
    private var refreshToken: String? = null
    val hasBetaToken: Boolean = betaToken != null
    val betaCapability: BetaCapability =
        if (hasBetaToken || accessToken != null) {
            BetaCapability.Enabled
        } else {
            val message = if (BuildConfig.BUYWISE_SHOW_DEBUG_INFO) {
                BetaCapability.DEBUG_TOKEN_REQUIRED_MESSAGE
            } else {
                BetaCapability.TOKEN_REQUIRED_MESSAGE
            }
            BetaCapability(false, message)
        }

    @PublishedApi
    internal val json = Json {
        ignoreUnknownKeys = true
        explicitNulls = false
    }
    @PublishedApi
    internal val jsonMediaType = mediaType("application/json; charset=utf-8")

    inline fun <reified T> get(path: String, requireAuth: Boolean = false): T =
        json.decodeFromString(executeText(authorized(Request.Builder().url("$baseUrl$path").get(), requireAuth).build()))

    inline fun <reified T> getWithOptionalUserAuth(path: String): T =
        json.decodeFromString(executeText(optionalUserAuthorized(Request.Builder().url("$baseUrl$path").get()).build()))

    inline fun <reified RequestDto, reified ResponseDto> post(
        path: String,
        body: RequestDto,
        requireAuth: Boolean = false,
    ): ResponseDto {
        val requestBody = json.encodeToString(body).toRequestBody(jsonMediaType)
        val request = authorized(Request.Builder().url("$baseUrl$path").post(requestBody), requireAuth).build()
        return json.decodeFromString(executeText(request))
    }

    inline fun <reified RequestDto, reified ResponseDto> postWithOptionalUserAuth(
        path: String,
        body: RequestDto,
    ): ResponseDto {
        val requestBody = json.encodeToString(body).toRequestBody(jsonMediaType)
        val request = optionalUserAuthorized(Request.Builder().url("$baseUrl$path").post(requestBody)).build()
        return json.decodeFromString(executeText(request))
    }

    inline fun <reified RequestDto> postUnit(path: String, body: RequestDto, requireAuth: Boolean = false) {
        val requestBody = json.encodeToString(body).toRequestBody(jsonMediaType)
        executeText(authorized(Request.Builder().url("$baseUrl$path").post(requestBody), requireAuth).build())
    }

    inline fun <reified RequestDto, reified ResponseDto> patch(
        path: String,
        body: RequestDto,
        requireAuth: Boolean = false,
    ): ResponseDto {
        val requestBody = json.encodeToString(body).toRequestBody(jsonMediaType)
        val request = authorized(Request.Builder().url("$baseUrl$path").patch(requestBody), requireAuth).build()
        return json.decodeFromString(executeText(request))
    }

    fun postEmpty(path: String, requireAuth: Boolean = false): OrderResponseDto {
        val request = authorized(Request.Builder().url("$baseUrl$path").post("{}".toRequestBody(jsonMediaType)), requireAuth).build()
        return json.decodeFromString(executeText(request))
    }

    fun guideStreamRequest(body: GuideStreamRequestDto): Request =
        guideStreamRequest("/api/v1/ai/guide/stream", body)

    fun guideFollowUpStreamRequest(body: GuideStreamRequestDto): Request =
        guideStreamRequest("/api/v1/ai/guide/follow-up/stream", body)

    fun compareFollowUpStreamRequest(body: CompareFollowUpRequestDto): Request {
        val requestBody = json.encodeToString(body).toRequestBody(jsonMediaType)
        return Request.Builder()
            .url("$baseUrl/api/v1/ai/compare/follow-up/stream")
            .apply { accessToken?.let { header("Authorization", "Bearer $it") } }
            .post(requestBody)
            .build()
    }

    private fun guideStreamRequest(path: String, body: GuideStreamRequestDto): Request {
        val requestBody = json.encodeToString(body).toRequestBody(jsonMediaType)
        return Request.Builder()
            .url("$baseUrl$path")
            .apply { accessToken?.let { header("Authorization", "Bearer $it") } }
            .post(requestBody)
            .build()
    }

    @Throws(IOException::class)
    fun getJson(path: String, requireAuth: Boolean = false): JSONObject {
        val request = authorized(Request.Builder().url("$baseUrl$path").get(), requireAuth).build()
        return executeJson(request)
    }

    @Throws(IOException::class)
    fun getJsonWithOptionalUserAuth(path: String): JSONObject {
        val request = optionalUserAuthorized(Request.Builder().url("$baseUrl$path").get()).build()
        return executeJson(request)
    }

    @Throws(IOException::class)
    fun postJson(path: String, body: RequestBody, requireAuth: Boolean = false): JSONObject {
        val request = authorized(Request.Builder().url("$baseUrl$path").post(body), requireAuth).build()
        return executeJson(request)
    }

    @Throws(IOException::class)
    fun putJson(path: String, body: RequestBody, requireAuth: Boolean = false): JSONObject {
        val request = authorized(Request.Builder().url("$baseUrl$path").put(body), requireAuth).build()
        return executeJson(request)
    }

    @Throws(IOException::class)
    fun patchJson(path: String, body: RequestBody, requireAuth: Boolean = false): JSONObject {
        val request = authorized(Request.Builder().url("$baseUrl$path").patch(body), requireAuth).build()
        return executeJson(request)
    }

    @Throws(IOException::class)
    fun delete(path: String, requireAuth: Boolean = false) {
        val request = authorized(Request.Builder().url("$baseUrl$path").delete(), requireAuth).build()
        executeText(request)
    }

    @Throws(IOException::class)
    fun uploadFile(filename: String, contentType: MediaType, bytes: ByteArray): UploadResult {
        val body = MultipartBody.Builder()
            .setType(MultipartBody.FORM)
            .addFormDataPart("file", filename, bytes.toRequestBody(contentType))
            .build()
        val request = Request.Builder()
            .url("$baseUrl/api/v1/upload")
            .apply {
                (accessToken ?: uploadToken)?.let { header("Authorization", "Bearer $it") }
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
        return JSONObject(executeText(request))
    }

    @PublishedApi
    internal fun executeText(request: Request): String {
        httpClient.newCall(request).execute().use { response ->
            val body = response.body?.string().orEmpty()
            if (!response.isSuccessful) {
                throw IOException("HTTP ${response.code}: ${body.ifBlank { response.message }}")
            }
            return body
        }
    }

    private fun authorized(builder: Request.Builder, requireAuth: Boolean): Request.Builder {
        if (!requireAuth) {
            return builder
        }
        val token = accessToken ?: betaToken ?: throw IOException(BetaCapability.TOKEN_REQUIRED_MESSAGE)
        return builder.header("Authorization", "Bearer $token")
    }

    private fun optionalUserAuthorized(builder: Request.Builder): Request.Builder =
        builder.apply { accessToken?.let { header("Authorization", "Bearer $it") } }

    fun setSessionTokens(accessToken: String?, refreshToken: String?) {
        this.accessToken = accessToken?.takeIf { it.isNotBlank() }
        this.refreshToken = refreshToken?.takeIf { it.isNotBlank() }
    }

    fun clearSessionTokens() {
        accessToken = null
        refreshToken = null
    }
}

internal data class UploadResult(val url: String, val filename: String)

internal fun mediaType(value: String): MediaType = value.toMediaType()
