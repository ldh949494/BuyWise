import 'product.dart';

class CompareResult {
  const CompareResult({
    required this.products,
    required this.table,
    required this.summary,
    required this.finalRecommendation,
  });

  final List<Product> products;
  final Map<String, Map<String, dynamic>> table;
  final String summary;
  final String finalRecommendation;

  factory CompareResult.fromJson(Map<String, dynamic> json) {
    final rawTable = Map<String, dynamic>.from(json['table'] as Map? ?? const {});
    return CompareResult(
      products: (json['products'] as List<dynamic>? ?? const [])
          .map((e) => Product.fromJson(e as Map<String, dynamic>))
          .toList(),
      table: rawTable.map(
        (key, value) => MapEntry(key, Map<String, dynamic>.from(value as Map)),
      ),
      summary: json['summary'] as String,
      finalRecommendation: json['final_recommendation'] as String,
    );
  }
}
