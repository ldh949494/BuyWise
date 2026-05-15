package com.buywise.android.viewmodel

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import com.buywise.android.data.CompareState
import com.buywise.android.data.GuideState
import com.buywise.android.data.HomeState
import com.buywise.android.data.Product
import com.buywise.android.data.ShopRepository
import com.buywise.android.data.VisionState

class BuyWiseViewModel(
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
