import 'dart:convert';

import 'package:http/http.dart' as http;

class ApiClient {
  ApiClient({this.baseUrl = 'http://localhost:8000'});

  final String baseUrl;

  Future<dynamic> get(String path) async {
    final response = await http.get(Uri.parse('$baseUrl$path')).timeout(const Duration(seconds: 2));
    if (response.statusCode >= 400) throw Exception(response.body);
    return jsonDecode(utf8.decode(response.bodyBytes));
  }

  Future<dynamic> post(String path, Map<String, dynamic> body) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl$path'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(body),
        )
        .timeout(const Duration(seconds: 2));
    if (response.statusCode >= 400) throw Exception(response.body);
    return jsonDecode(utf8.decode(response.bodyBytes));
  }
}
