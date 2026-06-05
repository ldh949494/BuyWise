package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.CompareArrows
import androidx.compose.material.icons.outlined.CameraAlt
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.Home
import androidx.compose.material.icons.outlined.Inventory2
import androidx.compose.material.icons.outlined.Refresh
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.buywise.android.data.CompareRow
import com.buywise.android.data.CompareState
import com.buywise.android.data.Product
import com.buywise.android.data.VisionState
import com.buywise.android.ui.BuyWiseDimens
import com.buywise.android.ui.BuyWiseIcons
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.displayPrice
import com.buywise.android.ui.displayRating
import com.buywise.android.ui.shortName
import com.buywise.android.ui.components.AdvicePanel
import com.buywise.android.ui.components.CategoryShortcut
import com.buywise.android.ui.components.EvidenceTag
import com.buywise.android.ui.components.EvidenceTone
import com.buywise.android.ui.components.ProductCard
import com.buywise.android.ui.components.ProductImagePreview
import com.buywise.android.ui.components.FloatingGlassCard
import com.buywise.android.ui.components.FloatingGlassTone
import com.buywise.android.ui.components.ScoreBadge
import com.buywise.android.ui.components.ShowcaseProductCard
import com.buywise.android.ui.components.ShowcaseTopBar
import com.buywise.android.ui.components.TactileIconTone

@Composable
fun CompareScreen(
    state: CompareState,
    onProductClick: (String) -> Unit,
    onRefresh: () -> Unit,
    onOpenHome: () -> Unit,
    onOpenGuide: () -> Unit,
) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(18.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        item {
            ShowcaseTopBar(
                title = "商品对比",
                onBack = null,
                leadingIcon = BuyWiseIcons.Compare,
                actionIcon = Icons.Outlined.Refresh,
                actionDescription = "刷新对比",
                onAction = onRefresh,
            )
        }
        if (state.isLoading) {
            item { LinearProgressIndicator(modifier = Modifier.fillMaxWidth()) }
        }
        state.errorMessage?.let { message ->
            item { ErrorPanel(message = message, actionLabel = "刷新", onAction = onRefresh) }
        }
        if (state.products.isEmpty()) {
            if (!state.isLoading && state.errorMessage == null) {
                item {
                    CompareEmptyStateCard(
                        onOpenHome = onOpenHome,
                        onOpenGuide = onOpenGuide,
                    )
                }
            }
        } else {
            item { Text("${state.products.size} 个商品", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink, fontWeight = FontWeight.Bold) }
            item { CompareScoreStrip(products = state.products, onProductClick = onProductClick) }
            item { CompareDecisionCard(state = state) }
            item { CompareTable(rows = state.rows, products = state.products) }
            item { CompareProsCons(products = state.products) }
            item {
                AdvicePanel(
                    title = state.products.firstOrNull { it.id == state.winnerId }?.let { "优先推荐：${it.shortName()}" } ?: "优先推荐",
                    body = state.summary ?: "综合价格、评分和当前购物需求，优先看整体价值更稳的候选。",
                )
            }
        }
    }
}

@Composable
private fun CompareEmptyStateCard(
    onOpenHome: () -> Unit,
    onOpenGuide: () -> Unit,
) {
    FloatingGlassCard(
        tone = FloatingGlassTone.Neutral,
        radius = BuyWiseDimens.CardRadius.dp,
        contentPadding = 18.dp,
    ) {
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
            com.buywise.android.ui.components.FloatingAssetBadge(
                icon = BuyWiseIcons.Compare,
                contentDescription = null,
                tone = TactileIconTone.Primary,
                size = 52.dp,
                iconSize = 26.dp,
            )
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(5.dp)) {
                Text("对比篮为空", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink, fontWeight = FontWeight.Bold)
                Text("先添加至少 2 个商品，再查看价格、评分和需求适配差异。", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
            }
        }
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 16.dp),
            horizontalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Button(
                onClick = onOpenHome,
                modifier = Modifier.weight(1f),
                colors = ButtonDefaults.buttonColors(
                    containerColor = BuyWiseTheme.colors.primary,
                    contentColor = BuyWiseTheme.colors.panel,
                ),
            ) {
                Icon(Icons.Outlined.Home, contentDescription = null, modifier = Modifier.size(18.dp))
                Spacer(Modifier.width(6.dp))
                Text("去首页选")
            }
            OutlinedButton(
                onClick = onOpenGuide,
                modifier = Modifier.weight(1f),
            ) {
                Icon(BuyWiseIcons.Guide, contentDescription = null, modifier = Modifier.size(18.dp))
                Spacer(Modifier.width(6.dp))
                Text("找导购")
            }
        }
    }
}

