package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
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
import com.buywise.android.data.BundlePlan
import com.buywise.android.data.AppliedPreferences
import com.buywise.android.data.GuideChatMessage
import com.buywise.android.data.GuideChatRole
import com.buywise.android.data.GuideState
import com.buywise.android.data.Recommendation
import com.buywise.android.data.cleanMarkdownText
import com.buywise.android.ui.BuyWiseIcons
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.BuyWiseVisualAssets
import com.buywise.android.ui.displayPrice
import com.buywise.android.ui.displayRating
import com.buywise.android.ui.components.ChatBundlePlanCard
import com.buywise.android.ui.components.ChatBundleSummary
import com.buywise.android.ui.components.ChatRecommendationCard
import com.buywise.android.ui.components.EvidenceTag
import com.buywise.android.ui.components.EvidenceTone
import com.buywise.android.ui.components.ShowcaseTopBar
import com.buywise.android.ui.components.TactileIconTile
import com.buywise.android.ui.components.TactileIconTone

@Composable
fun GuideChatScreen(
    state: GuideState,
    isRecordingAudio: Boolean,
    onBack: () -> Unit,
    onDraftChange: (String) -> Unit,
    onSend: () -> Unit,
    onPickImage: () -> Unit,
    onTakePhoto: () -> Unit,
    onRunVisionDemo: () -> Unit,
    onRunSpeechDemo: () -> Unit,
    onProductClick: (String) -> Unit,
    onIgnoreSavedPreferencesChange: (Boolean) -> Unit,
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
            item { OpeningAssistantMessage(state = state) }
            item { GuideProcessingCard(state = state, onIgnoreSavedPreferencesChange = onIgnoreSavedPreferencesChange) }
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
            isRecordingAudio = isRecordingAudio,
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
    ShowcaseTopBar(
        title = "AI 导购",
        modifier = Modifier.padding(horizontal = 14.dp, vertical = 12.dp),
        onBack = onBack,
        actionIcon = BuyWiseIcons.Guide,
        actionDescription = "导购助手",
    )
}

@Composable
private fun OpeningAssistantMessage(state: GuideState) {
    val text = when {
        state.compareChatContext != null -> "已带入当前对比结果。你可以继续问我哪个更适合、主要风险或购买前要确认什么。"
        state.query.isNotBlank() -> "我已看到你的需求：${state.query}。你可以继续问我商品区别、推荐理由或细节。"
        else -> "告诉我品类、商品名或需求，我可以先筛选商品；预算、用途和偏好可以之后补充。"
    }
    AssistantBubble(text = text, recommendations = emptyList(), bundlePlans = emptyList(), appliedPreferences = AppliedPreferences(), onProductClick = {})
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
        AssistantBubble(
            text = message.text.ifBlank { "正在整理回复..." },
            recommendations = message.recommendations,
            bundlePlans = message.bundlePlans,
            appliedPreferences = message.appliedPreferences,
            onProductClick = onProductClick,
        )
    }
}

@Composable
private fun AssistantBubble(
    text: String,
    recommendations: List<Recommendation>,
    bundlePlans: List<BundlePlan>,
    appliedPreferences: AppliedPreferences,
    onProductClick: (String) -> Unit,
) {
    val displayText = text.cleanMarkdownText().ifBlank { text }
    Column(modifier = Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            TactileIconTile(
                assetRes = BuyWiseVisualAssets.AssistantRobot,
                contentDescription = null,
                size = 38.dp,
                iconSize = 34.dp,
                rounded = true,
                tone = TactileIconTone.Primary,
            )
            Surface(
                modifier = Modifier.weight(1f),
                color = BuyWiseTheme.colors.panel,
                shape = RoundedCornerShape(18.dp, 18.dp, 18.dp, 4.dp),
                shadowElevation = 1.dp,
            ) {
                if (recommendations.isEmpty() && bundlePlans.isEmpty()) {
                    Text(
                        displayText,
                        modifier = Modifier.padding(horizontal = 14.dp, vertical = 10.dp),
                        color = BuyWiseTheme.colors.ink,
                        style = MaterialTheme.typography.bodyMedium,
                    )
                } else if (bundlePlans.isNotEmpty()) {
                    Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                        AppliedPreferenceLine(appliedPreferences)
                        ChatBundleSummary(text = displayText, bundlePlans = bundlePlans)
                    }
                } else {
                    Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                        AppliedPreferenceLine(appliedPreferences)
                        ChatDecisionSummary(text = displayText, recommendations = recommendations)
                    }
                }
            }
        }
        if (recommendations.isNotEmpty()) {
            LazyRow(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp),
                contentPadding = PaddingValues(start = 44.dp, end = 18.dp),
            ) {
                items(recommendations) { recommendation ->
                    ChatRecommendationCard(
                        recommendation = recommendation,
                        onClick = { onProductClick(recommendation.product.id) },
                    )
                }
            }
        }
        if (bundlePlans.isNotEmpty()) {
            LazyRow(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp),
                contentPadding = PaddingValues(start = 44.dp, end = 18.dp),
            ) {
                items(bundlePlans) { plan ->
                    ChatBundlePlanCard(plan = plan, onProductClick = onProductClick)
                }
            }
        }
    }
}

@Composable
private fun AppliedPreferenceLine(appliedPreferences: AppliedPreferences) {
    if (!appliedPreferences.hasVisibleSummary) return
    Text(
        guidePreferenceSummaryText(appliedPreferences, false),
        color = BuyWiseTheme.colors.primary,
        style = MaterialTheme.typography.labelMedium,
        maxLines = 1,
        overflow = TextOverflow.Ellipsis,
    )
}

