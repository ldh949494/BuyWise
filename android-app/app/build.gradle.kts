import org.gradle.api.GradleException
import org.jetbrains.kotlin.gradle.dsl.JvmTarget
import java.util.Properties

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
    id("org.jetbrains.kotlin.plugin.serialization")
}

val localProperties = Properties().apply {
    val localPropertiesFile = rootProject.file("local.properties")
    if (localPropertiesFile.isFile) {
        localPropertiesFile.inputStream().use(::load)
    }
}

fun localProperty(name: String): String? =
    localProperties.getProperty(name)?.takeIf { it.isNotBlank() }

fun configValue(name: String, defaultValue: String) =
    providers.gradleProperty(name)
        .orElse(providers.environmentVariable(name))
        .orElse(providers.provider { localProperty(name) })
        .orElse(defaultValue)

fun envValue(name: String): String? =
    providers.environmentVariable(name).orNull?.takeIf { it.isNotBlank() }

val releaseSigningEnvNames = listOf(
    "ANDROID_RELEASE_KEYSTORE_FILE",
    "ANDROID_RELEASE_KEYSTORE_PASSWORD",
    "ANDROID_RELEASE_KEY_ALIAS",
    "ANDROID_RELEASE_KEY_PASSWORD",
)
val releaseSigningValues = releaseSigningEnvNames.associateWith(::envValue)
val hasReleaseSigning = releaseSigningEnvNames.all { releaseSigningValues[it] != null }
val isReleaseBuildRequested = gradle.startParameter.taskNames.any { taskName ->
    taskName.contains("Release", ignoreCase = true)
}

fun releaseSigningValue(name: String): String =
    releaseSigningValues[name] ?: throw GradleException("Missing release signing value: $name")

if (isReleaseBuildRequested && !hasReleaseSigning) {
    throw GradleException(
        "Release signing requires ${releaseSigningEnvNames.joinToString(", ")} environment variables."
    )
}

android {
    namespace = "com.buywise.android"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.buywise.android"
        minSdk = 26
        targetSdk = 36
        versionCode = 8
        versionName = "0.1.8"
        val apiBaseUrl = configValue("ANDROID_API_BASE_URL", "http://10.0.2.2:8000")
        buildConfigField("String", "BUYWISE_API_BASE_URL", "\"${apiBaseUrl.get()}\"")
        val uploadToken = configValue("BUYWISE_UPLOAD_TOKEN", "upload-token")
        buildConfigField("String", "BUYWISE_UPLOAD_TOKEN", "\"${uploadToken.get()}\"")
        val betaToken = configValue("BUYWISE_BETA_TOKEN", "")
        buildConfigField("String", "BUYWISE_BETA_TOKEN", "\"${betaToken.get()}\"")
        val showDebugInfo = configValue("BUYWISE_SHOW_DEBUG_INFO", "false")
        buildConfigField("Boolean", "BUYWISE_SHOW_DEBUG_INFO", showDebugInfo.get())
    }

    buildFeatures {
        buildConfig = true
    }

    signingConfigs {
        if (hasReleaseSigning) {
            create("release") {
                storeFile = rootProject.file(releaseSigningValue("ANDROID_RELEASE_KEYSTORE_FILE"))
                storePassword = releaseSigningValue("ANDROID_RELEASE_KEYSTORE_PASSWORD")
                keyAlias = releaseSigningValue("ANDROID_RELEASE_KEY_ALIAS")
                keyPassword = releaseSigningValue("ANDROID_RELEASE_KEY_PASSWORD")
            }
        }
    }

    buildTypes {
        release {
            if (hasReleaseSigning) {
                signingConfig = signingConfigs.getByName("release")
            }
        }
    }

    lint {
        disable += setOf(
            "GradleDependency",
            "NewerVersionAvailable",
            "ObsoleteSdkInt",
        )
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
    implementation("androidx.navigation:navigation-compose:2.9.8")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.9.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.squareup.okhttp3:okhttp-sse:4.12.0")
    implementation("io.coil-kt.coil3:coil-compose:3.4.0")
    implementation("io.coil-kt.coil3:coil-network-okhttp:3.4.0")

    testImplementation("junit:junit:4.13.2")

    debugImplementation("androidx.compose.ui:ui-tooling")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}
