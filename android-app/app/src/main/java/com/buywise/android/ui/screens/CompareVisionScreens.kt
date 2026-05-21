package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
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
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.buywise.android.data.CompareRow
import com.buywise.android.data.CompareState
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
        item { SectionTitle("商品对比", "把候选商品的价格、评分和卖点放到同一张决策表里") }
        item { CompareTable(rows = state.rows) }
        item { SectionTitle("候选商品", "点击商品查看完整优缺点") }
        items(state.products) { product ->
            ProductCard(product = product, onClick = { onProductClick(product.id) })
        }
    }
}

@Composable
fun VisionScreen(state: VisionState, onProductClick: (String) -> Unit) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(18.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item { SectionTitle("图像识别", "保留原生上传入口，并展示 mock 识别结果") }
        item { UploadPanel() }
        item {
            InfoPanel(
                icon = { Icon(Icons.Outlined.Inventory2, contentDescription = null) },
                title = state.result.title,
                body = "置信度 ${state.result.confidence}% - ${state.result.labels.joinToString(" / ")}",
            )
        }
        item { SectionTitle("相似商品", "根据识别标签推荐可继续比较的商品") }
        items(state.result.similarProducts) { product ->
            ProductCard(product = product, onClick = { onProductClick(product.id) })
        }
    }
}

@Composable
private fun CompareTable(rows: List<CompareRow>) {
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
            rows.forEachIndexed { index, row ->
                if (index > 0) {
                    HorizontalDivider(color = BuyWiseTheme.colors.border)
                }
                Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text(row.title, fontWeight = FontWeight.Bold, color = BuyWiseTheme.colors.ink)
                    Text(
                        row.values.joinToString("  |  "),
                        color = BuyWiseTheme.colors.muted,
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
            }
        }
    }
}

@Composable
private fun UploadPanel() {
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
                "后续会接入真实多模态识别服务，当前展示固定识别结果。",
                color = BuyWiseTheme.colors.muted,
                style = MaterialTheme.typography.bodyMedium,
            )
            FilledTonalButton(onClick = {}) {
                Icon(Icons.Outlined.ImageSearch, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text("查看 mock 识别结果")
            }
        }
    }
}