@Composable
fun VisionScreen(
    state: VisionState,
    onTakePhoto: () -> Unit,
    onPickImage: () -> Unit,
    onRunVisionDemo: () -> Unit,
    onRunSpeechDemo: () -> Unit,
    onUseQuery: () -> Unit,
    onProductClick: (String) -> Unit,
    isInCompareBasket: (String) -> Boolean,
    onToggleCompare: (Product) -> Unit,
) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(18.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item {
            ShowcaseTopBar(
                title = "图片搜索",
                onBack = null,
                leadingIcon = BuyWiseIcons.Vision,
                actionIcon = BuyWiseIcons.Guide,
                actionDescription = "历史识别",
                onAction = onRunVisionDemo,
            )
        }
        item {
            UploadPanel(
                isLoading = state.isLoading,
                hasQuery = !state.recognizedQuery.isNullOrBlank(),
                selectedImageName = state.selectedImageName,
                onTakePhoto = onTakePhoto,
                onPickImage = onPickImage,
                onRunVisionDemo = onRunVisionDemo,
                onRunSpeechDemo = onRunSpeechDemo,
                onUseQuery = onUseQuery,
            )
        }
        if (state.isLoading) {
            item { LinearProgressIndicator(modifier = Modifier.fillMaxWidth()) }
        }
        state.errorMessage?.let { message ->
            item { ErrorPanel(message = message) }
        }
        item {
            VisionResultCard(
                state = state,
                onUseQuery = onUseQuery,
            )
        }
        if (state.speechText != null) {
            item {
                InfoPanel(
                    icon = { Icon(Icons.Outlined.CameraAlt, contentDescription = null) },
                    title = "语音识别结果",
                    body = state.speechText,
                )
            }
        }
        item { Text("相似商品", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink, fontWeight = FontWeight.Bold) }
        if (state.result.similarProducts.isEmpty()) {
            item { Text("识别图片后，会展示同类候选商品。", color = BuyWiseTheme.colors.muted) }
        }
        items(state.result.similarProducts) { product ->
            SimilarPickRow(
                product = product,
                isInCompareBasket = isInCompareBasket(product.id),
                onProductClick = { onProductClick(product.id) },
                onToggleCompare = { onToggleCompare(product) },
            )
        }
    }
}

@Composable
private fun CompareScoreStrip(products: List<Product>, onProductClick: (String) -> Unit) {
    LazyRow(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
        items(products.take(4)) { product ->
            ShowcaseProductCard(
                product = product,
                onClick = { onProductClick(product.id) },
                modifier = Modifier.width(124.dp),
                selected = product == products.firstOrNull(),
                score = product.recommendationScore?.toInt() ?: product.rating?.times(18)?.toInt()?.coerceIn(70, 92),
                showFavorite = false,
            )
        }
    }
}

@Composable
private fun CompareProsCons(products: List<Product>) {
    if (products.isEmpty()) return
    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        FloatingGlassCard(
            modifier = Modifier.weight(1f),
            tone = FloatingGlassTone.Success,
            radius = 14.dp,
            contentPadding = 12.dp,
        ) {
            Text("优点", color = BuyWiseTheme.colors.secondary, fontWeight = FontWeight.Bold)
            products.first().advantages.take(4).ifEmpty { listOf("价格稳定", "评分可靠") }.forEach {
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp), verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Outlined.CheckCircle, contentDescription = null, tint = BuyWiseTheme.colors.secondary, modifier = Modifier.size(14.dp))
                    Text(it, color = BuyWiseTheme.colors.ink, style = MaterialTheme.typography.labelMedium, maxLines = 2, overflow = TextOverflow.Ellipsis)
                }
            }
        }
        FloatingGlassCard(
            modifier = Modifier.weight(1f),
            tone = FloatingGlassTone.Warm,
            radius = 14.dp,
            contentPadding = 12.dp,
        ) {
            Text("注意", color = BuyWiseTheme.colors.danger, fontWeight = FontWeight.Bold)
            products.first().cautions.take(4).ifEmpty { listOf("确认尺寸", "查看售后") }.forEach {
                Text("- $it", color = BuyWiseTheme.colors.ink, style = MaterialTheme.typography.labelMedium, maxLines = 2, overflow = TextOverflow.Ellipsis)
            }
        }
    }
}

