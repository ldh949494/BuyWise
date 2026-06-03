package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
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
import androidx.compose.material.icons.outlined.Inventory2
import androidx.compose.material.icons.outlined.Refresh
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
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
import com.buywise.android.data.CompareRow
import com.buywise.android.data.CompareState
import com.buywise.android.data.Product
import com.buywise.android.data.VisionState
import com.buywise.android.ui.BuyWiseDimens
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.displayPrice
import com.buywise.android.ui.displayRating
import com.buywise.android.ui.shortName
import com.buywise.android.ui.components.ProductCard
import com.buywise.android.ui.components.ProductImagePreview
import com.buywise.android.ui.components.SectionTitle
import com.buywise.android.ui.components.FloatingGlassCard
import com.buywise.android.ui.components.FloatingGlassTone

@Composable
fun CompareScreen(
    state: CompareState,
    onProductClick: (String) -> Unit,
    onRefresh: () -> Unit,
) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(18.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    SectionTitle("商品对比", "看清价格、评分和关键差异。")
                }
                OutlinedButton(onClick = onRefresh, enabled = !state.isLoading) {
                    Icon(Icons.Outlined.Refresh, contentDescription = null)
                    Spacer(modifier = Modifier.width(6.dp))
                    Text("刷新")
                }
            }
        }
        if (state.isLoading) {
            item { LinearProgressIndicator(modifier = Modifier.fillMaxWidth()) }
        }
        state.errorMessage?.let { message ->
            item { ErrorPanel(message = message, actionLabel = "刷新", onAction = onRefresh) }
        }
        if (state.products.isNotEmpty()) {
            item { CompareCandidateStrip(products = state.products, onProductClick = onProductClick) }
        }
        item { CompareDecisionCard(state = state) }
        item { CompareTable(rows = state.rows, products = state.products) }
        item { SectionTitle("候选商品", "点击商品查看详情。") }
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
        item { SectionTitle("识别商品", "用图片或语音生成购物需求。") }
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
            InfoPanel(
                icon = { Icon(Icons.Outlined.Inventory2, contentDescription = null) },
                title = "识别结果",
                body = state.result.displayVisionSummary(state.recognizedQuery),
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
        item { SectionTitle("关联商品", "可带入导购继续推荐。") }
        if (state.result.similarProducts.isEmpty()) {
            item { Text("识别图片后，会展示同类候选商品。", color = BuyWiseTheme.colors.muted) }
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
