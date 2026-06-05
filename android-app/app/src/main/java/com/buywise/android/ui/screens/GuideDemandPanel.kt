package com.buywise.android.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.buywise.android.ui.BuyWiseDimens
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.components.FloatingGlassCard
import com.buywise.android.ui.components.FloatingGlassTone

@Composable
fun DemandPanel(query: String, summary: String, onModify: () -> Unit) {
    val profile = demandProfile(query = query, summary = summary)
    FloatingGlassCard(
        tone = FloatingGlassTone.Primary,
        radius = 14.dp,
        elevated = false,
        contentPadding = 12.dp,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    "已按这些需求推荐",
                    modifier = Modifier.weight(1f),
                    style = MaterialTheme.typography.titleMedium,
                    color = BuyWiseTheme.colors.ink,
                    fontWeight = FontWeight.Bold,
                )
                Text(
                    "修改",
                    modifier = Modifier
                        .background(BuyWiseTheme.colors.panelRaised, RoundedCornerShape(BuyWiseDimens.ChipRadius.dp))
                        .clickable(onClick = onModify)
                        .padding(horizontal = 12.dp, vertical = 7.dp),
                    color = BuyWiseTheme.colors.primary,
                    style = MaterialTheme.typography.labelMedium,
                    fontWeight = FontWeight.Bold,
                )
            }
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                DemandChip("预算", profile.budget, BuyWiseTheme.colors.accent)
                DemandChip("场景", profile.scene, BuyWiseTheme.colors.secondary)
                DemandChip("偏好", profile.preference, BuyWiseTheme.colors.primary)
            }
            if (summary.isNotBlank()) {
                Text(
                    summary,
                    color = BuyWiseTheme.colors.muted,
                    style = MaterialTheme.typography.bodyMedium,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis,
                )
            }
        }
    }
}

@Composable
private fun DemandChip(label: String, value: String, accent: Color) {
    Row(
        modifier = Modifier
            .background(BuyWiseTheme.colors.panelRaised, RoundedCornerShape(BuyWiseDimens.ChipRadius.dp))
            .padding(horizontal = 10.dp, vertical = 7.dp),
        horizontalArrangement = Arrangement.spacedBy(5.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            label,
            color = BuyWiseTheme.colors.muted,
            style = MaterialTheme.typography.labelMedium,
            maxLines = 1,
        )
        Text(
            value,
            color = accent,
            style = MaterialTheme.typography.labelMedium,
            fontWeight = FontWeight.Bold,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
        )
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
