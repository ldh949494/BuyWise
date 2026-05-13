import '../mock/mock_products.dart';
import '../models/agent_recommendation.dart';
import '../models/compare_result.dart';
import 'api_client.dart';

class AgentApi {
  AgentApi({ApiClient? client}) : _client = client ?? ApiClient();

  final ApiClient _client;

  Future<AgentResponse> recommend(String query) async {
    try {
      final data = await _client.post('/api/agent/recommend', {
        'query': query,
        'filters': {'category': 'mouse', 'max_price': 300}
      }) as Map<String, dynamic>;
      return AgentResponse.fromJson(data);
    } catch (_) {
      return mockAgentResponse();
    }
  }

  Future<CompareResult> compare(List<String> ids) async {
    try {
      final data = await _client.post('/api/compare', {'product_ids': ids}) as Map<String, dynamic>;
      return CompareResult.fromJson(data);
    } catch (_) {
      return mockCompareResult();
    }
  }

  Future<Map<String, dynamic>> recognizeMock() async {
    try {
      return await _client.post('/api/image-recognition/mock', {}) as Map<String, dynamic>;
    } catch (_) {
      return {
        'recognized_product': findMockProduct('k001'),
        'confidence': 92,
        'labels': ['75%配列', 'Gasket结构', '客制化机械键盘', 'PBT键帽'],
        'similar_products': mockProducts.where((p) => p.category == 'keyboard').skip(1).take(6).toList(),
        'summary': '这是一款 75% 配列的客制化机械键盘，适合桌搭和电竞氛围。',
      };
    }
  }
}
