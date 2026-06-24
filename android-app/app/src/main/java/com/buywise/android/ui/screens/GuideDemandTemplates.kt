package com.buywise.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.buywise.android.ui.BuyWiseDimens
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.components.FloatingGlassCard
import com.buywise.android.ui.components.FloatingGlassTone
import java.time.LocalDate
import kotlin.random.Random

@Composable
internal fun DemandTemplateRow(onTemplateClick: (String) -> Unit) {
    val templates = demandTemplatesForDate()
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        templates.forEach { template ->
            FloatingGlassCard(
                tone = FloatingGlassTone.Neutral,
                radius = 12.dp,
                fillMaxWidth = false,
                contentPadding = 0.dp,
                onClick = { onTemplateClick(template.query) },
            ) {
                Text(
                    template.label,
                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 10.dp),
                    color = BuyWiseTheme.colors.ink,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                )
            }
        }
    }
}

private data class DemandTemplate(val label: String, val query: String)

private val DailyDemandTemplatePool = listOf(
    DemandTemplate("宿舍低噪键盘", "宿舍写代码用，预算300以内，想要低噪音机械键盘，最好便于收纳。"),
    DemandTemplate("通勤降噪耳机", "通勤和办公室都能用，预算500以内，想要降噪好、佩戴舒服的耳机。"),
    DemandTemplate("办公显示器", "日常办公和轻度修图，预算1000以内，想要护眼、接口方便的显示器。"),
    DemandTemplate("厨房小家电", "租房做饭用，预算400以内，想要容易清洗、占地小的空气炸锅或电煮锅。"),
    DemandTemplate("旅行充电宝", "短途旅行用，预算200以内，想要轻便、容量够两天、可以给手机快充的充电宝。"),
    DemandTemplate("学生护眼台灯", "晚上学习用，预算300以内，想要护眼、亮度稳定、桌面占用小的台灯。"),
    DemandTemplate("猫毛清洁机", "家里有猫，预算800以内，想要吸猫毛效果好、噪音低、维护方便的吸尘器。"),
    DemandTemplate("通勤双肩包", "日常通勤背电脑，预算500以内，想要轻便、防泼水、分区合理的双肩包。"),
    DemandTemplate("健身智能表", "跑步和力量训练用，预算1000以内，想要续航好、心率记录准、佩戴舒服的智能手表。"),
    DemandTemplate("卧室投影仪", "卧室看电影用，预算1500以内，想要画面清楚、噪音低、自动校正方便的投影仪。"),
    DemandTemplate("便携咖啡杯", "办公室和通勤用，预算200以内，想要保温好、不漏水、容易清洗的咖啡杯。"),
    DemandTemplate("儿童学习平板", "小学孩子学习用，预算1500以内，想要护眼、内容可控、家长管理方便的学习平板。"),
)

private fun demandTemplatesForDate(date: LocalDate = LocalDate.now()): List<DemandTemplate> =
    DailyDemandTemplatePool.shuffled(Random(date.toEpochDay())).take(3)
