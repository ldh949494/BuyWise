package com.buywise.android.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
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
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.automirrored.outlined.Send
import androidx.compose.material.icons.outlined.AutoAwesome
import androidx.compose.material.icons.outlined.CameraAlt
import androidx.compose.material.icons.outlined.ImageSearch
import androidx.compose.material.icons.outlined.Mic
import androidx.compose.material.icons.outlined.PhotoLibrary
import androidx.compose.material.icons.outlined.SmartToy
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.buywise.android.data.GuideChatMessage
import com.buywise.android.data.GuideChatRole
import com.buywise.android.data.GuideState
import com.buywise.android.data.Recommendation
import com.buywise.android.data.cleanMarkdownText
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.components.FloatingGlassCard
import com.buywise.android.ui.components.FloatingGlassTone
import com.buywise.android.ui.components.ProductImagePreview
import com.buywise.android.ui.displayPrice

@Composable
fun GuideChatScreen(
    state: GuideState,
    onBack: () -> Unit,
    onDraftChange: (String) -> Unit,
    onSend: () -> Unit,
    onPickImage: () -> Unit,
    onTakePhoto: () -> Unit,
    onRunVisionDemo: () -> Unit,
    onRunSpeechDemo: () -> Unit,
    onProductClick: (String) -> Unit,
) {
    val listState = rememberLazyListState()
    LaunchedEffect(state.chatMessages.size, state.chatMessages.lastOrNull()?.text) {
        if (state.chatMessages.isNotEmpty()) {
            listState.animateScrollToItem(state.chatMessages.size)
        }
    }

    Column(modifier = Modifier.fillMaxSize()) {
        GuideChatTopBar(onBack = onBack)
        LazyColumn(
            state = listState,
            modifier = Modifier.weight(1f),
            contentPadding = PaddingValues(18.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            item { OpeningAssistantMessage(state = state, onProductClick = onProductClick) }
            items(state.chatMessages) { message ->
                ChatMessageRow(message = message, onProductClick = onProductClick)
            }
            if (state.errorMessage != null) {
                item { ErrorPanel(message = state.errorMessage) }
            }
        }
        GuideChatInputBar(
            draft = state.chatDraft,
            isStreaming = state.isStreaming,
            onDraftChange = onDraftChange,
            onSend = onSend,
            onPickImage = onPickImage,
            onTakePhoto = onTakePhoto,
            onRunVisionDemo = onRunVisionDemo,
            onRunSpeechDemo = onRunSpeechDemo,
        )
    }
}

@Composable
private fun GuideChatTopBar(onBack: () -> Unit) {
    Row(
        modifier = Modifier.fillMaxWidth().padding(horizontal = 14.dp, vertical = 12.dp),
        horizontalArrangement = Arrangement.spacedBy(12.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        IconButton(onClick = onBack) {
            Icon(Icons.AutoMirrored.Outlined.ArrowBack, contentDescription = "返回导购工作台")
        }
        Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
            Text("对话导购助手", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
            Text("继续追问商品区别、推荐理由或细节", color = BuyWiseTheme.colors.muted)
        }
        Surface(color = BuyWiseTheme.colors.panel, shape = RoundedCornerShape(16.dp), shadowElevation = 4.dp, modifier = Modifier.size(52.dp)) {
            Icon(Icons.Outlined.AutoAwesome, contentDescription = null, tint = BuyWiseTheme.colors.primary, modifier = Modifier.padding(14.dp))
        }
    }
}

@Composable
private fun OpeningAssistantMessage(state: GuideState, onProductClick: (String) -> Unit) {
    val text = when {
        state.query.isNotBlank() -> "我已看到你的需求：${state.query}。你可以继续问我商品区别、推荐理由或细节。"
        else -> "告诉我预算、用途和偏好，我可以帮你筛选商品。"
    }
    AssistantBubble(text = text, recommendations = state.recommendations, onProductClick = onProductClick)
}

@Composable
private fun ChatMessageRow(message: GuideChatMessage, onProductClick: (String) -> Unit) {
    if (message.role == GuideChatRole.USER) {
        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
            Surface(color = BuyWiseTheme.colors.primary, shape = RoundedCornerShape(18.dp, 18.dp, 4.dp, 18.dp)) {
                Text(
                    message.text,
                    modifier = Modifier.padding(horizontal = 14.dp, vertical = 10.dp).fillMaxWidth(0.78f),
                    color = Color.White,
                    style = MaterialTheme.typography.bodyMedium,
                )
            }
        }
    } else if (message.role == GuideChatRole.SYSTEM) {
        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.Center) {
            Surface(color = BuyWiseTheme.colors.primarySoft, shape = RoundedCornerShape(999.dp)) {
                Text(
                    message.text,
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 7.dp),
                    color = BuyWiseTheme.colors.primary,
                    style = MaterialTheme.typography.labelMedium,
                )
            }
        }
    } else {
        AssistantBubble(text = message.text.ifBlank { "正在整理回复..." }, recommendations = message.recommendations, onProductClick = onProductClick)
    }
}

