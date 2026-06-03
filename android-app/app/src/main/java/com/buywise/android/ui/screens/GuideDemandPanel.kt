package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Tune
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.components.EvidenceTag
import com.buywise.android.ui.components.EvidenceTone
import com.buywise.android.ui.components.FloatingGlassCard
import com.buywise.android.ui.components.FloatingGlassTone

@Composable
fun DemandPanel(query: String, summary: String) {
    val profile = demandProfile(query = query, summary = summary)
    FloatingGlassCard(tone = FloatingGlassTone.Primary, contentPadding = 16.dp) {
        Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp), verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Outlined.Tune, contentDescription = null, tint = BuyWiseTheme.colors.primary)
                Text("需求摘要", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
                Spacer(modifier = Modifier.weight(1f))
                EvidenceTag("可修改")
            }
            FlowRow(horizontalArrangement = Arrangement.spacedBy(10.dp), verticalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.fillMaxWidth()) {
                DemandTile("意图", "商品推荐", tone = EvidenceTone.Info, modifier = Modifier.weight(1f))
                DemandTile("预算", profile.budget, tone = EvidenceTone.Warning, modifier = Modifier.weight(1f))
                DemandTile("场景", profile.scene, tone = EvidenceTone.Success, modifier = Modifier.weight(1f))
                DemandTile("偏好", profile.preference, tone = EvidenceTone.Info, modifier = Modifier.weight(1f))
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
    tone: EvidenceTone,
    modifier: Modifier = Modifier,
) {
    FloatingGlassCard(
        modifier = modifier,
        tone = tone.toFloatingGlassTone(),
        elevated = false,
        fillMaxWidth = false,
        contentPadding = 12.dp,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
            EvidenceTag(label, tone = tone)
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

private fun EvidenceTone.toFloatingGlassTone(): FloatingGlassTone = when (this) {
    EvidenceTone.Info -> FloatingGlassTone.Primary
    EvidenceTone.Success -> FloatingGlassTone.Success
    EvidenceTone.Warning -> FloatingGlassTone.Warm
    EvidenceTone.Danger -> FloatingGlassTone.Warm
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
