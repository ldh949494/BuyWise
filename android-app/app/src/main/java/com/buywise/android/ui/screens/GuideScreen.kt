package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Switch
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.graphics.vector.ImageVector
import com.buywise.android.data.GuideState
import com.buywise.android.data.GuideResultStatus
import com.buywise.android.data.Product
import com.buywise.android.data.AppliedPreferences
import com.buywise.android.ui.BuyWiseDimens
import com.buywise.android.ui.BuyWiseIcons
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.components.BundlePlanCard
import com.buywise.android.ui.components.FloatingAssetBadge
import com.buywise.android.ui.components.FloatingGlassCard
import com.buywise.android.ui.components.FloatingGlassTone
import com.buywise.android.ui.components.ProductCard
import com.buywise.android.ui.components.ProvisionalProductCard
import com.buywise.android.ui.components.SectionTitle
import com.buywise.android.ui.components.TactileIconTile
import com.buywise.android.ui.components.TactileIconTone
import com.buywise.android.ui.displayPrice
import kotlinx.coroutines.launch

@Composable
fun GuideScreen(
    state: GuideState,
    onQueryChange: (String) -> Unit,
    onSubmit: () -> Unit,
    onOpenChat: () -> Unit,
    onNewConversation: () -> Unit,
    onOpenHistory: () -> Unit,
    onProductClick: (String) -> Unit,
    isInCompareBasket: (String) -> Boolean,
    onToggleCompare: (Product, String?) -> Unit,
    onIgnoreSavedPreferencesChange: (Boolean) -> Unit,
    onOpenGuidePreferences: () -> Unit,
) {
    val listState = rememberLazyListState()
    val coroutineScope = rememberCoroutineScope()
    val isClarifying = state.resultStatus == GuideResultStatus.Clarifying
    val hasResults = state.recommendations.isNotEmpty() || state.bundlePlans.isNotEmpty()
    val isShowingProvisionalProducts = state.isStreaming &&
        state.hasProvisionalResults &&
        state.bundlePlans.isEmpty() &&
        state.recommendations.isNotEmpty()
    val shouldShowDemandPanel = state.query.isNotBlank() &&
        (state.intentSummary.isNotBlank() || state.recommendations.isNotEmpty())
    val shouldShowResultsSection = !isClarifying

    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        state = listState,
        contentPadding = PaddingValues(18.dp),
        verticalArrangement = Arrangement.spacedBy(18.dp),
    ) {
        item { GuideDecisionHeader(onNewConversation = onNewConversation, onOpenHistory = onOpenHistory) }
        item { GuideInputPanel(state = state, onQueryChange = onQueryChange, onSubmit = onSubmit, onOpenChat = onOpenChat) }
        item {
            PreferenceUsagePanel(
                appliedPreferences = state.appliedPreferences,
                ignoreSavedPreferences = state.ignoreSavedPreferences,
                onIgnoreSavedPreferencesChange = onIgnoreSavedPreferencesChange,
                onOpenGuidePreferences = onOpenGuidePreferences,
            )
        }
        guideStreamItems(state)
        if (shouldShowDemandPanel) {
            item {
                DemandPanel(
                    query = state.query,
                    summary = state.intentSummary,
                    onModify = { coroutineScope.launch { listState.animateScrollToItem(1) } },
                )
            }
        }
        if (shouldShowResultsSection) {
            item {
                SectionTitle(
                    title = when {
                        state.bundlePlans.isNotEmpty() -> "组合方案"
                        isShowingProvisionalProducts -> "方案生成中"
                        else -> "首推与备选"
                    },
                    subtitle = if (isShowingProvisionalProducts) {
                        "先看看以下相关商品，完整推荐理由还在生成。"
                    } else {
                        "先看商品候选，再核对理由、风险和证据。"
                    },
                )
            }
            if (state.appliedPreferences.hasVisibleSummary) {
                item {
                    AppliedPreferenceSummary(
                        appliedPreferences = state.appliedPreferences,
                        ignoreSavedPreferences = state.ignoreSavedPreferences,
                        onIgnoreSavedPreferencesChange = onIgnoreSavedPreferencesChange,
                        onOpenGuidePreferences = onOpenGuidePreferences,
                    )
                }
            }
            if (!state.isStreaming && !hasResults) {
                item { RecommendationEmptyState(resultStatus = state.resultStatus) }
            }
            if (isShowingProvisionalProducts) {
                item { ResultQualityNotice(message = "方案生成中，先看看以下商品吧。") }
            }
            if (state.fallbackMessage != null && hasResults) {
                item { ResultQualityNotice(message = state.fallbackMessage) }
            }
            if (state.bundlePlans.isNotEmpty()) {
                itemsIndexed(state.bundlePlans) { index, plan ->
                    BundlePlanCard(plan = plan, featured = index == 1, onProductClick = onProductClick)
                }
            } else {
                itemsIndexed(state.recommendations) { index, recommendation ->
                    if (isShowingProvisionalProducts) {
                        ProvisionalProductCard(
                            product = recommendation.product,
                            onClick = { onProductClick(recommendation.product.id) },
                        )
                    } else {
                        Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                            if (index == 0) {
                                TopRecommendationStrip(
                                    product = recommendation.product,
                                    onClick = { onProductClick(recommendation.product.id) },
                                )
                                EvidenceConfidenceNotice(product = recommendation.product)
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
        }
    }
}

@Composable
private fun PreferenceUsagePanel(
    appliedPreferences: AppliedPreferences,
    ignoreSavedPreferences: Boolean,
    onIgnoreSavedPreferencesChange: (Boolean) -> Unit,
    onOpenGuidePreferences: () -> Unit,
) {
    FloatingGlassCard(tone = FloatingGlassTone.Neutral, radius = 14.dp, contentPadding = 14.dp) {
        Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text("导购偏好", color = BuyWiseTheme.colors.ink, fontWeight = FontWeight.Bold)
                    Text(
                        preferenceSummaryText(appliedPreferences, ignoreSavedPreferences),
                        color = BuyWiseTheme.colors.muted,
                        style = MaterialTheme.typography.bodyMedium,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis,
                    )
                }
                Switch(checked = ignoreSavedPreferences, onCheckedChange = onIgnoreSavedPreferencesChange)
            }
            RaisedGuideButton(
                label = "调整导购偏好",
                icon = BuyWiseIcons.Tune,
                primary = false,
                enabled = true,
                modifier = Modifier.fillMaxWidth(),
                onClick = onOpenGuidePreferences,
            )
        }
    }
}

