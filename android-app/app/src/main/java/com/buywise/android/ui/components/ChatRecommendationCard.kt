package com.buywise.android.ui.components

import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.buywise.android.data.Recommendation
import com.buywise.android.ui.BuyWiseTheme
import com.buywise.android.ui.displayPrice

@Composable
fun ChatRecommendationCard(recommendation: Recommendation, onClick: () -> Unit, modifier: Modifier = Modifier) {
    val product = recommendation.product
    FloatingGlassCard(
        modifier = modifier.width(148.dp),
        tone = FloatingGlassTone.Primary,
        radius = 16.dp,
        fillMaxWidth = false,
        contentPadding = 10.dp,
        onClick = onClick,
    ) {
        ProductImagePreview(product = product, modifier = Modifier.size(54.dp))
        Text(
            product.name,
            color = BuyWiseTheme.colors.ink,
            fontWeight = FontWeight.Bold,
            maxLines = 2,
            overflow = TextOverflow.Ellipsis,
        )
        Text(
            product.price.displayPrice(),
            color = BuyWiseTheme.colors.primary,
            fontWeight = FontWeight.Bold,
            style = MaterialTheme.typography.bodyMedium,
        )
    }
}
