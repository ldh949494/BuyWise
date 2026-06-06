package com.buywise.android.data

import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject

class GuidePreferencesRepository internal constructor(
    private val apiClient: BuyWiseApiClient,
) {
    fun load(): GuidePreferences {
        return parseGuidePreferences(apiClient.getJson("/api/v1/guide/preferences", requireAuth = true))
    }

    fun save(preferences: GuidePreferences): GuidePreferences {
        val body = preferences.toJson().toString().toRequestBody(mediaType("application/json; charset=utf-8"))
        return parseGuidePreferences(apiClient.putJson("/api/v1/guide/preferences", body, requireAuth = true))
    }

    fun clear() {
        apiClient.delete("/api/v1/guide/preferences", requireAuth = true)
    }
}

internal fun parseGuidePreferences(json: JSONObject?): GuidePreferences {
    if (json == null) return GuidePreferences()
    return GuidePreferences(
        budgetPolicy = json.optString("budget_policy", "slightly_flexible"),
        presentationStyle = json.optString("presentation_style", "compare_options"),
        singleItemBudgets = parseBudgetMap(json.optJSONObject("single_item_budgets")),
        bundleBudgetRange = parseBudgetRange(json.optJSONObject("bundle_budget_range")),
        priorityTags = json.optJSONArray("priority_tags").toGuideStringList(),
        excludedTags = json.optJSONArray("excluded_tags").toGuideStringList(),
        excludedBrands = json.optJSONArray("excluded_brands").toGuideStringList(),
        ownedCategories = json.optJSONArray("owned_categories").toGuideStringList(),
        extraNotes = json.optGuideStringOrNull("extra_notes"),
        hasSavedPreferences = json.optBoolean("has_saved_preferences", false),
    )
}

internal fun parseAppliedPreferences(json: JSONObject?): AppliedPreferences {
    if (json == null) return AppliedPreferences()
    val constraints = json.optJSONArray("constraints")
    return AppliedPreferences(
        usedSavedPreferences = json.optBoolean("used_saved_preferences", false),
        ignoredSavedPreferences = json.optBoolean("ignored_saved_preferences", false),
        budgetPolicy = json.optGuideStringOrNull("budget_policy"),
        presentationStyle = json.optGuideStringOrNull("presentation_style"),
        summary = json.optJSONArray("summary").toGuideStringList(),
        constraints = (0 until (constraints?.length() ?: 0)).mapNotNull { index ->
            constraints?.optJSONObject(index)?.let {
                AppliedPreferenceConstraint(
                    type = it.optString("type"),
                    key = it.optString("key"),
                    label = it.optString("label"),
                    effect = it.optString("effect"),
                )
            }
        },
    )
}

internal fun GuidePreferences.toJson(): JSONObject {
    return JSONObject()
        .put("budget_policy", budgetPolicy)
        .put("presentation_style", presentationStyle)
        .put("single_item_budgets", JSONObject().also { root ->
            singleItemBudgets.forEach { (category, range) -> root.put(category, range.toJson()) }
        })
        .put("bundle_budget_range", bundleBudgetRange?.toJson())
        .put("priority_tags", priorityTags.toJsonArray())
        .put("excluded_tags", excludedTags.toJsonArray())
        .put("excluded_brands", excludedBrands.toJsonArray())
        .put("owned_categories", ownedCategories.toJsonArray())
        .put("extra_notes", extraNotes)
}

private fun BudgetRange.toJson(): JSONObject =
    JSONObject().put("min", min).put("max", max)

private fun parseBudgetMap(json: JSONObject?): Map<String, BudgetRange> {
    if (json == null) return emptyMap()
    return json.keys().asSequence().associateWith { key -> parseBudgetRange(json.optJSONObject(key)) ?: BudgetRange() }
}

private fun parseBudgetRange(json: JSONObject?): BudgetRange? {
    if (json == null) return null
    return BudgetRange(min = json.optGuideDoubleOrNull("min"), max = json.optGuideDoubleOrNull("max"))
}

private fun List<String>.toJsonArray(): JSONArray {
    val array = JSONArray()
    forEach { array.put(it) }
    return array
}

private fun JSONArray?.toGuideStringList(): List<String> {
    if (this == null) return emptyList()
    return (0 until length()).mapNotNull { index -> optString(index).takeIf { it.isNotBlank() } }
}

private fun JSONObject.optGuideStringOrNull(name: String): String? =
    if (has(name) && !isNull(name)) optString(name).takeIf { it.isNotBlank() } else null

private fun JSONObject.optGuideDoubleOrNull(name: String): Double? =
    if (has(name) && !isNull(name)) optDouble(name) else null
