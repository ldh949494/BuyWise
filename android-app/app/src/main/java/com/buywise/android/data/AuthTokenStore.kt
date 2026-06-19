package com.buywise.android.data

import android.content.Context
import androidx.core.content.edit

class AuthTokenStore(context: Context) {
    private val prefs = context.applicationContext.getSharedPreferences("buywise_auth", Context.MODE_PRIVATE)

    fun getAccessToken(): String? = prefs.getString(KEY_ACCESS_TOKEN, null)?.takeIf { it.isNotBlank() }

    fun getRefreshToken(): String? = prefs.getString(KEY_REFRESH_TOKEN, null)?.takeIf { it.isNotBlank() }

    fun getPhoneMasked(): String? = prefs.getString(KEY_PHONE_MASKED, null)?.takeIf { it.isNotBlank() }

    fun save(tokens: AuthTokens, user: AuthUser? = null) {
        prefs.edit {
            putString(KEY_ACCESS_TOKEN, tokens.accessToken)
            putString(KEY_REFRESH_TOKEN, tokens.refreshToken)
            putString(KEY_PHONE_MASKED, user?.phoneMasked ?: getPhoneMasked().orEmpty())
        }
    }

    fun clear() {
        prefs.edit { clear() }
    }

    companion object {
        private const val KEY_ACCESS_TOKEN = "access_token"
        private const val KEY_REFRESH_TOKEN = "refresh_token"
        private const val KEY_PHONE_MASKED = "phone_masked"
    }
}
