package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
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
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
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
import com.buywise.android.ui.components.SoftTag

@Composable
fun UploadPanel(
    isLoading: Boolean,
    hasQuery: Boolean,
    onRunVisionDemo: () -> Unit,
    onRunSpeechDemo: () -> Unit,
    onUseQuery: () -> Unit,
) {
    Card(
        colors = CardDefaults.cardColors(containerColor = BuyWiseTheme.colors.panel),
        shape = RoundedCornerShape(BuyWiseDimens.CardRadius.dp),
        border = CardDefaults.outlinedCardBorder(),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
    ) {
        Column(modifier = Modifier.fillMaxWidth().padding(18.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
            Surface(color = BuyWiseTheme.colors.accentSoft, shape = RoundedCornerShape(14.dp), modifier = Modifier.size(56.dp)) {
                Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center) {
                    Icon(Icons.Outlined.CameraAlt, contentDescription = null, tint = BuyWiseTheme.colors.accent)
                }
            }
            Text("上传商品图片", style = MaterialTheme.typography.titleLarge, color = BuyWiseTheme.colors.ink)
            Text(
                "当前使用演示资源，不申请相机和麦克风权限。",
                color = BuyWiseTheme.colors.muted,
                style = MaterialTheme.typography.bodyMedium,
            )
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf("上传商品图片", "识别商品类别", "提取视觉特征", "关联推荐商品").forEach { SoftTag(it) }
            }
            FilledTonalButton(onClick = onRunVisionDemo, enabled = !isLoading) {
                Icon(Icons.Outlined.ImageSearch, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text("识别图片")
            }
            OutlinedButton(onClick = onRunSpeechDemo, enabled = !isLoading) {
                Icon(Icons.Outlined.CameraAlt, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text("语音描述需求")
            }
            OutlinedButton(onClick = onUseQuery, enabled = hasQuery && !isLoading) {
                Icon(Icons.Outlined.Inventory2, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text("生成导购建议")
            }
        }
    }
}

fun VisionResult.displayVisionSummary(query: String?): String {
    val labelsText = labels.takeIf { it.isNotEmpty() }?.joinToString(" / ") ?: "机械键盘 / 白色 / 紧凑布局"
    val generatedQuery = query?.takeIf { it.isNotBlank() } ?: title.takeIf { it != "等待识别商品" } ?: "白色 无线 紧凑机械键盘"
    return "类别：机械键盘\n颜色：白色\n特征：$labelsText\n生成 query：$generatedQuery"
}
