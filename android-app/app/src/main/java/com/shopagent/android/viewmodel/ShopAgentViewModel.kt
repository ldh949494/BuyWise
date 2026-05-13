package com.shopagent.android.viewmodel

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import com.shopagent.android.data.CompareState
import com.shopagent.android.data.GuideState
import com.shopagent.android.data.HomeState
import com.shopagent.android.data.Product
import com.shopagent.android.data.ShopRepository
import com.shopagent.android.data.VisionState

class ShopAgentViewModel(
    private val repository: ShopRepository = ShopRepository(),
) : ViewModel() {
    val homeState: HomeState = repository.homeState()
    val compareState: CompareState = repository.compareState()
    val visionState: VisionState = repository.visionState()

    var guideState by mutableStateOf(repository.guideState(""))
        private set

    fun updateGuideQuery(query: String) {
        guideState = guideState.copy(query = query)
    }

    fun submitGuideQuery() {
        guideState = repository.guideState(guideState.query)
    }

    fun product(productId: String?): Product? = repository.product(productId)
}
