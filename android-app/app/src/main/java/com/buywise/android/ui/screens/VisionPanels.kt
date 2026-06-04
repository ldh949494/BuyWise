package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.material3.Button
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp
import com.buywise.android.data.VisionResult
import com.buywise.android.ui.BuyWiseIcons
import com.buywise.android.ui.BuyWiseDimens
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.components.FloatingAssetBadge
import com.buywise.android.ui.components.FloatingGlassCard
import com.buywise.android.ui.components.FloatingGlassTone
import com.buywise.android.ui.components.TactileIconTone

@Composable
fun UploadPanel(
    isLoading: Boolean,
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
                    contentDescription = null,
                    tone = TactileIconTone.Primary,
                    size = 54.dp,
                    iconSize = 28.dp,
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
                    title = "上传音频",
                    subtitle = "点击录制",
                    icon = BuyWiseIcons.Speech,
                    modifier = Modifier.weight(1f),
                    enabled = !isLoading,
                    onClick = onRunSpeechDemo,
                )
            }
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                OutlinedButton(onClick = onPickImage, enabled = !isLoading, modifier = Modifier.weight(1f)) {
                    Icon(BuyWiseIcons.PhotoLibrary, contentDescription = null)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("相册")
                }
                OutlinedButton(onClick = onTakePhoto, enabled = !isLoading, modifier = Modifier.weight(1f)) {
                    Icon(BuyWiseIcons.Camera, contentDescription = null)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("拍照")
                }
                FilledTonalButton(onClick = onUseQuery, enabled = hasQuery && !isLoading, modifier = Modifier.weight(1f)) {
                    Icon(BuyWiseIcons.Guide, contentDescription = null)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("导购")
                }
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
    enabled: Boolean,
    onClick: () -> Unit,
) {
    FloatingGlassCard(
        modifier = modifier,
        tone = FloatingGlassTone.Neutral,
        radius = 16.dp,
        contentPadding = 16.dp,
        onClick = if (enabled) onClick else null,
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(8.dp)) {
            FloatingAssetBadge(icon = icon, contentDescription = null, size = 54.dp, iconSize = 26.dp)
            Text(title, color = BuyWiseTheme.colors.ink, style = MaterialTheme.typography.labelMedium)
            Text(subtitle, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.labelMedium)
        }
    }
}

fun VisionResult.displayVisionSummary(query: String?): String {
    val labelsText = labels.takeIf { it.isNotEmpty() }?.joinToString(" / ") ?: "暂无明确标签"
    val generatedQuery = query?.takeIf { it.isNotBlank() } ?: title.takeIf { it != "等待识别商品" } ?: "白色 无线 紧凑机械键盘"
    return "识别结果：$labelsText\n用于导购：$generatedQuery"
}
