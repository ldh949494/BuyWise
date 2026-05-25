package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.CompareArrows
import androidx.compose.material.icons.outlined.CameraAlt
import androidx.compose.material.icons.outlined.ImageSearch
import androidx.compose.material.icons.outlined.Inventory2
import androidx.compose.material.icons.outlined.EmojiEvents
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.buywise.android.data.CompareRow
import com.buywise.android.data.CompareState
import com.buywise.android.data.Product
import com.buywise.android.data.VisionState
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.components.ProductCard
import com.buywise.android.ui.components.SectionTitle

@Composable
fun CompareScreen(state: CompareState, onProductClick: (String) -> Unit) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(18.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item { SectionTitle("商品对比", "对已选商品进行价格、评分、优点和注意事项分析。") }
        if (state.isLoading) {
            item { LinearProgressIndicator(modifier = Modifier.fillMaxWidth()) }
        }
        state.errorMessage?.let { message ->
            item { ErrorPanel(message = message) }
        }
        item { CompareDecisionCard(state = state) }
        item { CompareTable(rows = state.rows, products = state.products) }
        item { SectionTitle("候选商品", "点击商品查看后端详情。") }
        if (!state.isLoading && state.products.isEmpty()) {
            item { Text("暂无可对比商品。", color = BuyWiseTheme.colors.muted) }
        }
        items(state.products) { product ->
            ProductCard(product = product, onClick = { onProductClick(product.id) })
        }
    }
}

@Composable
fun VisionScreen(
    state: VisionState,
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
        item { SectionTitle("多模态联调", "使用固定演示资源调用后端上传、识图和语音接口。") }
        item {
            UploadPanel(
                isLoading = state.isLoading,
                hasQuery = !state.recognizedQuery.isNullOrBlank(),
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
            InfoPanel(
                icon = { Icon(Icons.Outlined.Inventory2, contentDescription = null) },
                title = state.result.title,
                body = "${state.result.labels.joinToString(" / ")}",
            )
        }
        state.speechText?.let { text ->
            item {
                InfoPanel(
                    icon = { Icon(Icons.Outlined.CameraAlt, contentDescription = null) },
                    title = "语音识别结果",
                    body = text,
                )
            }
        }
        item { SectionTitle("识别关联商品", "可将识别 query 带入导购继续推荐。") }
        if (state.result.similarProducts.isEmpty()) {
            item { Text("等待后端识别结果。", color = BuyWiseTheme.colors.muted) }
        }
        items(state.result.similarProducts) { product ->
            ProductCard(
                product = product,
                onClick = { onProductClick(product.id) },
                isInCompareBasket = isInCompareBasket(product.id),
                onToggleCompare = { onToggleCompare(product) },
            )
        }
    }
}

