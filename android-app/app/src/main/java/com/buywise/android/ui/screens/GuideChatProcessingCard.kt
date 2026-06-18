package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.buywise.android.data.GuideResultStatus
import com.buywise.android.data.GuideState
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.components.FloatingGlassCard
import com.buywise.android.ui.components.FloatingGlassTone
import com.buywise.android.ui.components.StatusChecklistRow

@Composable
internal fun GuideProcessingCard(state: GuideState, onIgnoreSavedPreferencesChange: (Boolean) -> Unit) {
    val isCompareChat = state.compareChatContext != null
    val isClarifying = state.resultStatus == GuideResultStatus.Clarifying
    val hasGuideResults = state.recommendations.isNotEmpty() || state.bundlePlans.isNotEmpty()
    FloatingGlassCard(
        tone = FloatingGlassTone.Neutral,
        radius = 16.dp,
        contentPadding = 14.dp,
        elevated = false,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
            StatusChecklistRow(
                label = if (isCompareChat) "对比上下文" else "理解需求",
                status = if (isCompareChat) "已带入" else if (state.query.isNotBlank()) "完成" else "等待中",
                done = isCompareChat || state.query.isNotBlank(),
            )
            StatusChecklistRow(
                label = if (isCompareChat) "对比商品" else if (isClarifying) "补充目标" else "检索商品",
                status = when {
                    isCompareChat -> "完成"
                    isClarifying -> "等待补充"
                    hasGuideResults -> "完成"
                    state.isStreaming -> "搜索中"
                    else -> "待开始"
                },
                done = isCompareChat || hasGuideResults,
            )
            StatusChecklistRow(
                label = "生成回答",
                status = when {
                    state.isStreaming -> "生成中"
                    isClarifying || isCompareChat || hasGuideResults -> "完成"
                    else -> "待开始"
                },
                done = !state.isStreaming && (isClarifying || isCompareChat || hasGuideResults),
            )
            if (state.fallbackMessage != null && hasGuideResults) {
                Surface(color = BuyWiseTheme.colors.accentSoft, shape = RoundedCornerShape(12.dp)) {
                    Text(
                        state.fallbackMessage,
                        modifier = Modifier.padding(horizontal = 12.dp, vertical = 9.dp),
                        color = BuyWiseTheme.colors.ink,
                        style = MaterialTheme.typography.labelMedium,
                    )
                }
            }
            if (state.hasProvisionalResults && hasGuideResults) {
                Surface(color = BuyWiseTheme.colors.primarySoft, shape = RoundedCornerShape(12.dp)) {
                    Text(
                        "先返回候选，正在复核商品证据。",
                        modifier = Modifier.padding(horizontal = 12.dp, vertical = 9.dp),
                        color = BuyWiseTheme.colors.primary,
                        style = MaterialTheme.typography.labelMedium,
                    )
                }
            }
            if (!isCompareChat) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                        Text("导购偏好", color = BuyWiseTheme.colors.ink, fontWeight = FontWeight.Bold)
                        Text(
                            guidePreferenceSummaryText(state.appliedPreferences, state.ignoreSavedPreferences),
                            color = BuyWiseTheme.colors.muted,
                            style = MaterialTheme.typography.labelMedium,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                        )
                    }
                    Switch(checked = state.ignoreSavedPreferences, onCheckedChange = onIgnoreSavedPreferencesChange)
                }
            }
        }
    }
}
