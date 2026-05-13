import 'package:flutter/material.dart';

import 'pages/agent_guide_page.dart';
import 'pages/compare_page.dart';
import 'pages/home_page.dart';
import 'pages/image_recognition_page.dart';
import 'pages/product_detail_page.dart';
import 'theme/app_theme.dart';

class GearMindApp extends StatelessWidget {
  const GearMindApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'GearMind Agent',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      initialRoute: '/',
      routes: {
        '/': (_) => const HomePage(),
        '/agent': (_) => const AgentGuidePage(),
        '/compare': (_) => const ComparePage(),
        '/image-recognition': (_) => const ImageRecognitionPage(),
      },
      onGenerateRoute: (settings) {
        if (settings.name?.startsWith('/product/') ?? false) {
          final id = settings.name!.split('/').last;
          return MaterialPageRoute(builder: (_) => ProductDetailPage(productId: id));
        }
        return null;
      },
    );
  }
}
