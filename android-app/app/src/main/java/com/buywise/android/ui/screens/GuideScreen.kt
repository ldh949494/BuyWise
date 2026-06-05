package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import com.buywise.android.data.GuideState
import com.buywise.android.data.Product
import com.buywise.android.ui.BuyWiseDimens
import com.buywise.android.ui.BuyWiseIcons
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.components.FloatingAssetBadge
import com.buywise.android.ui.components.FloatingGlassCard
import com.buywise.android.ui.components.FloatingGlassTone
import com.buywise.android.ui.components.ProductCard
import com.buywise.android.ui.components.SectionTitle
import com.buywise.android.ui.components.TactileIconTile
import com.buywise.android.ui.components.TactileIconTone
import com.buywise.android.ui.displayPrice

@Composable
fun GuideScreen(
    state: GuideState,
    onQueryChange: (String) -> Unit,
    onSubmit: () -> Unit,
    onOpenChat: () -> Unit,
    onProductClick: (String) -> Unit,
    isInCompareBasket: (String) -> Boolean,
    onToggleCompare: (Product, String?) -> Unit,
) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(18.dp),
        verticalArrangement = Arrangement.spacedBy(18.dp),
    ) {
        item { WorkbenchHeader() }
        item { GuideInputPanel(state = state, onQueryChange = onQueryChange, onSubmit = onSubmit, onOpenChat = onOpenChat) }
        guideStreamItems(state)
        item { DemandPanel(query = state.query, summary = state.intentSummary) }
        item {
            SectionTitle(
                title = "推荐结果",
                subtitle = "先看首推，再对比关键差异。",
            )
        }
        if (!state.isStreaming && state.recommendations.isEmpty()) {
            item { RecommendationEmptyState() }
        }
        itemsIndexed(state.recommendations) { index, recommendation ->
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                if (index == 0) {
                    TopRecommendationStrip(
                        product = recommendation.product,
                        onClick = { onProductClick(recommendation.product.id) },
                    )
                }
                ProductCard(
                    product = recommendation.product,
                    onClick = { onProductClick(recommendation.product.id) },
                    isInCompareBasket = isInCompareBasket(recommendation.product.id),
                    onToggleCompare = { onToggleCompare(recommendation.product, state.query) },
                    recommendationReason = recommendation.reason,
                    isFeatured = index == 0,
                )
            }
        }
    }
}

@Composable
private fun WorkbenchHeader() {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.weight(1f)) {
            Text("AI 导购工作台", style = MaterialTheme.typography.headlineMedium, color = BuyWiseTheme.colors.ink)
            Text(
                "先提取需求，再给出候选商品和可核查理由。",
                color = BuyWiseTheme.colors.muted,
                style = MaterialTheme.typography.bodyMedium,
            )
        }
        TactileIconTile(
            icon = BuyWiseIcons.Guide,
            contentDescription = null,
            size = 58.dp,
            iconSize = 28.dp,
            tone = TactileIconTone.Primary,
        )
    }
}

