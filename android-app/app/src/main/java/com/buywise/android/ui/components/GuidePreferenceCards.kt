package com.buywise.android.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.buywise.android.data.GuidePreferences
import com.buywise.android.ui.BuyWiseDimens
import com.buywise.android.ui.BuyWiseIcons
import com.buywise.android.ui.BuyWiseTheme

@Composable
fun GuidePreferencesPanel(
    preferences: GuidePreferences,
    enabled: Boolean,
    onBudgetPolicyChange: (String) -> Unit,
    onPresentationStyleChange: (String) -> Unit,
    onPriorityTagToggle: (String) -> Unit,
    onExcludedTagToggle: (String) -> Unit,
    onOwnedCategoryToggle: (String) -> Unit,
    onBundleBudgetMaxChange: (String) -> Unit,
    onClear: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(modifier = modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        GuidePreferenceOverviewCard(preferences = preferences)
        PreferenceSegmentCard(
            title = "预算策略",
            description = "决定 AI 在推荐单品和整套方案时如何处理价格边界。",
            icon = BuyWiseIcons.Tune,
            options = listOf(
                PreferenceOption("strict", "严格预算", "只推荐预算内"),
                PreferenceOption("slightly_flexible", "小幅超预算", "默认 5%-10%"),
                PreferenceOption("quality_first", "品质优先", "允许为关键体验让步"),
            ),
            selected = preferences.budgetPolicy,
            enabled = enabled,
            onSelect = onBudgetPolicyChange,
        )
        BundleBudgetCard(
            value = preferences.bundleBudgetRange?.max?.toInt()?.toString().orEmpty(),
            budgetPolicy = preferences.budgetPolicy,
            enabled = enabled,
            onValueChange = onBundleBudgetMaxChange,
        )
        PreferenceTagCard(
            title = "核心偏好",
            description = "这些标签会提高对应商品和方案的排序权重。",
            icon = BuyWiseIcons.ThumbsUp,
            options = listOf("性价比", "静音", "耐用", "颜值", "便携", "游戏性能", "办公效率", "售后稳定"),
            selected = preferences.priorityTags,
            enabled = enabled,
            tone = PreferenceTagTone.Positive,
            onToggle = onPriorityTagToggle,
        )
        PreferenceTagCard(
            title = "排除项",
            description = "这些条件会在推荐理由和方案组合中被明确规避。",
            icon = BuyWiseIcons.ThumbsDown,
            options = listOf("二手", "RGB", "无线", "小众品牌"),
            selected = preferences.excludedTags,
            enabled = enabled,
            tone = PreferenceTagTone.Warning,
            onToggle = onExcludedTagToggle,
        )
        PreferenceTagCard(
            title = "已有设备",
            description = "整套方案会优先补齐缺口，避免重复购买。",
            icon = BuyWiseIcons.Inventory,
            options = listOf("电脑", "显示器", "机械键盘", "鼠标", "蓝牙耳机"),
            selected = preferences.ownedCategories,
            enabled = enabled,
            tone = PreferenceTagTone.Neutral,
            onToggle = onOwnedCategoryToggle,
        )
        PreferenceSegmentCard(
            title = "输出风格",
            description = "控制 AI 是直接给结论，还是展开多方案对比和解释。",
            icon = BuyWiseIcons.Guide,
            options = listOf(
                PreferenceOption("direct_answer", "直接结论", "先给可买项"),
                PreferenceOption("compare_options", "多方案对比", "适合组合输出"),
                PreferenceOption("detailed_explanation", "解释详细", "说明取舍依据"),
            ),
            selected = preferences.presentationStyle,
            enabled = enabled,
            onSelect = onPresentationStyleChange,
        )
        PreferenceResetCard(enabled = enabled, onClear = onClear)
    }
}

