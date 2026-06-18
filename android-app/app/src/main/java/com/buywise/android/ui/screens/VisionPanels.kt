package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.buywise.android.data.VisionResult
import com.buywise.android.ui.BuyWiseIcons
import com.buywise.android.ui.BuyWiseDimens
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.BuyWiseVisualAssets
import com.buywise.android.ui.components.FloatingAssetBadge
import com.buywise.android.ui.components.FloatingGlassCard
import com.buywise.android.ui.components.FloatingGlassTone
import com.buywise.android.ui.components.TactileIconTone

@Composable
fun UploadPanel(
    isLoading: Boolean,
    isRecordingAudio: Boolean,
    hasQuery: Boolean,
    selectedImageName: String?,
    onTakePhoto: () -> Unit,
    onPickImage: () -> Unit,
    onRunVisionDemo: () -> Unit,
    onRunSpeechDemo: () -> Unit,
    onUseQuery: () -> Unit,
) {
    FloatingGlassCard(
        tone = FloatingGlassTone.Warm,
        radius = BuyWiseDimens.HeroRadius.dp,
        contentPadding = 20.dp,
    ) {
        Column(modifier = Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(16.dp)) {
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp), verticalAlignment = Alignment.CenterVertically) {
                Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text("用图片或音频搜索", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
                    Text(selectedImageName?.let { "已选择：$it" } ?: "上传图片或描述声音，生成可带入导购的需求。", color = BuyWiseTheme.colors.muted)
                }
                FloatingAssetBadge(
                    icon = BuyWiseIcons.Camera,
                    assetRes = BuyWiseVisualAssets.Camera,
                    contentDescription = null,
                    tone = TactileIconTone.Primary,
                    size = 54.dp,
                    iconSize = 40.dp,
                )
            }
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {
                UploadModeCard(
                    title = "上传图片",
                    subtitle = "点击上传",
                    icon = BuyWiseIcons.Image,
                    modifier = Modifier.weight(1f),
                    enabled = !isLoading,
                    onClick = onPickImage,
                )
                UploadModeCard(
                    title = if (isRecordingAudio) "正在录音" else "语音输入",
                    subtitle = if (isRecordingAudio) "点击结束" else "点击录制",
                    icon = BuyWiseIcons.Speech,
                    modifier = Modifier.weight(1f),
                    selected = isRecordingAudio,
                    enabled = !isLoading,
                    onClick = onRunSpeechDemo,
                )
            }
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                VisionActionButton(
                    label = "相册",
                    icon = BuyWiseIcons.PhotoLibrary,
                    enabled = !isLoading,
                    modifier = Modifier.weight(1f),
                    onClick = onPickImage,
                )
                VisionActionButton(
                    label = "拍照",
                    icon = BuyWiseIcons.Camera,
                    enabled = !isLoading,
                    modifier = Modifier.weight(1f),
                    onClick = onTakePhoto,
                )
                VisionActionButton(
                    label = "导购",
                    icon = BuyWiseIcons.Guide,
                    enabled = hasQuery && !isLoading,
                    primary = true,
                    modifier = Modifier.weight(1f),
                    onClick = onUseQuery,
                )
            }
        }
    }
}

@Composable
private fun UploadModeCard(
    title: String,
    subtitle: String,
    icon: ImageVector,
    modifier: Modifier = Modifier,
    selected: Boolean = false,
    enabled: Boolean,
    onClick: () -> Unit,
) {
    val assetRes = when (icon) {
        BuyWiseIcons.Image -> BuyWiseVisualAssets.Camera
        BuyWiseIcons.Speech -> BuyWiseVisualAssets.Headphones
        else -> null
    }
    FloatingGlassCard(
        modifier = modifier,
        tone = if (selected) FloatingGlassTone.Primary else FloatingGlassTone.Neutral,
        radius = 16.dp,
        contentPadding = 16.dp,
        onClick = if (enabled) onClick else null,
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(8.dp)) {
            FloatingAssetBadge(
                icon = icon,
                assetRes = assetRes,
                contentDescription = null,
                size = 54.dp,
                iconSize = if (assetRes == null) 26.dp else 40.dp,
            )
            Text(title, color = BuyWiseTheme.colors.ink, style = MaterialTheme.typography.labelMedium)
            Text(subtitle, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.labelMedium)
        }
    }
}

@Composable
private fun VisionActionButton(
    label: String,
    icon: ImageVector,
    enabled: Boolean,
    modifier: Modifier = Modifier,
    primary: Boolean = false,
    onClick: () -> Unit,
) {
    val tone = when {
        primary && enabled -> FloatingGlassTone.SolidPrimary
        primary -> FloatingGlassTone.Neutral
        else -> FloatingGlassTone.Neutral
    }
    val foreground = when {
        primary && enabled -> Color.White
        enabled -> BuyWiseTheme.colors.ink
        else -> BuyWiseTheme.colors.muted
    }
    FloatingGlassCard(
        modifier = modifier,
        tone = tone,
        radius = 999.dp,
        contentPadding = 0.dp,
        elevated = true,
        onClick = if (enabled) onClick else null,
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 14.dp, vertical = 11.dp),
            horizontalArrangement = Arrangement.Center,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(icon, contentDescription = null, tint = foreground, modifier = Modifier.size(20.dp))
            Text(
                label,
                color = foreground,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                modifier = Modifier.padding(start = 8.dp),
            )
        }
    }
}

fun VisionResult.displayVisionSummary(query: String?): String {
    val labelsText = labels.takeIf { it.isNotEmpty() }?.joinToString(" / ") ?: "暂无明确标签"
    val generatedQuery = query?.takeIf { it.isNotBlank() } ?: title.takeIf { it.isNotBlank() } ?: "暂无可用导购词"
    return "识别结果：$labelsText\n用于导购：$generatedQuery"
}
