package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.buywise.android.data.GuideSessionHistoryState
import com.buywise.android.data.GuideSessionSummary
import com.buywise.android.ui.BuyWiseIcons
import com.buywise.android.ui.BuyWiseTheme

@Composable
fun GuideSessionHistoryDialog(
    state: GuideSessionHistoryState,
    onDismiss: () -> Unit,
    onOpenSession: (String) -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        confirmButton = { TextButton(onClick = onDismiss) { Text("关闭") } },
        title = { Text("导购历史") },
        text = {
            when {
                state.isLoading -> Row(horizontalArrangement = Arrangement.spacedBy(10.dp), verticalAlignment = Alignment.CenterVertically) {
                    CircularProgressIndicator()
                    Text("正在加载历史记录")
                }
                state.errorMessage != null -> Text(state.errorMessage, color = BuyWiseTheme.colors.danger)
                state.items.isEmpty() -> Text("暂无历史导购会话")
                else -> LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    items(state.items) { item ->
                        GuideSessionHistoryRow(item = item, onOpen = { onOpenSession(item.sessionId) })
                    }
                }
            }
        },
    )
}

@Composable
private fun GuideSessionHistoryRow(item: GuideSessionSummary, onOpen: () -> Unit) {
    TextButton(onClick = onOpen, modifier = Modifier.fillMaxWidth()) {
        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp), verticalAlignment = Alignment.CenterVertically) {
            Icon(BuyWiseIcons.Assistant, contentDescription = null, tint = BuyWiseTheme.colors.primary)
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                Text(item.title ?: "导购会话", color = BuyWiseTheme.colors.ink, fontWeight = FontWeight.Bold, maxLines = 1, overflow = TextOverflow.Ellipsis)
                Text(
                    item.lastMessage ?: item.updatedAt ?: item.sessionId,
                    color = BuyWiseTheme.colors.muted,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.padding(top = 2.dp),
                )
            }
        }
    }
}
