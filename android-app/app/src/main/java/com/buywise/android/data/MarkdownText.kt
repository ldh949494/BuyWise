package com.buywise.android.data

internal fun String.cleanMarkdownText(): String =
    replace(Regex("""\[([^]]+)]\([^)]+\)"""), "$1")
        .replace(Regex("""`([^`]+)`"""), "$1")
        .replace(Regex("""[*_~]{1,3}([^*_~]+)[*_~]{1,3}"""), "$1")
        .lines()
        .map { line -> line.cleanMarkdownLine() }
        .filter { it.isNotBlank() }
        .joinToString(" ")
        .replace(Regex("""\s+"""), " ")
        .trim()

internal fun List<String>.cleanMarkdownTextList(): List<String> =
    map { it.cleanMarkdownText() }.filter { it.isNotBlank() }

private fun String.cleanMarkdownLine(): String =
    trim()
        .removePrefix(">")
        .trim()
        .replace(Regex("""^#{1,6}\s*"""), "")
        .replace(Regex("""^[-*+]\s+"""), "")
        .replace(Regex("""^\d+[.)]\s+"""), "")
