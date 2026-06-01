package com.buywise.android.data

import java.io.IOException

class AuthRepository internal constructor(
    private val apiClient: BuyWiseApiClient,
    private val tokenStore: AuthTokenStore,
) {
    fun currentState(): AccountState {
        val phone = tokenStore.getPhoneMasked()
        return AccountState(
            isLoggedIn = phone != null,
            phoneMasked = phone,
            canUseGuestMode = apiClient.hasBetaToken,
        )
    }

    @Throws(IOException::class)
    fun requestOtp(phone: String): String? {
        val response: OtpRequestResponseDto = apiClient.post(
            "/api/v1/auth/otp/request",
            OtpRequestDto(phone = phone),
        )
        return response.debugOtp
    }

    @Throws(IOException::class)
    fun verifyOtp(phone: String, code: String): AccountState {
        val response: AuthTokenResponseDto = apiClient.post(
            "/api/v1/auth/otp/verify",
            OtpVerifyRequestDto(phone = phone, code = code, deviceName = "Android"),
        )
        tokenStore.save(response.toTokens(), response.user)
        apiClient.setSessionTokens(response.accessToken, response.refreshToken)
        return currentState().copy(statusMessage = "登录成功")
    }

    @Throws(IOException::class)
    fun restoreSession(): AccountState {
        val refreshToken = tokenStore.getRefreshToken() ?: return currentState()
        apiClient.setSessionTokens(tokenStore.getAccessToken(), refreshToken)
        val response: RefreshResponseDto = apiClient.post(
            "/api/v1/auth/refresh",
            RefreshRequestDto(refreshToken = refreshToken),
        )
        tokenStore.save(response.toTokens())
        apiClient.setSessionTokens(response.accessToken, response.refreshToken)
        return currentState()
    }

    @Throws(IOException::class)
    fun logout(): AccountState {
        val refreshToken = tokenStore.getRefreshToken()
        if (refreshToken != null) {
            runCatching {
                apiClient.postUnit("/api/v1/auth/logout", LogoutRequestDto(refreshToken = refreshToken))
            }
        }
        tokenStore.clear()
        apiClient.clearSessionTokens()
        return currentState().copy(statusMessage = "已退出登录")
    }

    fun enterGuestMode(): AccountState =
        currentState().copy(statusMessage = "已进入游客体验模式，受保护功能使用评审体验 token。")
}