@Composable
private fun AssistantBubble(
    text: String,
    recommendations: List<Recommendation>,
    onProductClick: (String) -> Unit,
) {
    val displayText = text.cleanMarkdownText().ifBlank { text }
    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
        Surface(color = BuyWiseTheme.colors.primarySoft, shape = CircleShape, modifier = Modifier.size(34.dp)) {
            Icon(Icons.Outlined.SmartToy, contentDescription = null, tint = BuyWiseTheme.colors.primary, modifier = Modifier.padding(7.dp))
        }
        Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Surface(color = BuyWiseTheme.colors.panel, shape = RoundedCornerShape(18.dp, 18.dp, 18.dp, 4.dp), shadowElevation = 1.dp) {
                Text(
                    displayText,
                    modifier = Modifier.padding(horizontal = 14.dp, vertical = 10.dp),
                    color = BuyWiseTheme.colors.ink,
                    style = MaterialTheme.typography.bodyMedium,
                )
            }
            if (recommendations.isNotEmpty()) {
                LazyRow(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    items(recommendations) { recommendation ->
                        CompactRecommendationCard(
                            recommendation = recommendation,
                            onClick = { onProductClick(recommendation.product.id) },
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun CompactRecommendationCard(recommendation: Recommendation, onClick: () -> Unit) {
    val product = recommendation.product
    FloatingGlassCard(
        modifier = Modifier.width(210.dp),
        tone = FloatingGlassTone.Primary,
        radius = 16.dp,
        fillMaxWidth = false,
        contentPadding = 10.dp,
        onClick = onClick,
    ) {
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            ProductImagePreview(product = product, modifier = Modifier.size(64.dp))
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text(product.name, color = BuyWiseTheme.colors.ink, fontWeight = FontWeight.Bold, maxLines = 2, overflow = TextOverflow.Ellipsis)
                Text(product.price.displayPrice(), color = BuyWiseTheme.colors.primary, fontWeight = FontWeight.Bold)
            }
        }
    }
}

@Composable
private fun GuideChatInputBar(
    draft: String,
    isStreaming: Boolean,
    onDraftChange: (String) -> Unit,
    onSend: () -> Unit,
    onPickImage: () -> Unit,
    onTakePhoto: () -> Unit,
    onRunVisionDemo: () -> Unit,
    onRunSpeechDemo: () -> Unit,
) {
    var imageMenuExpanded by remember { mutableStateOf(false) }
    Surface(color = BuyWiseTheme.colors.panel, shadowElevation = 8.dp) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(horizontal = 14.dp, vertical = 12.dp),
            horizontalArrangement = Arrangement.spacedBy(10.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Box {
                IconButton(onClick = { imageMenuExpanded = true }, enabled = !isStreaming) {
                    Icon(Icons.Outlined.ImageSearch, contentDescription = "图片识别", tint = BuyWiseTheme.colors.primary)
                }
                DropdownMenu(expanded = imageMenuExpanded, onDismissRequest = { imageMenuExpanded = false }) {
                    DropdownMenuItem(
                        text = { Text("相册识图") },
                        leadingIcon = { Icon(Icons.Outlined.PhotoLibrary, contentDescription = null) },
                        onClick = {
                            imageMenuExpanded = false
                            onPickImage()
                        },
                    )
                    DropdownMenuItem(
                        text = { Text("拍照识图") },
                        leadingIcon = { Icon(Icons.Outlined.CameraAlt, contentDescription = null) },
                        onClick = {
                            imageMenuExpanded = false
                            onTakePhoto()
                        },
                    )
                    DropdownMenuItem(
                        text = { Text("快速识别") },
                        leadingIcon = { Icon(Icons.Outlined.AutoAwesome, contentDescription = null) },
                        onClick = {
                            imageMenuExpanded = false
                            onRunVisionDemo()
                        },
                    )
                }
            }
            IconButton(onClick = onRunSpeechDemo, enabled = !isStreaming) {
                Icon(Icons.Outlined.Mic, contentDescription = "语音描述", tint = BuyWiseTheme.colors.primary)
            }
            OutlinedTextField(
                value = draft,
                onValueChange = onDraftChange,
                modifier = Modifier.weight(1f),
                placeholder = { Text("继续追问商品细节...") },
                singleLine = true,
            )
            Surface(
                color = if (draft.isBlank() || isStreaming) BuyWiseTheme.colors.primarySoft else BuyWiseTheme.colors.primary,
                shape = CircleShape,
                modifier = Modifier.size(50.dp).clickable(enabled = draft.isNotBlank() && !isStreaming, onClick = onSend),
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Icon(
                        Icons.AutoMirrored.Outlined.Send,
                        contentDescription = "发送",
                        tint = if (draft.isBlank() || isStreaming) BuyWiseTheme.colors.muted else Color.White,
                    )
                }
            }
        }
    }
}
