import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
    id("org.jetbrains.kotlin.plugin.serialization")
}

android {
    namespace = "com.buywise.android"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.buywise.android"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0"
        val apiBaseUrl = providers.gradleProperty("ANDROID_API_BASE_URL")
            .orElse(providers.environmentVariable("ANDROID_API_BASE_URL"))
            .orElse("http://10.0.2.2:8000")
        buildConfigField("String", "BUYWISE_API_BASE_URL", "\"${apiBaseUrl.get()}\"")
        val uploadToken = providers.gradleProperty("BUYWISE_UPLOAD_TOKEN")
            .orElse(providers.environmentVariable("BUYWISE_UPLOAD_TOKEN"))
            .orElse("upload-token")
        buildConfigField("String", "BUYWISE_UPLOAD_TOKEN", "\"${uploadToken.get()}\"")
        val betaToken = providers.gradleProperty("BUYWISE_BETA_TOKEN")
            .orElse(providers.environmentVariable("BUYWISE_BETA_TOKEN"))
            .orElse("")
        buildConfigField("String", "BUYWISE_BETA_TOKEN", "\"${betaToken.get()}\"")
        val showDebugInfo = providers.gradleProperty("BUYWISE_SHOW_DEBUG_INFO")
            .orElse(providers.environmentVariable("BUYWISE_SHOW_DEBUG_INFO"))
            .orElse("false")
        buildConfigField("Boolean", "BUYWISE_SHOW_DEBUG_INFO", showDebugInfo.get())
    }

    buildFeatures {
        buildConfig = true
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

}

kotlin {
    compilerOptions {
        jvmTarget.set(JvmTarget.JVM_17)
    }
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2026.03.00")

    implementation(composeBom)
    androidTestImplementation(composeBom)

    implementation("androidx.activity:activity-compose:1.12.3")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.10.0")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.10.0")
    implementation("androidx.navigation:navigation-compose:2.9.7")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.9.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.squareup.okhttp3:okhttp-sse:4.12.0")
    implementation("io.coil-kt.coil3:coil-compose:3.4.0")

    debugImplementation("androidx.compose.ui:ui-tooling")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}
