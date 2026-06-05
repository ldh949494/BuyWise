package com.buywise.android.ui.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.TextButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.buywise.android.data.BundlePlan
import com.buywise.android.data.BundlePlanItem
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.displayPrice

@Composable
fun BundlePlanCard(
    plan: BundlePlan,
    featured: Boolean,
    onProductClick: (String) -> Unit,
) {
    val tone = if (featured) FloatingGlassTone.Success else FloatingGlassTone.Neutral
    FloatingGlassCard(tone = tone, radius = 18.dp, contentPadding = 16.dp) {
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top,
            ) {
                Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text(plan.title, color = BuyWiseTheme.colors.ink, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                    Text(
                        plan.summary ?: plan.scenarioFit ?: "已按预算档整理桌面装备组合。",
                        color = BuyWiseTheme.colors.muted,
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
                Column(horizontalAlignment = Alignment.End, verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text(plan.totalPrice.displayPrice(), color = BuyWiseTheme.colors.primary, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                    Text(plan.budgetLabel(), color = plan.budgetStatusColor(), style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.Bold)
                }
            }
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                BundlePill("完整度 ${plan.completeness.includedRequired}/${plan.completeness.expectedRequired}")
                if (plan.completeness.optionalIncluded > 0) {
                    BundlePill("可选 ${plan.completeness.optionalIncluded}")
                }
                val riskCount = plan.compatibilityChecks.count { it.status != "pass" }
                BundlePill(if (riskCount > 0) "风险 $riskCount 项" else "搭配通过")
            }
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                plan.items.take(5).forEach { item ->
                    BundlePlanItemRow(item = item, onClick = { onProductClick(item.product.id) })
                }
                if (plan.items.size > 5) {
                    Text(
                        "另有 ${plan.items.size - 5} 个补充项，可在方案详情中查看。",
                        color = BuyWiseTheme.colors.muted,
                        style = MaterialTheme.typography.labelMedium,
                    )
                }
            }
            val note = plan.tradeoffs.firstOrNull() ?: plan.compareHighlights.firstOrNull()
            if (note != null) {
                Text(note, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
            }
        }
    }
}

@Composable
fun ChatBundleSummary(
    text: String,
    bundlePlans: List<BundlePlan>,
    modifier: Modifier = Modifier,
) {
    val balanced = bundlePlans.getOrNull(1) ?: bundlePlans.first()
    Column(modifier = modifier, verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
            EvidenceTag("方案", tone = EvidenceTone.Success)
            Text(
                "${bundlePlans.size} 套预算档",
                color = BuyWiseTheme.colors.primary,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
            )
        }
        Text(
            balanced.title,
            color = BuyWiseTheme.colors.ink,
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold,
            maxLines = 2,
            overflow = TextOverflow.Ellipsis,
        )
        Text(
            "${balanced.totalPrice.displayPrice()} · 完整度 ${balanced.completeness.includedRequired}/${balanced.completeness.expectedRequired}",
            color = BuyWiseTheme.colors.primary,
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = FontWeight.Bold,
        )
        balanced.tradeoffs.firstOrNull()?.let {
            Text(it, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
        }
        if (text.isNotBlank()) {
            Text(text, color = BuyWiseTheme.colors.ink, style = MaterialTheme.typography.bodyMedium, maxLines = 3, overflow = TextOverflow.Ellipsis)
        }
    }
}

@Composable
fun ChatBundlePlanCard(plan: BundlePlan, onProductClick: (String) -> Unit) {
    FloatingGlassCard(
        tone = FloatingGlassTone.Neutral,
        radius = 16.dp,
        contentPadding = 14.dp,
        fillMaxWidth = false,
    ) {
        Column(modifier = Modifier.fillMaxWidth(0.78f), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                EvidenceTag(plan.budgetLabel(), tone = if (plan.budgetStatus == "within_budget") EvidenceTone.Success else EvidenceTone.Warning)
                Text(plan.totalPrice.displayPrice(), color = BuyWiseTheme.colors.primary, fontWeight = FontWeight.Bold)
            }
            Text(
                plan.title,
                color = BuyWiseTheme.colors.ink,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
            plan.items.take(3).forEach { item ->
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                    Text(item.category, color = BuyWiseTheme.colors.primary, style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.Bold)
                    Text(
                        item.product.name,
                        modifier = Modifier.weight(1f),
                        color = BuyWiseTheme.colors.ink,
                        style = MaterialTheme.typography.labelMedium,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                    Text(item.product.price.displayPrice(), color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.labelMedium)
                }
            }
            plan.items.firstOrNull()?.let { item ->
                TextButton(onClick = { onProductClick(item.product.id) }) {
                    Text("查看首个商品")
                }
            }
        }
    }
}

@Composable
private fun BundlePlanItemRow(item: BundlePlanItem, onClick: () -> Unit) {
    FloatingGlassCard(
        tone = FloatingGlassTone.Neutral,
        radius = 12.dp,
        elevated = false,
        contentPadding = 12.dp,
        onClick = onClick,
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(10.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                Text(item.category, color = BuyWiseTheme.colors.primary, style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.Bold)
                Text(
                    item.product.name,
                    color = BuyWiseTheme.colors.ink,
                    style = MaterialTheme.typography.bodyMedium,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
                item.role?.let {
                    Text(it, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.labelMedium)
                }
            }
            Text(item.product.price.displayPrice(), color = BuyWiseTheme.colors.ink, fontWeight = FontWeight.Bold)
        }
    }
}

@Composable
private fun BundlePill(label: String) {
    FloatingGlassCard(tone = FloatingGlassTone.Primary, radius = 999.dp, fillMaxWidth = false, contentPadding = 0.dp) {
        Text(
            label,
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
            color = BuyWiseTheme.colors.primary,
            style = MaterialTheme.typography.labelMedium,
            fontWeight = FontWeight.Bold,
        )
    }
}

private fun BundlePlan.budgetLabel(): String = when (budgetStatus) {
    "within_budget" -> "预算内"
    "slightly_over_budget" -> "小幅超预算"
    "over_budget" -> "超预算"
    else -> "预算待确认"
}

@Composable
private fun BundlePlan.budgetStatusColor(): Color = when (budgetStatus) {
    "within_budget" -> BuyWiseTheme.colors.secondary
    "slightly_over_budget", "over_budget" -> BuyWiseTheme.colors.accent
    else -> BuyWiseTheme.colors.muted
}
