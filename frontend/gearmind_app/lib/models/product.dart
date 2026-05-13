class Product {
  const Product({
    required this.id,
    required this.name,
    required this.brand,
    required this.category,
    required this.price,
    required this.rating,
    required this.sales,
    required this.imageUrl,
    required this.tags,
    required this.description,
    required this.specs,
    required this.pros,
    required this.cons,
    required this.recommendedFor,
    required this.notRecommendedFor,
    required this.reviewSummary,
    required this.matchScore,
  });

  final String id;
  final String name;
  final String brand;
  final String category;
  final double price;
  final double rating;
  final int sales;
  final String imageUrl;
  final List<String> tags;
  final String description;
  final Map<String, dynamic> specs;
  final List<String> pros;
  final List<String> cons;
  final List<String> recommendedFor;
  final List<String> notRecommendedFor;
  final String reviewSummary;
  final int matchScore;

  factory Product.fromJson(Map<String, dynamic> json) {
    List<String> strings(String key) =>
        (json[key] as List<dynamic>? ?? const []).map((e) => '$e').toList();
    return Product(
      id: json['id'] as String,
      name: json['name'] as String,
      brand: json['brand'] as String,
      category: json['category'] as String,
      price: (json['price'] as num).toDouble(),
      rating: (json['rating'] as num).toDouble(),
      sales: (json['sales'] as num).toInt(),
      imageUrl: json['image_url'] as String? ?? json['imageUrl'] as String,
      tags: strings('tags'),
      description: json['description'] as String,
      specs: Map<String, dynamic>.from(json['specs'] as Map? ?? const {}),
      pros: strings('pros'),
      cons: strings('cons'),
      recommendedFor: strings('recommended_for'),
      notRecommendedFor: strings('not_recommended_for'),
      reviewSummary: json['review_summary'] as String,
      matchScore: (json['match_score'] as num).toInt(),
    );
  }
}
