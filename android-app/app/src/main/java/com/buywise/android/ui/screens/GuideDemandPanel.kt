package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.AutoAwesome
import androidx.compose.material.icons.outlined.Category
import androidx.compose.material.icons.outlined.Inventory2
import androidx.compose.material.icons.outlined.Tune
import androidx.compose.material.icons.outlined.Wallet
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.buywise.android.ui.BuyWiseDimens
import com.buywise.android.ui.BuyWiseTheme

@Composable
fun DemandPanel(query: String, summary: String) {
    val profile = demandProfile(query = query, summary = summary)
    Card(
        colors = CardDefaults.cardColors(containerColor = BuyWiseTheme.colors.panel),
        shape = RoundedCornerShape(BuyWiseDimens.CardRadius.dp),
        border = CardDefaults.outlinedCardBorder(),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
    ) {
        Column(modifier = Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp), verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Outlined.Tune, contentDescription = null, tint = BuyWiseTheme.colors.primary)
                Text("结构化需求画像", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
                Spacer(modifier = Modifier.weight(1f))
                Text("AI 已提取", color = BuyWiseTheme.colors.primary, fontWeight = FontWeight.Bold)
            }
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {
                DemandTile("预算", profile.budget, Icons.Outlined.Wallet, Modifier.weight(1f))
                DemandTile("场景", profile.scene, Icons.Outlined.Inventory2, Modifier.weight(1f))
            }
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {
                DemandTile("偏好", profile.preference, Icons.Outlined.AutoAwesome, Modifier.weight(1f))
                DemandTile("品类", profile.category, Icons.Outlined.Category, Modifier.weight(1f))
            }
            if (summary.isNotBlank()) {
                Text(summary, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
            }
        }
    }
}

@Composable
private fun DemandTile(
    label: String,
    value: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    modifier: Modifier = Modifier,
) {
    Surface(
        color = BuyWiseTheme.colors.panel,
        shape = RoundedCornerShape(16.dp),
        border = CardDefaults.outlinedCardBorder(),
        modifier = modifier,
    ) {
        Row(
            modifier = Modifier.padding(14.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Surface(color = BuyWiseTheme.colors.primarySoft, shape = RoundedCornerShape(12.dp), modifier = Modifier.size(42.dp)) {
                Icon(icon, contentDescription = null, tint = BuyWiseTheme.colors.primary, modifier = Modifier.padding(10.dp))
            }
            Column(verticalArrangement = Arrangement.spacedBy(4.dp), modifier = Modifier.weight(1f)) {
                Text(label, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.labelMedium)
                Text(
                    value,
                    color = BuyWiseTheme.colors.ink,
                    fontWeight = FontWeight.Bold,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis,
                )
            }
        }
    }
}

private data class DemandProfile(val budget: String, val scene: String, val preference: String, val category: String)

private fun demandProfile(query: String, summary: String): DemandProfile {
    val text = "$query $summary"
    return DemandProfile(
        budget = Regex("""\d+\s*(元|以内|以下)?""").find(text)?.value?.replace(" ", "") ?: "待确认",
        scene = when {
            "宿舍" in text -> "宿舍 / 写代码"
            "通勤" in text -> "通勤"
            "办公" in text -> "办公"
            else -> "日常使用"
        },
        preference = listOfNotNull(
            "低噪音".takeIf { "低噪" in text || "静音" in text || "声音小" in text },
            "收纳友好".takeIf { "收纳" in text || "便携" in text },
            "预算友好".takeIf { "预算" in text || "以内" in text },
        ).joinToString(" / ").ifBlank { "实用优先" },
        category = when {
            "键盘" in text -> "机械键盘"
            "耳机" in text -> "耳机"
            "鼠标" in text -> "鼠标"
            else -> "数码商品"
        },
    )
}
