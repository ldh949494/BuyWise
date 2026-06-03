package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.CameraAlt
import androidx.compose.material.icons.outlined.ImageSearch
import androidx.compose.material.icons.outlined.Inventory2
import androidx.compose.material.icons.outlined.PhotoLibrary
import androidx.compose.material.icons.outlined.Refresh
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Button
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.buywise.android.data.VisionResult
import com.buywise.android.ui.BuyWiseDimens
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.components.FloatingGlassCard
import com.buywise.android.ui.components.FloatingGlassTone

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
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
                Surface(color = BuyWiseTheme.colors.accentSoft, shape = RoundedCornerShape(14.dp), modifier = Modifier.size(56.dp)) {
                    Icon(Icons.Outlined.CameraAlt, contentDescription = null, tint = BuyWiseTheme.colors.accent, modifier = Modifier.padding(14.dp))
                }
                Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text("识别商品", style = MaterialTheme.typography.titleLarge, color = BuyWiseTheme.colors.ink)
                    Text(
                        selectedImageName?.let { "已选择：$it" } ?: "选择图片或用语音描述需求，再带入导购推荐。",
                        color = BuyWiseTheme.colors.muted,
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
            }
            Row(horizontalArrangement = Arrangement.spacedBy(14.dp), modifier = Modifier.fillMaxWidth()) {
                Surface(
                    color = BuyWiseTheme.colors.panelAlt,
                    shape = RoundedCornerShape(16.dp),
                    border = CardDefaults.outlinedCardBorder(),
                    modifier = Modifier.size(width = 150.dp, height = 150.dp),
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Icon(Icons.Outlined.ImageSearch, contentDescription = null, tint = BuyWiseTheme.colors.primary, modifier = Modifier.size(42.dp))
                    }
                }
                Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Button(onClick = onRunVisionDemo, enabled = !isLoading, modifier = Modifier.fillMaxWidth()) {
                        Icon(Icons.Outlined.ImageSearch, contentDescription = null)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("识别图片")
                    }
                    OutlinedButton(onClick = onRunSpeechDemo, enabled = !isLoading, modifier = Modifier.fillMaxWidth()) {
                        Icon(Icons.Outlined.CameraAlt, contentDescription = null)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("语音描述")
                    }
                    FilledTonalButton(onClick = onUseQuery, enabled = hasQuery && !isLoading, modifier = Modifier.fillMaxWidth()) {
                        Icon(Icons.Outlined.Inventory2, contentDescription = null)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("带入导购")
                    }
                }
            }
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                OutlinedButton(onClick = onPickImage, enabled = !isLoading, modifier = Modifier.weight(1f)) {
                    Icon(Icons.Outlined.PhotoLibrary, contentDescription = null)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("相册")
                }
                OutlinedButton(onClick = onTakePhoto, enabled = !isLoading, modifier = Modifier.weight(1f)) {
                    Icon(Icons.Outlined.CameraAlt, contentDescription = null)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("拍照")
                }
                OutlinedButton(onClick = onRunVisionDemo, enabled = !isLoading, modifier = Modifier.weight(1f)) {
                    Icon(Icons.Outlined.Refresh, contentDescription = null)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("重识别")
                }
            }
        }
    }
}

fun VisionResult.displayVisionSummary(query: String?): String {
    val labelsText = labels.takeIf { it.isNotEmpty() }?.joinToString(" / ") ?: "暂无明确标签"
    val generatedQuery = query?.takeIf { it.isNotBlank() } ?: title.takeIf { it != "等待识别商品" } ?: "白色 无线 紧凑机械键盘"
    return "识别结果：$labelsText\n用于导购：$generatedQuery"
}
