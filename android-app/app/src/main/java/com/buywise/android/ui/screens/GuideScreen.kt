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
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.AutoAwesome
import androidx.compose.material.icons.outlined.ShoppingBag
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.buywise.android.data.GuideState
import com.buywise.android.data.Product
import com.buywise.android.ui.BuyWiseDimens
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.components.EvidenceTag
import com.buywise.android.ui.components.EvidenceTone
import com.buywise.android.ui.components.FloatingGlassCard
import com.buywise.android.ui.components.FloatingGlassTone
import com.buywise.android.ui.components.ProductCard
import com.buywise.android.ui.components.SectionTitle
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
                subtitle = "按预算、场景、库存和已购反馈信号排序",
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
        Surface(
            color = BuyWiseTheme.colors.panel,
            shape = RoundedCornerShape(16.dp),
            shadowElevation = 0.dp,
            modifier = Modifier.size(58.dp),
        ) {
            Icon(
                Icons.Outlined.AutoAwesome,
                contentDescription = null,
                tint = BuyWiseTheme.colors.primary,
                modifier = Modifier.padding(15.dp),
            )
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
    FloatingGlassCard(
        tone = FloatingGlassTone.Neutral,
        radius = BuyWiseDimens.HeroRadius.dp,
        contentPadding = 18.dp,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
            Surface(color = BuyWiseTheme.colors.primarySoft, shape = RoundedCornerShape(16.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 14.dp),
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Icon(Icons.Outlined.AutoAwesome, contentDescription = null, tint = BuyWiseTheme.colors.primary)
                    Text(
                        "一句话描述需求，BuyWise 会提取预算、场景和偏好，再推荐商品。",
                        color = BuyWiseTheme.colors.primary,
                        fontWeight = FontWeight.Bold,
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
            }
            Text("购物需求", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
            OutlinedTextField(
                value = state.query,
                onValueChange = onQueryChange,
                modifier = Modifier.fillMaxWidth(),
                minLines = 4,
                placeholder = { Text("宿舍写代码用，预算300以内，想要低噪音机械键盘，最好便于收纳。") },
            )
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {
                Button(
                    onClick = onSubmit,
                    modifier = Modifier.weight(1f),
                    enabled = !state.isStreaming,
                ) {
                    Icon(Icons.Outlined.AutoAwesome, contentDescription = null)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(if (state.isStreaming) "生成中..." else "生成推荐")
                }
                androidx.compose.material3.OutlinedButton(
                    onClick = onOpenChat,
                    modifier = Modifier.weight(1f),
                ) {
                    Text("进入对话导购")
                }
            }
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                EvidenceTag("预算 500 内")
                EvidenceTag("宿舍场景", tone = EvidenceTone.Success)
                EvidenceTag("低噪音")
                EvidenceTag("图片/语音可带入", tone = EvidenceTone.Warning)
            }
        }
    }
}

@Composable
private fun RecommendationEmptyState() {
    FloatingGlassCard(tone = FloatingGlassTone.Neutral, contentPadding = 20.dp) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(14.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Surface(color = BuyWiseTheme.colors.primarySoft, shape = RoundedCornerShape(14.dp), modifier = Modifier.size(52.dp)) {
                Icon(Icons.Outlined.ShoppingBag, contentDescription = null, tint = BuyWiseTheme.colors.primary, modifier = Modifier.padding(14.dp))
            }
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
                Text("预算、场景和已购反馈综合最稳", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.labelMedium)
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
                icon = { Icon(Icons.Outlined.AutoAwesome, contentDescription = null) },
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
