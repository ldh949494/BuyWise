import 'product.dart';

class AgentRecommendation {
  const AgentRecommendation({
    required this.product,
    required this.matchScore,
    required this.reason,
  });

  final Product product;
  final int matchScore;
  final String reason;

  factory AgentRecommendation.fromJson(Map<String, dynamic> json) {
    return AgentRecommendation(
      product: Product.fromJson(json['product'] as Map<String, dynamic>),
      matchScore: (json['match_score'] as num).toInt(),
      reason: json['reason'] as String,
    );
  }
}

class AgentResponse {
  const AgentResponse({
    required this.intent,
    required this.recommendations,
    required this.summary,
    required this.pitfalls,
  });

  final Map<String, dynamic> intent;
  final List<AgentRecommendation> recommendations;
  final String summary;
  final List<String> pitfalls;

  factory AgentResponse.fromJson(Map<String, dynamic> json) {
    return AgentResponse(
      intent: Map<String, dynamic>.from(json['intent'] as Map? ?? const {}),
      recommendations: (json['recommendations'] as List<dynamic>? ?? const [])
          .map((e) => AgentRecommendation.fromJson(e as Map<String, dynamic>))
          .toList(),
      summary: json['summary'] as String,
      pitfalls:
          (json['pitfalls'] as List<dynamic>? ?? const []).map((e) => '$e').toList(),
    );
  }
}
