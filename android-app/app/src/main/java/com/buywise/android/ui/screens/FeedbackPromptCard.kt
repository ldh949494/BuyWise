package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.RateReview
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.buywise.android.data.FeedbackDraft
import com.buywise.android.data.FeedbackPrompt
import com.buywise.android.ui.BuyWiseTheme

private val ProTags = listOf("good_value", "easy_to_use", "quiet", "comfortable", "durable")
private val ConTags = listOf("noisy", "overpriced", "fragile", "uncomfortable", "hard_to_use")

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
    Card(
        colors = CardDefaults.cardColors(containerColor = BuyWiseTheme.colors.panel),
        shape = RoundedCornerShape(8.dp),
        border = CardDefaults.outlinedCardBorder(),
    ) {
        Column(modifier = Modifier.fillMaxWidth().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Icon(Icons.Outlined.RateReview, contentDescription = null, tint = BuyWiseTheme.colors.primary)
                Column(modifier = Modifier.weight(1f)) {
                    Text(prompt.productName, style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
                    Text("提交收货后反馈", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
                }
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
                    label = { Text("$rating 星") },
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
        TagPicker("优点标签", ProTags, draft.prosTags) {
            onDraftChange(draft.copy(prosTags = it))
        }
        TagPicker("缺点标签", ConTags, draft.consTags) {
            onDraftChange(draft.copy(consTags = it))
        }
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

@Composable
private fun TagPicker(label: String, tags: List<String>, selected: List<String>, onSelectedChange: (List<String>) -> Unit) {
    Text(label, fontWeight = FontWeight.Bold, color = BuyWiseTheme.colors.ink)
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        tags.forEach { tag ->
            AssistChip(
                onClick = {
                    onSelectedChange(if (tag in selected) selected - tag else selected + tag)
                },
                label = { Text(tag) },
            )
        }
    }
}