@Composable
private fun ChatDecisionSummary(
    text: String,
    recommendations: List<Recommendation>,
    modifier: Modifier = Modifier,
) {
    var expanded by remember { mutableStateOf(false) }
    val topRecommendation = recommendations.first()
    val product = topRecommendation.product
    val alternatives = recommendations.drop(1).take(2)

    Column(modifier = modifier, verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
            EvidenceTag("首推", tone = EvidenceTone.Success)
            Text(
                product.price.displayPrice(),
                color = BuyWiseTheme.colors.primary,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
            )
            Text(
                "评分 ${product.rating.displayRating()}",
                color = BuyWiseTheme.colors.muted,
                style = MaterialTheme.typography.labelMedium,
            )
        }
        Text(
            product.name,
            color = BuyWiseTheme.colors.ink,
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold,
            maxLines = 2,
            overflow = TextOverflow.Ellipsis,
        )
        ChatReasonBlock(
            title = "为什么先看它",
            lines = listOf(topRecommendation.reason, product.headline)
                .map { it.cleanMarkdownText() }
                .filter { it.isNotBlank() }
                .distinct()
                .take(2),
        )
        if (alternatives.isNotEmpty()) {
            Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text("备选", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.labelMedium)
                alternatives.forEach { recommendation ->
                    AlternativeProductLine(recommendation = recommendation)
                }
            }
        }
        if (text.isNotBlank()) {
            Surface(color = BuyWiseTheme.colors.panelAlt, shape = RoundedCornerShape(14.dp)) {
                Column(modifier = Modifier.padding(horizontal = 12.dp, vertical = 10.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text("补充说明", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.labelMedium)
                    Text(
                        text,
                        color = BuyWiseTheme.colors.ink,
                        style = MaterialTheme.typography.bodyMedium,
                        maxLines = if (expanded) Int.MAX_VALUE else 3,
                        overflow = TextOverflow.Ellipsis,
                    )
                    TextButton(onClick = { expanded = !expanded }) {
                        Text(if (expanded) "收起说明" else "展开完整说明")
                    }
                }
            }
        }
    }
}

@Composable
private fun ChatReasonBlock(title: String, lines: List<String>) {
    if (lines.isEmpty()) return
    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Text(title, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.labelMedium)
        lines.forEach { line ->
            Text(
                "- $line",
                color = BuyWiseTheme.colors.ink,
                style = MaterialTheme.typography.bodyMedium,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
            )
        }
    }
}

@Composable
private fun AlternativeProductLine(recommendation: Recommendation) {
    val product = recommendation.product
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            product.name,
            modifier = Modifier.weight(1f),
            color = BuyWiseTheme.colors.ink,
            style = MaterialTheme.typography.bodyMedium,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
        )
        Text(
            product.price.displayPrice(),
            color = BuyWiseTheme.colors.primary,
            style = MaterialTheme.typography.labelMedium,
            fontWeight = FontWeight.Bold,
        )
    }
}

@Composable
private fun GuideChatInputBar(
    draft: String,
    isStreaming: Boolean,
    isRecordingAudio: Boolean,
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
                TactileIconTile(
                    icon = BuyWiseIcons.Vision,
                    contentDescription = "图片识别",
                    size = 46.dp,
                    iconSize = 22.dp,
                    enabled = !isStreaming,
                    onClick = { imageMenuExpanded = true },
                )
                DropdownMenu(expanded = imageMenuExpanded, onDismissRequest = { imageMenuExpanded = false }) {
                    DropdownMenuItem(
                        text = { Text("相册识图") },
                        leadingIcon = { Icon(BuyWiseIcons.PhotoLibrary, contentDescription = null) },
                        onClick = {
                            imageMenuExpanded = false
                            onPickImage()
                        },
                    )
                    DropdownMenuItem(
                        text = { Text("拍照识图") },
                        leadingIcon = { Icon(BuyWiseIcons.Camera, contentDescription = null) },
                        onClick = {
                            imageMenuExpanded = false
                            onTakePhoto()
                        },
                    )
                    DropdownMenuItem(
                        text = { Text("快速识别") },
                        leadingIcon = { Icon(BuyWiseIcons.Guide, contentDescription = null) },
                        onClick = {
                            imageMenuExpanded = false
                            onRunVisionDemo()
                        },
                    )
                }
            }
            TactileIconTile(
                icon = BuyWiseIcons.Speech,
                contentDescription = if (isRecordingAudio) "停止录音" else "语音描述",
                size = 46.dp,
                iconSize = 22.dp,
                tone = if (isRecordingAudio) TactileIconTone.SolidPrimary else TactileIconTone.Primary,
                selected = isRecordingAudio,
                enabled = !isStreaming,
                onClick = onRunSpeechDemo,
            )
            OutlinedTextField(
                value = draft,
                onValueChange = onDraftChange,
                modifier = Modifier.weight(1f),
                placeholder = { Text(if (isRecordingAudio) "正在录音，点麦克风结束..." else "继续补充或追问...") },
                singleLine = true,
            )
            TactileIconTile(
                icon = BuyWiseIcons.Send,
                contentDescription = "发送",
                size = 50.dp,
                iconSize = 22.dp,
                rounded = true,
                tone = if (draft.isBlank() || isStreaming) TactileIconTone.Primary else TactileIconTone.SolidPrimary,
                enabled = draft.isNotBlank() && !isStreaming,
                onClick = onSend,
            )
        }
    }
}