@Composable
private fun AppliedPreferenceSummary(
    appliedPreferences: AppliedPreferences,
    ignoreSavedPreferences: Boolean,
    onIgnoreSavedPreferencesChange: (Boolean) -> Unit,
    onOpenGuidePreferences: () -> Unit,
) {
    PreferenceUsagePanel(appliedPreferences, ignoreSavedPreferences, onIgnoreSavedPreferencesChange, onOpenGuidePreferences)
}

private fun preferenceSummaryText(appliedPreferences: AppliedPreferences, ignoreSavedPreferences: Boolean): String {
    if (ignoreSavedPreferences || appliedPreferences.ignoredSavedPreferences) {
        return "本次未使用长期导购偏好"
    }
    val summary = appliedPreferences.summary.take(3)
    if (summary.isEmpty()) {
        return "本次会优先使用已保存的预算、排除项和呈现方式"
    }
    return "已按你的导购偏好：" + summary.joinToString("、")
}

@Composable
private fun GuideDecisionHeader(onNewConversation: () -> Unit, onOpenHistory: () -> Unit) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.weight(1f)) {
            Text("导购决策", style = MaterialTheme.typography.headlineMedium, color = BuyWiseTheme.colors.ink)
            Text(
                "先确认需求，再给出可核查的首推、备选和购买前注意。",
                color = BuyWiseTheme.colors.muted,
                style = MaterialTheme.typography.bodyMedium,
            )
        }
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            TactileIconTile(icon = BuyWiseIcons.History, contentDescription = "历史记录", size = 46.dp, iconSize = 22.dp, onClick = onOpenHistory)
            TactileIconTile(icon = BuyWiseIcons.NewChat, contentDescription = "新建对话", size = 46.dp, iconSize = 22.dp, tone = TactileIconTone.Primary, onClick = onNewConversation)
        }
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
        radius = 12.dp,
        elevated = false,
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
                        "说出品类或商品名即可开始，预算、用途和偏好可以继续补充。",
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
                    label = if (state.isStreaming) "生成中..." else "开始导购",
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
                    label = "继续追问",
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

@Composable
private fun TopRecommendationStrip(product: Product, onClick: () -> Unit) {
    FloatingGlassCard(
        tone = FloatingGlassTone.Success,
        radius = 12.dp,
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
                Text("先核对证据，再看是否符合你的核心需求", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.labelMedium)
            }
            Text(product.price.displayPrice(), color = BuyWiseTheme.colors.primary, style = MaterialTheme.typography.titleMedium)
        }
    }
}

@Composable
private fun EvidenceConfidenceNotice(product: Product) {
    val hasProductPage = product.productUrl?.isNotBlank() == true
    val hasSnapshot = product.price != null || product.stockStatus?.isNotBlank() == true
    val hasReview = product.reviewSummary?.isNotBlank() == true
    if (hasProductPage && hasSnapshot && hasReview) {
        return
    }
    FloatingGlassCard(
        tone = FloatingGlassTone.Warm,
        radius = 12.dp,
        elevated = false,
        contentPadding = 12.dp,
    ) {
        Text(
            "证据较少，建议打开商家页面确认价格、库存和评价后再决定。",
            color = BuyWiseTheme.colors.ink,
            style = MaterialTheme.typography.bodyMedium,
        )
    }
}

private fun androidx.compose.foundation.lazy.LazyListScope.guideStreamItems(state: GuideState) {
    if (state.isStreaming) {
        item { AnalysisProgressCard(title = "BuyWise 正在生成导购建议") }
    }
    if (state.resultStatus == GuideResultStatus.Clarifying) {
        item { ClarificationStateCard(message = state.clarificationMessage) }
    } else if (state.partialReply.isNotBlank()) {
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