@Composable
private fun CompareCandidateStrip(products: List<Product>, onProductClick: (String) -> Unit) {
    LazyRow(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        items(products) { product ->
            FloatingGlassCard(
                modifier = Modifier.width(190.dp),
                tone = FloatingGlassTone.Neutral,
                radius = 16.dp,
                fillMaxWidth = false,
                contentPadding = 10.dp,
                onClick = { onProductClick(product.id) },
            ) {
                Row(
                    horizontalArrangement = Arrangement.spacedBy(10.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    ProductImagePreview(product = product, modifier = Modifier.size(54.dp))
                    Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Text(
                            product.shortName(),
                            color = BuyWiseTheme.colors.ink,
                            fontWeight = FontWeight.Bold,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                        )
                        Text(product.price.displayPrice(), color = BuyWiseTheme.colors.primary, fontWeight = FontWeight.Bold)
                    }
                }
            }
        }
    }
}

@Composable
private fun VisionResultCard(state: VisionState, onUseQuery: () -> Unit) {
    FloatingGlassCard(
        tone = FloatingGlassTone.Neutral,
        radius = 16.dp,
        contentPadding = 14.dp,
    ) {
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
            ProductImagePreview(
                product = state.result.similarProducts.firstOrNull()
                    ?: Product("0", state.result.title, null, null, null, null, null, "", emptyList(), emptyList(), emptyList()),
                modifier = Modifier.size(width = 92.dp, height = 76.dp),
            )
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(7.dp)) {
                Text("识别结果", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
                Text("品类", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.labelMedium)
                Text(
                    state.result.title.takeIf { it.isNotBlank() } ?: "机械键盘",
                    color = BuyWiseTheme.colors.ink,
                    fontWeight = FontWeight.Bold,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp), verticalAlignment = Alignment.CenterVertically) {
                    EvidenceTag("${state.result.confidence}% 匹配", tone = EvidenceTone.Success)
                    EvidenceTag("RGB 灯效", tone = EvidenceTone.Info)
                }
                VisionResultActionButton(
                    enabled = !state.recognizedQuery.isNullOrBlank(),
                    onClick = onUseQuery,
                )
            }
            ScoreBadge(state.result.confidence.coerceIn(0, 99), size = 48.dp)
        }
    }
}

@Composable
private fun VisionResultActionButton(enabled: Boolean, onClick: () -> Unit) {
    val foreground = if (enabled) BuyWiseTheme.colors.ink else BuyWiseTheme.colors.muted
    FloatingGlassCard(
        tone = FloatingGlassTone.Neutral,
        radius = 999.dp,
        fillMaxWidth = false,
        contentPadding = 0.dp,
        elevated = true,
        onClick = if (enabled) onClick else null,
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 10.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(BuyWiseIcons.Search, contentDescription = null, tint = foreground, modifier = Modifier.size(18.dp))
            Text(
                "查找此类商品",
                color = foreground,
                style = MaterialTheme.typography.labelMedium,
                fontWeight = FontWeight.Bold,
            )
        }
    }
}

@Composable
private fun SimilarPickRow(
    product: Product,
    isInCompareBasket: Boolean,
    onProductClick: () -> Unit,
    onToggleCompare: () -> Unit,
) {
    FloatingGlassCard(
        tone = if (isInCompareBasket) FloatingGlassTone.Primary else FloatingGlassTone.Neutral,
        radius = 14.dp,
        contentPadding = 10.dp,
        onClick = onProductClick,
    ) {
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
            ProductImagePreview(product = product, modifier = Modifier.size(width = 76.dp, height = 54.dp))
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text(product.shortName(), color = BuyWiseTheme.colors.ink, fontWeight = FontWeight.Bold, maxLines = 1, overflow = TextOverflow.Ellipsis)
                Text(product.price.displayPrice(), color = BuyWiseTheme.colors.ink, style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.Bold)
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    product.tags.take(3).forEach { EvidenceTag(it, tone = EvidenceTone.Info) }
                }
            }
            CategoryShortcut(
                label = "",
                icon = BuyWiseIcons.Compare,
                tone = if (isInCompareBasket) TactileIconTone.SolidPrimary else TactileIconTone.Neutral,
                onClick = onToggleCompare,
            )
        }
    }
}