@Composable
private fun GuidePreferenceOverviewCard(preferences: GuidePreferences) {
    FloatingGlassCard(
        tone = if (preferences.hasSavedPreferences) FloatingGlassTone.Success else FloatingGlassTone.Primary,
        radius = BuyWiseDimens.CardRadius.dp,
        contentPadding = 18.dp,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top,
            ) {
                Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(5.dp)) {
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                        Icon(BuyWiseIcons.Tune, contentDescription = null, tint = BuyWiseTheme.colors.primary)
                        Text("导购偏好", style = MaterialTheme.typography.titleLarge, color = BuyWiseTheme.colors.ink)
                    }
                    Text(
                        "用于桌面好物和电子产品导购，单品走商品对比，组合走方案对比。",
                        color = BuyWiseTheme.colors.muted,
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
                EvidenceTag(
                    label = if (preferences.hasSavedPreferences) "已保存" else "待保存",
                    tone = if (preferences.hasSavedPreferences) EvidenceTone.Success else EvidenceTone.Info,
                )
            }
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.fillMaxWidth()) {
                PreferenceMetric(
                    label = "预算",
                    value = budgetPolicyLabel(preferences.budgetPolicy),
                    modifier = Modifier.weight(1f),
                )
                PreferenceMetric(
                    label = "整套上限",
                    value = preferences.bundleBudgetRange?.max?.toInt()?.let { "¥$it" } ?: "未设置",
                    modifier = Modifier.weight(1f),
                )
            }
        }
    }
}

@Composable
private fun PreferenceMetric(label: String, value: String, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .background(BuyWiseTheme.colors.panel.copy(alpha = 0.72f), RoundedCornerShape(10.dp))
            .border(1.dp, BuyWiseTheme.colors.border.copy(alpha = 0.72f), RoundedCornerShape(10.dp))
            .padding(horizontal = 12.dp, vertical = 10.dp),
        verticalArrangement = Arrangement.spacedBy(3.dp),
    ) {
        Text(label, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.labelMedium)
        Text(
            value,
            color = BuyWiseTheme.colors.ink,
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
        )
    }
}

@Composable
private fun PreferenceSegmentCard(
    title: String,
    description: String,
    icon: ImageVector,
    options: List<PreferenceOption>,
    selected: String,
    enabled: Boolean,
    onSelect: (String) -> Unit,
) {
    FloatingGlassCard(
        tone = FloatingGlassTone.Neutral,
        radius = BuyWiseDimens.CardRadius.dp,
        elevated = false,
        contentPadding = 16.dp,
    ) {
        PreferenceCardHeader(title = title, description = description, icon = icon)
        Spacer(Modifier.height(12.dp))
        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            options.forEach { option ->
                PreferenceSegmentButton(
                    option = option,
                    selected = selected == option.value,
                    enabled = enabled,
                    onClick = { onSelect(option.value) },
                )
            }
        }
    }
}

@Composable
private fun BundleBudgetCard(
    value: String,
    budgetPolicy: String,
    enabled: Boolean,
    onValueChange: (String) -> Unit,
) {
    FloatingGlassCard(
        tone = FloatingGlassTone.Neutral,
        radius = BuyWiseDimens.CardRadius.dp,
        elevated = false,
        contentPadding = 16.dp,
    ) {
        PreferenceCardHeader(
            title = "整套方案预算",
            description = "用户提出配齐一整套电脑或开学好物时，AI 会按这个上限生成方案。",
            icon = BuyWiseIcons.Shopping,
        )
        Spacer(Modifier.height(12.dp))
        OutlinedTextField(
            value = value,
            onValueChange = onValueChange,
            modifier = Modifier.fillMaxWidth(),
            enabled = enabled,
            label = { Text("预算上限") },
            prefix = { Text("¥") },
            singleLine = true,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
        )
        Spacer(Modifier.height(8.dp))
        val helper = if (budgetPolicy == "strict") {
            "严格预算下，超出预算的组合会降级或被排除。"
        } else {
            "允许小幅超预算时，超出 5%-10% 的原因会在方案中标红说明。"
        }
        Text(helper, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.labelMedium)
    }
}

@Composable
private fun PreferenceTagCard(
    title: String,
    description: String,
    icon: ImageVector,
    options: List<String>,
    selected: List<String>,
    enabled: Boolean,
    tone: PreferenceTagTone,
    onToggle: (String) -> Unit,
) {
    FloatingGlassCard(
        tone = FloatingGlassTone.Neutral,
        radius = BuyWiseDimens.CardRadius.dp,
        elevated = false,
        contentPadding = 16.dp,
    ) {
        PreferenceCardHeader(title = title, description = description, icon = icon)
        Spacer(Modifier.height(12.dp))
        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            options.forEach { label ->
                PreferenceTag(
                    label = label,
                    selected = label in selected,
                    enabled = enabled,
                    tone = tone,
                    onClick = { onToggle(label) },
                )
            }
        }
    }
}

