package com.buywise.android.data

import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import org.junit.Assert.assertEquals
import org.junit.Test

class AuthDtoSerializationTest {
    private val json = Json { explicitNulls = false }

    @Test
    fun otpRequestUsesBackendFieldNames() {
        val payload = json.encodeToString(OtpRequestDto(phone = "13812345678"))

        assertEquals("""{"phone":"13812345678"}""", payload)
    }

    @Test
    fun otpVerifyUsesBackendFieldNames() {
        val payload = json.encodeToString(
            OtpVerifyRequestDto(
                phone = "13812345678",
                code = "123456",
                deviceName = "Android",
            ),
        )

        assertEquals("""{"phone":"13812345678","code":"123456","device_name":"Android"}""", payload)
    }
}
