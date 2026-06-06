package com.buywise.android.ui.screens

import com.buywise.android.data.AppliedPreferences

internal fun guidePreferenceSummaryText(appliedPreferences: AppliedPreferences, ignoreSavedPreferences: Boolean): String {
    if (ignoreSavedPreferences || appliedPreferences.ignoredSavedPreferences) {
        return "本次未使用长期导购偏好"
    }
    val summary = appliedPreferences.summary.take(3)
    if (summary.isEmpty()) {
        return "本次会优先使用已保存的导购偏好"
    }
    return "已按导购偏好：" + summary.joinToString("、")
}