@Composable
private fun PreferenceResetCard(enabled: Boolean, onClear: () -> Unit) {
    FloatingGlassCard(
        tone = FloatingGlassTone.Warm,
        radius = BuyWiseDimens.CardRadius.dp,
        elevated = false,
        contentPadding = 16.dp,
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(BuyWiseIcons.Security, contentDescription = null, tint = BuyWiseTheme.colors.accent)
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text("偏好数据", style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
                Text("清除后，下一次导购会回到默认预算和输出风格。", color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
            }
            OutlinedButton(onClick = onClear, enabled = enabled) {
                Icon(BuyWiseIcons.Clear, contentDescription = null)
                Spacer(Modifier.width(6.dp))
                Text("清除")
            }
        }
    }
}

@Composable
private fun PreferenceCardHeader(title: String, description: String, icon: ImageVector) {
    Row(horizontalArrangement = Arrangement.spacedBy(10.dp), verticalAlignment = Alignment.Top) {
        Icon(icon, contentDescription = null, modifier = Modifier.size(22.dp), tint = BuyWiseTheme.colors.primary)
        Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(title, style = MaterialTheme.typography.titleMedium, color = BuyWiseTheme.colors.ink)
            Text(description, color = BuyWiseTheme.colors.muted, style = MaterialTheme.typography.bodyMedium)
        }
    }
}

@Composable
private fun PreferenceSegmentButton(
    option: PreferenceOption,
    selected: Boolean,
    enabled: Boolean,
    onClick: () -> Unit,
) {
    val shape = RoundedCornerShape(10.dp)
    val background = when {
        selected -> BuyWiseTheme.colors.primarySoft
        else -> BuyWiseTheme.colors.panel
    }
    val border = if (selected) BuyWiseTheme.colors.primary else BuyWiseTheme.colors.border
    val titleColor = when {
        !enabled -> BuyWiseTheme.colors.muted.copy(alpha = 0.7f)
        selected -> BuyWiseTheme.colors.primary
        else -> BuyWiseTheme.colors.ink
    }
    val bodyColor = if (enabled) BuyWiseTheme.colors.muted else BuyWiseTheme.colors.muted.copy(alpha = 0.7f)
    Column(
        modifier = Modifier
            .defaultMinSize(minWidth = 104.dp, minHeight = 64.dp)
            .background(background, shape)
            .border(1.dp, border, shape)
            .clickable(enabled = enabled, onClick = onClick)
            .padding(horizontal = 12.dp, vertical = 10.dp),
        verticalArrangement = Arrangement.spacedBy(3.dp),
    ) {
        Text(option.label, color = titleColor, style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.Bold)
        Text(option.caption, color = bodyColor, style = MaterialTheme.typography.labelMedium)
    }
}

@Composable
private fun PreferenceTag(
    label: String,
    selected: Boolean,
    enabled: Boolean,
    tone: PreferenceTagTone,
    onClick: () -> Unit,
) {
    val shape = RoundedCornerShape(BuyWiseDimens.ChipRadius.dp)
    val selectedBackground = when (tone) {
        PreferenceTagTone.Positive -> BuyWiseTheme.colors.secondarySoft
        PreferenceTagTone.Warning -> BuyWiseTheme.colors.accentSoft
        PreferenceTagTone.Neutral -> BuyWiseTheme.colors.primarySoft
    }
    val selectedText = when (tone) {
        PreferenceTagTone.Positive -> BuyWiseTheme.colors.secondary
        PreferenceTagTone.Warning -> BuyWiseTheme.colors.accent
        PreferenceTagTone.Neutral -> BuyWiseTheme.colors.primary
    }
    val background = if (selected) selectedBackground else BuyWiseTheme.colors.panel
    val foreground = when {
        !enabled -> BuyWiseTheme.colors.muted.copy(alpha = 0.7f)
        selected -> selectedText
        else -> BuyWiseTheme.colors.ink
    }
    val border = if (selected) selectedText.copy(alpha = 0.55f) else BuyWiseTheme.colors.border
    Text(
        label,
        modifier = Modifier
            .defaultMinSize(minHeight = 40.dp)
            .background(background, shape)
            .border(1.dp, border, shape)
            .clickable(enabled = enabled, onClick = onClick)
            .padding(horizontal = 12.dp, vertical = 9.dp),
        color = foreground,
        style = MaterialTheme.typography.labelMedium,
        fontWeight = FontWeight.Bold,
    )
}

private data class PreferenceOption(
    val value: String,
    val label: String,
    val caption: String,
)

private enum class PreferenceTagTone {
    Positive,
    Warning,
    Neutral,
}

private fun budgetPolicyLabel(value: String): String = when (value) {
    "strict" -> "严格预算"
    "quality_first" -> "品质优先"
    else -> "小幅超预算"
}
