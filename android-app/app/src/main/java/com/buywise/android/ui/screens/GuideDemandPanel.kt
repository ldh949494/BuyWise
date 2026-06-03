package com.buywise.android.ui.screens

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Tune
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.components.EvidenceTag
import com.buywise.android.ui.components.FloatingGlassCard
import com.buywise.android.ui.components.FloatingGlassTone

@Composable
fun DemandPanel(query: String, summary: String) {
    val profile = demandProfile(query = query, summary = summary)
    FloatingGlassCard(tone = FloatingGlassTone.Neutral, contentPadding = 16.dp, elevated = false) {
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp), verticalAlignment = Alignment.CenterVertically) {
                Surface(color = BuyWiseTheme.colors.primarySoft, shape = RoundedCornerShape(10.dp), modifier = Modifier.size(34.dp)) {
                    Icon(
                        Icons.Outlined.Tune,
                        contentDescription = null,
                        tint = BuyWiseTheme.colors.primary,
                        modifier = Modifier.padding(8.dp),
                    )
                }
                Text("需求摘要", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
                Spacer(modifier = Modifier.weight(1f))
                EvidenceTag("可修改")
            }
            DemandSummaryGrid(profile = profile)
            if (summary.isNotBlank()) {
                Text(summary, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
            }
        }
    }
}

@Composable
private fun DemandSummaryGrid(profile: DemandProfile) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        color = BuyWiseTheme.colors.panelAlt.copy(alpha = 0.72f),
        border = BorderStroke(1.dp, BuyWiseTheme.colors.border),
    ) {
        Column(modifier = Modifier.padding(horizontal = 12.dp, vertical = 10.dp)) {
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {
                DemandField("意图", "商品推荐", BuyWiseTheme.colors.primary, modifier = Modifier.weight(1f))
                DemandField("预算", profile.budget, BuyWiseTheme.colors.accent, modifier = Modifier.weight(1f))
            }
            HorizontalDivider(modifier = Modifier.padding(vertical = 8.dp), color = BuyWiseTheme.colors.border)
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {
                DemandField("场景", profile.scene, BuyWiseTheme.colors.secondary, modifier = Modifier.weight(1f))
                DemandField("偏好", profile.preference, BuyWiseTheme.colors.primary, modifier = Modifier.weight(1f))
            }
        }
    }
}

@Composable
private fun DemandField(label: String, value: String, accent: Color, modifier: Modifier = Modifier) {
    Row(
        modifier = modifier.defaultMinSize(minHeight = 44.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(
            modifier = Modifier
                .size(8.dp)
                .background(accent, RoundedCornerShape(999.dp)),
        )
        Column(verticalArrangement = Arrangement.spacedBy(2.dp), modifier = Modifier.weight(1f)) {
            Text(label, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.labelMedium)
            Text(
                value,
                color = BuyWiseTheme.colors.ink,
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.SemiBold,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
        }
    }
}

private data class DemandProfile(val budget: String, val scene: String, val preference: String)

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
    )
}