@Composable
private fun GuideInputPanel(
    state: GuideState,
    onQueryChange: (String) -> Unit,
    onSubmit: () -> Unit,
    onOpenChat: () -> Unit,
) {
    val haptic = LocalHapticFeedback.current
    FloatingGlassCard(
        tone = FloatingGlassTone.Neutral,
        radius = BuyWiseDimens.HeroRadius.dp,
        contentPadding = 18.dp,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
            FloatingGlassCard(
                tone = FloatingGlassTone.Primary,
                radius = 16.dp,
                contentPadding = 14.dp,
            ) {
                Row(
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    FloatingAssetBadge(
                        icon = BuyWiseIcons.Guide,
                        contentDescription = null,
                        size = 42.dp,
                        iconSize = 21.dp,
                        tone = TactileIconTone.Primary,
                    )
                    Text(
                        "描述预算、用途和偏好，BuyWise 会给出候选商品和理由。",
                        modifier = Modifier.weight(1f),
                        color = BuyWiseTheme.colors.primary,
                        fontWeight = FontWeight.Bold,
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
            }
            Text("购物需求", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
            DemandTemplateRow(
                onTemplateClick = { template ->
                    haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                    onQueryChange(template)
                },
            )
            FloatingGlassCard(
                tone = FloatingGlassTone.Neutral,
                radius = 14.dp,
                elevated = false,
                contentPadding = 0.dp,
            ) {
                OutlinedTextField(
                    value = state.query,
                    onValueChange = onQueryChange,
                    modifier = Modifier.fillMaxWidth(),
                    minLines = 4,
                    placeholder = { Text("宿舍写代码用，预算300以内，想要低噪音机械键盘，最好便于收纳。") },
                )
            }
            Text(
                if (state.query.isBlank()) "选择一个模板，或直接输入你的需求。" else "已记录 ${state.query.length} 字需求，可继续补充。",
                color = BuyWiseTheme.colors.muted,
                style = MaterialTheme.typography.labelMedium,
            )
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {
                RaisedGuideButton(
                    label = if (state.isStreaming) "生成中..." else "生成推荐",
                    icon = BuyWiseIcons.Guide,
                    primary = true,
                    enabled = !state.isStreaming && state.query.isNotBlank(),
                    modifier = Modifier.weight(1f),
                    onClick = {
                        haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                        onSubmit()
                    },
                )
                RaisedGuideButton(
                    label = "进入对话导购",
                    icon = BuyWiseIcons.Assistant,
                    primary = false,
                    enabled = true,
                    modifier = Modifier.weight(1f),
                    onClick = {
                        haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                        onOpenChat()
                    },
                )
            }
        }
    }
}

@Composable
private fun DemandTemplateRow(onTemplateClick: (String) -> Unit) {
    val templates = listOf(
        DemandTemplate("宿舍低噪键盘", "宿舍写代码用，预算300以内，想要低噪音机械键盘，最好便于收纳。"),
        DemandTemplate("通勤降噪耳机", "通勤和办公室都能用，预算500以内，想要降噪好、佩戴舒服的耳机。"),
        DemandTemplate("办公显示器", "日常办公和轻度修图，预算1000以内，想要护眼、接口方便的显示器。"),
    )
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        templates.forEach { template ->
            FloatingGlassCard(
                tone = FloatingGlassTone.Neutral,
                radius = 12.dp,
                fillMaxWidth = false,
                contentPadding = 0.dp,
                onClick = { onTemplateClick(template.query) },
            ) {
                Text(
                    template.label,
                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 10.dp),
                    color = BuyWiseTheme.colors.ink,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                )
            }
        }
    }
}

@Composable
private fun RaisedGuideButton(
    label: String,
    icon: ImageVector,
    primary: Boolean,
    enabled: Boolean,
    modifier: Modifier = Modifier,
    onClick: () -> Unit,
) {
    val tone = when {
        primary && enabled -> FloatingGlassTone.SolidPrimary
        primary -> FloatingGlassTone.Primary
        else -> FloatingGlassTone.Neutral
    }
    val foreground = when {
        primary && enabled -> Color.White
        enabled -> BuyWiseTheme.colors.ink
        else -> BuyWiseTheme.colors.muted
    }
    FloatingGlassCard(
        modifier = modifier,
        tone = tone,
        radius = 999.dp,
        contentPadding = 0.dp,
        onClick = if (enabled) onClick else null,
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 18.dp, vertical = 13.dp),
            horizontalArrangement = Arrangement.Center,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(icon, contentDescription = null, tint = foreground)
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                label,
                color = foreground,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
            )
        }
    }
}

private data class DemandTemplate(val label: String, val query: String)

@Composable
private fun RecommendationEmptyState() {
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
                Text("还没有推荐结果", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
                Text(
                    "输入预算、用途和偏好后，这里会展示候选商品、推荐理由和冲突点。",
                    color = BuyWiseTheme.colors.muted,
                    style = MaterialTheme.typography.bodyMedium,
                )
            }
        }
    }
}

@Composable
private fun TopRecommendationStrip(product: Product, onClick: () -> Unit) {
    FloatingGlassCard(
        tone = FloatingGlassTone.Success,
        radius = 16.dp,
        contentPadding = 14.dp,
        onClick = onClick,
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text("优先推荐", color = BuyWiseTheme.colors.secondary, fontWeight = FontWeight.Bold)
                Text(product.name, color = BuyWiseTheme.colors.ink, maxLines = 1, overflow = TextOverflow.Ellipsis)
                Text("理由清楚，适合先看", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.labelMedium)
            }
            Text(product.price.displayPrice(), color = BuyWiseTheme.colors.primary, style = MaterialTheme.typography.titleMedium)
        }
    }
}

private fun androidx.compose.foundation.lazy.LazyListScope.guideStreamItems(state: GuideState) {
    if (state.isStreaming) {
        item { LinearProgressIndicator(modifier = Modifier.fillMaxWidth()) }
    }
    if (state.partialReply.isNotBlank()) {
        item {
            InfoPanel(
                icon = { Icon(BuyWiseIcons.Guide, contentDescription = null) },
                title = "AI 推荐理由",
                body = state.partialReply,
            )
        }
    }
    if (state.errorMessage != null) {
        item {
            ErrorPanel(message = state.errorMessage)
        }
    }
}
