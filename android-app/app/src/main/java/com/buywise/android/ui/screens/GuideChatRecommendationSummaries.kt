package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.buywise.android.data.Recommendation
import com.buywise.android.data.cleanMarkdownText
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.components.EvidenceTag
import com.buywise.android.ui.components.EvidenceTone
import com.buywise.android.ui.displayPrice
import com.buywise.android.ui.displayRating

@Composable
internal fun ChatProvisionalSummary(text: String) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        EvidenceTag("方案生成中", tone = EvidenceTone.Info)
        Text(
            "先看看以下相关商品，完整推荐理由还在生成。",
            color = BuyWiseTheme.colors.ink,
            style = MaterialTheme.typography.bodyMedium,
        )
        if (text.isNotBlank() && text != "正在整理回复...") {
            Text(
                text,
                color = BuyWiseTheme.colors.muted,
                style = MaterialTheme.typography.bodyMedium,
                maxLines = 3,
                overflow = TextOverflow.Ellipsis,
            )
        }
    }
}

@Composable
internal fun ChatDecisionSummary(
    text: String,
    recommendations: List<Recommendation>,
    modifier: Modifier = Modifier,
) {
    var expanded by remember { mutableStateOf(false) }
    val topRecommendation = recommendations.first()
    val product = topRecommendation.product
    val alternatives = recommendations.drop(1).take(2)

    Column(modifier = modifier, verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
            EvidenceTag("首推", tone = EvidenceTone.Success)
            Text(
                product.price.displayPrice(),
                color = BuyWiseTheme.colors.primary,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
            )
            Text(
                "评分 ${product.rating.displayRating()}",
                color = BuyWiseTheme.colors.muted,
                style = MaterialTheme.typography.labelMedium,
            )
        }
        Text(
            product.name,
            color = BuyWiseTheme.colors.ink,
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold,
            maxLines = 2,
            overflow = TextOverflow.Ellipsis,
        )
        ChatReasonBlock(
            title = "为什么先看它",
            lines = listOf(topRecommendation.reason, product.headline)
                .map { it.cleanMarkdownText() }
                .filter { it.isNotBlank() }
                .distinct()
                .take(2),
        )
        if (alternatives.isNotEmpty()) {
            Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text("备选", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.labelMedium)
                alternatives.forEach { recommendation ->
                    AlternativeProductLine(recommendation = recommendation)
                }
            }
        }
        if (text.isNotBlank()) {
            Surface(color = BuyWiseTheme.colors.panelAlt, shape = RoundedCornerShape(14.dp)) {
                Column(modifier = Modifier.padding(horizontal = 12.dp, vertical = 10.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text("补充说明", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.labelMedium)
                    Text(
                        text,
                        color = BuyWiseTheme.colors.ink,
                        style = MaterialTheme.typography.bodyMedium,
                        maxLines = if (expanded) Int.MAX_VALUE else 3,
                        overflow = TextOverflow.Ellipsis,
                    )
                    TextButton(onClick = { expanded = !expanded }) {
                        Text(if (expanded) "收起说明" else "展开完整说明")
                    }
                }
            }
        }
    }
}

@Composable
private fun ChatReasonBlock(title: String, lines: List<String>) {
    if (lines.isEmpty()) return
    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Text(title, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.labelMedium)
        lines.forEach { line ->
            Text(
                "- $line",
                color = BuyWiseTheme.colors.ink,
                style = MaterialTheme.typography.bodyMedium,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
            )
        }
    }
}

@Composable
private fun AlternativeProductLine(recommendation: Recommendation) {
    val product = recommendation.product
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            product.name,
            modifier = Modifier.weight(1f),
            color = BuyWiseTheme.colors.ink,
            style = MaterialTheme.typography.bodyMedium,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
        )
        Text(
            product.price.displayPrice(),
            color = BuyWiseTheme.colors.primary,
            style = MaterialTheme.typography.labelMedium,
            fontWeight = FontWeight.Bold,
        )
    }
}