@Composable
private fun CompareDecisionCard(state: CompareState) {
    val winner = state.products.firstOrNull { it.id == state.winnerId }
        ?: state.products.maxByOrNull { it.recommendationScore ?: -1.0 }
    Card(
        colors = CardDefaults.cardColors(containerColor = BuyWiseTheme.colors.panel),
        shape = RoundedCornerShape(8.dp),
        border = CardDefaults.outlinedCardBorder(),
    ) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            androidx.compose.foundation.layout.Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Icon(Icons.Outlined.EmojiEvents, contentDescription = null, tint = BuyWiseTheme.colors.accent)
                Text("AI 对比结论", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
            }
            Text(
                state.summary ?: "选择 2 个以上商品后，BuyWise 会结合价格、评分、推荐分和优缺点生成决策建议。",
                color = BuyWiseTheme.colors.muted,
                style = MaterialTheme.typography.bodyMedium,
            )
            winner?.let {
                Surface(color = BuyWiseTheme.colors.secondarySoft, shape = RoundedCornerShape(8.dp)) {
                    Column(modifier = Modifier.fillMaxWidth().padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Text("优先推荐", color = BuyWiseTheme.colors.secondary, fontWeight = FontWeight.Bold)
                        Text(it.name, color = BuyWiseTheme.colors.ink, fontWeight = FontWeight.Bold)
                        Text(
                            "推荐指数 ${it.recommendationScore.displayScore()}，${it.headline}",
                            color = BuyWiseTheme.colors.muted,
                            style = MaterialTheme.typography.bodyMedium,
                            maxLines = 2,
                            overflow = TextOverflow.Ellipsis,
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun CompareTable(rows: List<CompareRow>, products: List<Product>) {
    Card(
        colors = CardDefaults.cardColors(containerColor = BuyWiseTheme.colors.panel),
        shape = RoundedCornerShape(8.dp),
        border = CardDefaults.outlinedCardBorder(),
    ) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            androidx.compose.foundation.layout.Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Icon(Icons.AutoMirrored.Outlined.CompareArrows, contentDescription = null, tint = BuyWiseTheme.colors.primary)
                Text("对比维度", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
            }
            if (rows.isEmpty()) {
                Text("等待后端对比结果。", color = BuyWiseTheme.colors.muted)
            } else {
                rows.forEachIndexed { index, row ->
                    if (index > 0) {
                        HorizontalDivider(color = BuyWiseTheme.colors.border)
                    }
                    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Text(row.title, fontWeight = FontWeight.Bold, color = BuyWiseTheme.colors.ink)
                        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            row.values.forEachIndexed { valueIndex, value ->
                                AssistChip(
                                    onClick = {},
                                    label = {
                                        Text(
                                            value,
                                            maxLines = 2,
                                            overflow = TextOverflow.Ellipsis,
                                        )
                                    },
                                    leadingIcon = if (row.isBestValue(valueIndex, products)) {
                                        { Icon(Icons.Outlined.EmojiEvents, contentDescription = null) }
                                    } else {
                                        null
                                    },
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun UploadPanel(
    isLoading: Boolean,
    hasQuery: Boolean,
    onRunVisionDemo: () -> Unit,
    onRunSpeechDemo: () -> Unit,
    onUseQuery: () -> Unit,
) {
    Card(
        colors = CardDefaults.cardColors(containerColor = BuyWiseTheme.colors.panel),
        shape = RoundedCornerShape(8.dp),
        border = CardDefaults.outlinedCardBorder(),
    ) {
        Column(modifier = Modifier.fillMaxWidth().padding(18.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
            Surface(color = BuyWiseTheme.colors.accentSoft, shape = RoundedCornerShape(8.dp), modifier = Modifier.size(48.dp)) {
                Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center) {
                    Icon(Icons.Outlined.CameraAlt, contentDescription = null, tint = BuyWiseTheme.colors.accent)
                }
            }
            Text("上传商品图片", style = MaterialTheme.typography.titleLarge, color = BuyWiseTheme.colors.ink)
            Text(
                "图片和音频使用内置演示资源，不申请相机或麦克风权限。",
                color = BuyWiseTheme.colors.muted,
                style = MaterialTheme.typography.bodyMedium,
            )
            FilledTonalButton(onClick = onRunVisionDemo, enabled = !isLoading) {
                Icon(Icons.Outlined.ImageSearch, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text("运行识图联调")
            }
            OutlinedButton(onClick = onRunSpeechDemo, enabled = !isLoading) {
                Icon(Icons.Outlined.CameraAlt, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text("运行语音联调")
            }
            OutlinedButton(onClick = onUseQuery, enabled = hasQuery && !isLoading) {
                Icon(Icons.Outlined.Inventory2, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text("带入导购")
            }
        }
    }
}

private fun CompareRow.isBestValue(index: Int, products: List<Product>): Boolean {
    if (products.isEmpty() || index !in products.indices) return false
    val bestScore = products.maxOfOrNull { it.recommendationScore ?: -1.0 } ?: return false
    return title.contains("推荐") && (products[index].recommendationScore ?: -1.0) == bestScore
}

private fun Double?.displayScore(): String = this?.let { "${formatNumber(it)}分" } ?: "待分析"

private fun formatNumber(value: Double): String =
    if (value % 1.0 == 0.0) value.toInt().toString() else "%.1f".format(value)
