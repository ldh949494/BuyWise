package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.RateReview
import androidx.compose.material3.Button
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.buywise.android.data.FeedbackDraft
import com.buywise.android.data.FeedbackPrompt
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.components.EvidenceTag
import com.buywise.android.ui.components.EvidenceTone
import com.buywise.android.ui.components.FloatingGlassCard
import com.buywise.android.ui.components.FloatingGlassTone

@Composable
fun FeedbackPromptCard(
    prompt: FeedbackPrompt,
    draft: FeedbackDraft,
    expanded: Boolean,
    isSubmitting: Boolean,
    errorMessage: String?,
    canUseFeedback: Boolean,
    tokenRequiredMessage: String?,
    onToggle: () -> Unit,
    onDraftChange: (FeedbackDraft) -> Unit,
    onSubmit: () -> Unit,
) {
    FloatingGlassCard(
        tone = if (expanded) FloatingGlassTone.Warm else FloatingGlassTone.Neutral,
        contentPadding = 16.dp,
    ) {
        Column(modifier = Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
                Surface(color = BuyWiseTheme.colors.primarySoft, shape = RoundedCornerShape(12.dp), modifier = Modifier.size(46.dp)) {
                    Box(contentAlignment = Alignment.Center) {
                        Icon(Icons.Outlined.RateReview, contentDescription = null, tint = BuyWiseTheme.colors.primary)
                    }
                }
                Column(modifier = Modifier.weight(1f)) {
                    Text(prompt.productName, style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
                    Text("已购买", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
                }
                EvidenceTag("待反馈", tone = EvidenceTone.Warning)
            }
            tokenRequiredMessage?.takeIf { !canUseFeedback }?.let {
                Text(it, color = BuyWiseTheme.colors.danger, style = MaterialTheme.typography.bodyMedium)
            }
            Button(onClick = onToggle, enabled = canUseFeedback && !isSubmitting, modifier = Modifier.fillMaxWidth()) {
                Text(if (expanded) "收起反馈表单" else "评价")
            }
            if (expanded) {
                FeedbackForm(
                    draft = draft,
                    isSubmitting = isSubmitting,
                    errorMessage = errorMessage,
                    onDraftChange = onDraftChange,
                    onSubmit = onSubmit,
                )
            }
        }
    }
}

@Composable
private fun FeedbackForm(
    draft: FeedbackDraft,
    isSubmitting: Boolean,
    errorMessage: String?,
    onDraftChange: (FeedbackDraft) -> Unit,
    onSubmit: () -> Unit,
) {
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text("评分", fontWeight = FontWeight.Bold, color = BuyWiseTheme.colors.ink)
        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            (1..5).forEach { rating ->
                FilterChip(
                    selected = draft.rating == rating,
                    onClick = { onDraftChange(draft.copy(rating = rating)) },
                    label = { Text("★".repeat(rating)) },
                )
            }
        }
        OutlinedTextField(
            value = draft.content,
            onValueChange = { onDraftChange(draft.copy(content = it)) },
            modifier = Modifier.fillMaxWidth(),
            minLines = 3,
            label = { Text("使用体验") },
        )
        Text("是否符合预期", fontWeight = FontWeight.Bold, color = BuyWiseTheme.colors.ink)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            FilterChip(
                selected = draft.metExpectation,
                onClick = { onDraftChange(draft.copy(metExpectation = true)) },
                label = { Text("符合") },
                leadingIcon = if (draft.metExpectation) {
                    { Icon(Icons.Outlined.CheckCircle, contentDescription = null) }
                } else {
                    null
                },
            )
            FilterChip(
                selected = !draft.metExpectation,
                onClick = { onDraftChange(draft.copy(metExpectation = false)) },
                label = { Text("不符合") },
            )
        }
        errorMessage?.let { Text(it, color = BuyWiseTheme.colors.danger, style = MaterialTheme.typography.bodyMedium) }
        Button(onClick = onSubmit, enabled = !isSubmitting, modifier = Modifier.fillMaxWidth()) {
            Text(if (isSubmitting) "提交中..." else "提交反馈")
        }
    }
}
