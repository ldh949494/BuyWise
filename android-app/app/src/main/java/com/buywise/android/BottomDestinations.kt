package com.buywise.android

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.CompareArrows
import androidx.compose.material.icons.outlined.Home
import androidx.compose.material.icons.outlined.ImageSearch
import androidx.compose.material.icons.outlined.Person
import androidx.compose.material.icons.outlined.SmartToy
import androidx.compose.material3.Icon
import androidx.compose.runtime.Composable

internal data class BottomDestination(
    val route: String,
    val label: String,
    val icon: @Composable () -> Unit,
)

internal fun bottomDestinations(): List<BottomDestination> =
    listOf(
        BottomDestination("home", "首页") { Icon(Icons.Outlined.Home, contentDescription = null) },
        BottomDestination("guide", "导购") { Icon(Icons.Outlined.SmartToy, contentDescription = null) },
        BottomDestination("compare", "对比") { Icon(Icons.AutoMirrored.Outlined.CompareArrows, contentDescription = null) },
        BottomDestination("vision", "识图") { Icon(Icons.Outlined.ImageSearch, contentDescription = null) },
        BottomDestination("account", "我的") { Icon(Icons.Outlined.Person, contentDescription = null) },
    )
