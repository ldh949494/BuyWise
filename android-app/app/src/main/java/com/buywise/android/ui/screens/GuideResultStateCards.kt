package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.buywise.android.data.GuideResultStatus
import com.buywise.android.ui.BuyWiseIcons
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.components.FloatingGlassCard
import com.buywise.android.ui.components.FloatingGlassTone
import com.buywise.android.ui.components.TactileIconTile
import com.buywise.android.ui.components.TactileIconTone

@Composable
internal fun RecommendationEmptyState(resultStatus: GuideResultStatus) {
    FloatingGlassCard(tone = FloatingGlassTone.Neutral, contentPadding = 20.dp) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(14.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            TactileIconTile(
                icon = BuyWiseIcons.Shopping,
                contentDescription = null,
                tone = TactileIconTone.Primary,
            )
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text(
                    if (resultStatus == GuideResultStatus.Empty) "没有找到可推荐候选" else "还没有推荐结果",
                    style = MaterialTheme.typography.titleMedium,
                    color = BuyWiseTheme.colors.ink,
                )
                Text(
                    if (resultStatus == GuideResultStatus.Empty) {
                        "当前目录没有找到可推荐候选。换个品类或商品名再试。"
                    } else {
                        "输入品类、商品名或需求后，这里会先展示候选商品，再补齐推荐理由、风险和证据。"
                    },
                    color = BuyWiseTheme.colors.muted,
                    style = MaterialTheme.typography.bodyMedium,
                )
            }
        }
    }
}

@Composable
internal fun ClarificationStateCard(message: String?) {
    FloatingGlassCard(
        tone = FloatingGlassTone.Primary,
        radius = 12.dp,
        elevated = false,
        contentPadding = 16.dp,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text("补充商品目标", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.primary)
            Text(
                message ?: "告诉我想看哪类商品或商品名即可继续。",
                color = BuyWiseTheme.colors.ink,
                style = MaterialTheme.typography.bodyMedium,
            )
        }
    }
}

@Composable
internal fun ResultQualityNotice(message: String) {
    FloatingGlassCard(
        tone = FloatingGlassTone.Warm,
        radius = 12.dp,
        elevated = false,
        contentPadding = 12.dp,
    ) {
        Text(
            message,
            color = BuyWiseTheme.colors.ink,
            style = MaterialTheme.typography.bodyMedium,
        )
    }
}
