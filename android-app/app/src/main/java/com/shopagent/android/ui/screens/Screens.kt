package com.shopagent.android.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.automirrored.outlined.CompareArrows
import androidx.compose.material.icons.outlined.AutoAwesome
import androidx.compose.material.icons.outlined.CameraAlt
import androidx.compose.material.icons.outlined.ImageSearch
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.shopagent.android.data.CompareState
import com.shopagent.android.data.GuideState
import com.shopagent.android.data.HomeState
import com.shopagent.android.data.Product
import com.shopagent.android.data.VisionState
import com.shopagent.android.ui.ShopAgentTheme
import com.shopagent.android.ui.components.MetricPill
import com.shopagent.android.ui.components.ProductCard
import com.shopagent.android.ui.components.SectionTitle

@Composable
fun HomeScreen(state: HomeState, onProductClick: (String) -> Unit, onOpenGuide: () -> Unit) {
    LazyColumn(
        modifier = Modifier.fillMaxSize().padding(18.dp),
        verticalArrangement = Arrangement.spacedBy(18.dp),
    ) {
        item {
            Card(
                colors = CardDefaults.cardColors(containerColor = ShopAgentTheme.colors.panel),
                shape = RoundedCornerShape(22.dp),
            ) {
                Column(modifier = Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
                    Text("ShopAgent", color = ShopAgentTheme.colors.primary, fontWeight = FontWeight.Bold)
                    Text(state.heroTitle, fontSize = 28.sp, fontWeight = FontWeight.Bold)
                    Text(state.heroSubtitle, color = ShopAgentTheme.colors.muted)
                    Button(onClick = onOpenGuide) {
                        Icon(Icons.Outlined.AutoAwesome, contentDescription = null)
                        Spacer(modifier = Modifier.padding(horizontal = 4.dp))
                        Text("开始 AI 导购")
                    }
                }
            }
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                MetricPill("导购模式", "文本 MVP")
                MetricPill("后端预留", "10.0.2.2")
            }
        }
        item {
            SectionTitle("精选商品", "先用 mock 数据把移动端导购体验跑通")
        }
        items(state.products) { product ->
            ProductCard(product = product, onClick = { onProductClick(product.id) })
        }
    }
}

@Composable
fun GuideScreen(
    state: GuideState,
    onQueryChange: (String) -> Unit,
    onSubmit: () -> Unit,
    onProductClick: (String) -> Unit,
) {
    LazyColumn(
        modifier = Modifier.fillMaxSize().padding(18.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item { SectionTitle("AI 导购", "输入预算、场景和偏好，先生成结构化需求") }
        item {
            OutlinedTextField(
                value = state.query,
                onValueChange = onQueryChange,
                modifier = Modifier.fillMaxWidth(),
                minLines = 3,
                label = { Text("购物需求") },
                placeholder = { Text("例如：300 元以内，适合 FPS 的轻量化无线鼠标") },
            )
        }
        item {
            Button(onClick = onSubmit, modifier = Modifier.fillMaxWidth()) {
                Text("生成推荐")
            }
        }
        item {
            Card(colors = CardDefaults.cardColors(containerColor = ShopAgentTheme.colors.panel)) {
                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("需求画像", fontWeight = FontWeight.Bold)
                    Text(state.intentSummary, color = ShopAgentTheme.colors.muted)
                }
            }
        }
        items(state.recommendations) { recommendation ->
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                ProductCard(product = recommendation.product, onClick = { onProductClick(recommendation.product.id) })
                Text(recommendation.reason, color = ShopAgentTheme.colors.muted, modifier = Modifier.padding(horizontal = 8.dp))
            }
        }
    }
}

@Composable
fun CompareScreen(state: CompareState, onProductClick: (String) -> Unit) {
    LazyColumn(
        modifier = Modifier.fillMaxSize().padding(18.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item { SectionTitle("商品对比", "第一版以 mock 对比表承接后续真实能力") }
        items(state.products) { product ->
            ProductCard(product = product, onClick = { onProductClick(product.id) })
        }
        item {
            Card(colors = CardDefaults.cardColors(containerColor = ShopAgentTheme.colors.panel)) {
                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Icon(Icons.AutoMirrored.Outlined.CompareArrows, contentDescription = null)
                        Text("对比摘要", fontWeight = FontWeight.Bold)
                    }
                    state.rows.forEach { row ->
                        Text(row.title, fontWeight = FontWeight.SemiBold)
                        Text(row.values.joinToString(" | "), color = ShopAgentTheme.colors.muted)
                    }
                }
            }
        }
    }
}

@Composable
fun VisionScreen(state: VisionState, onProductClick: (String) -> Unit) {
    LazyColumn(
        modifier = Modifier.fillMaxSize().padding(18.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item { SectionTitle("图像识别", "当前保留原生入口和 mock 识别结果") }
        item {
            Card(colors = CardDefaults.cardColors(containerColor = ShopAgentTheme.colors.panel)) {
                Column(modifier = Modifier.fillMaxWidth().padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Icon(Icons.Outlined.CameraAlt, contentDescription = null)
                    Text("上传或拍摄商品图片", fontSize = 20.sp, fontWeight = FontWeight.Bold)
                    Text("首版不接入真实识别，先承接结果结构和推荐区块。", color = ShopAgentTheme.colors.muted)
                    FilledTonalButton(onClick = {}) {
                        Icon(Icons.Outlined.ImageSearch, contentDescription = null)
                        Spacer(modifier = Modifier.padding(horizontal = 4.dp))
                        Text("查看 mock 识别结果")
                    }
                }
            }
        }
        item {
            Card(colors = CardDefaults.cardColors(containerColor = ShopAgentTheme.colors.panel)) {
                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(state.result.title, fontWeight = FontWeight.Bold)
                    Text("置信度 ${state.result.confidence}%", color = ShopAgentTheme.colors.primary)
                    Text(state.result.labels.joinToString(" / "), color = ShopAgentTheme.colors.muted)
                }
            }
        }
        items(state.result.similarProducts) { product ->
            ProductCard(product = product, onClick = { onProductClick(product.id) })
        }
    }
}

@Composable
fun ProductDetailScreen(product: Product?, onBack: () -> Unit) {
    LazyColumn(
        modifier = Modifier.fillMaxSize().padding(18.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item {
            IconButton(onClick = onBack) {
                Icon(Icons.AutoMirrored.Outlined.ArrowBack, contentDescription = "返回")
            }
        }
        item {
            if (product == null) {
                Text("商品不存在", fontSize = 22.sp, fontWeight = FontWeight.Bold)
            } else {
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Text(product.brand, color = ShopAgentTheme.colors.secondary, fontWeight = FontWeight.Bold)
                    Text(product.name, fontSize = 28.sp, fontWeight = FontWeight.Bold)
                    Text("¥${product.price} · 推荐分 ${product.score}", color = ShopAgentTheme.colors.primary, fontWeight = FontWeight.Bold)
                    Text(product.headline, color = ShopAgentTheme.colors.muted)
                }
            }
        }
        if (product != null) {
            item {
                DetailBlock("适合", product.advantages)
            }
            item {
                DetailBlock("注意", product.cautions)
            }
            item {
                DetailBlock("标签", product.tags)
            }
        }
    }
}

@Composable
private fun DetailBlock(title: String, items: List<String>) {
    Card(colors = CardDefaults.cardColors(containerColor = ShopAgentTheme.colors.panel)) {
        Column(modifier = Modifier.fillMaxWidth().padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(title, fontWeight = FontWeight.Bold)
            items.forEach { item ->
                Text("• $item", color = ShopAgentTheme.colors.muted)
            }
        }
    }
}
