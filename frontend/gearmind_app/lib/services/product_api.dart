import '../mock/mock_products.dart';
import '../models/product.dart';
import 'api_client.dart';

class ProductApi {
  ProductApi({ApiClient? client}) : _client = client ?? ApiClient();

  final ApiClient _client;

  Future<List<Product>> listProducts({String? category}) async {
    try {
      final path = category == null ? '/api/products' : '/api/products?category=$category';
      final data = await _client.get(path) as List<dynamic>;
      return data.map((e) => Product.fromJson(e as Map<String, dynamic>)).toList();
    } catch (_) {
      return category == null ? mockProducts : mockProducts.where((p) => p.category == category).toList();
    }
  }

  Future<Product> getProduct(String id) async {
    try {
      final data = await _client.get('/api/products/$id') as Map<String, dynamic>;
      return Product.fromJson(data);
    } catch (_) {
      return findMockProduct(id);
    }
  }
}
