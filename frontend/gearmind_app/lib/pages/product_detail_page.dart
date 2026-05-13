import 'package:flutter/material.dart';

import '../models/product.dart';
import '../services/product_api.dart';
import '../theme/app_theme.dart';
import '../widgets/app_nav_bar.dart';
import '../widgets/match_score_badge.dart';
import '../widgets/tag_chip.dart';

class ProductDetailPage extends StatelessWidget {
  const ProductDetailPage({super.key, required this.productId});

  final String productId;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const AppNavBar(),
      body: FutureBuilder<Product>(
        future: ProductApi().getProduct(productId),
        builder: (context, snapshot) {
          final p = snapshot.data;
          if (p == null) return const Center(child: CircularProgressIndicator());
          return SingleChildScrollView(
            padding: const EdgeInsets.all(28),
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 1320),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Expanded(child: _Gallery(product: p)),
                      const SizedBox(width: 28),
                      Expanded(child: _BuyPanel(product: p)),
                    ]),
                    const SizedBox(height: 26),
                    Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Expanded(flex: 2, child: _DeepAnalysis(product: p)),
                      const SizedBox(width: 22),
                      Expanded(child: _AudiencePanel(product: p)),
                    ]),
                    const SizedBox(height: 26),
                    _Bundle(product: p),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

class _Gallery extends StatelessWidget {
  const _Gallery({required this.product});
  final Product product;
  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(children: [
          ClipRRect(borderRadius: BorderRadius.circular(20), child: Image.network(product.imageUrl, height: 430, width: double.infinity, fit: BoxFit.cover)),
          const SizedBox(height: 14),
          Row(children: List.generate(4, (i) => Expanded(child: Container(margin: EdgeInsets.only(right: i == 3 ? 0 : 12), height: 88, decoration: BoxDecoration(borderRadius: BorderRadius.circular(14), border: Border.all(color: i == 0 ? AppTheme.primary : AppTheme.line), image: DecorationImage(image: NetworkImage(product.imageUrl), fit: BoxFit.cover)))))),
        ]),
      ),
    );
  }
}

class _BuyPanel extends StatelessWidget {
  const _BuyPanel({required this.product});
  final Product product;
  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(product.name, style: const TextStyle(fontSize: 30, fontWeight: FontWeight.w900, color: AppTheme.ink)),
          const SizedBox(height: 10),
          Text(product.description, style: const TextStyle(color: AppTheme.muted, height: 1.6)),
          const SizedBox(height: 18),
          Row(children: [Text('￥${product.price.toStringAsFixed(0)}', style: const TextStyle(fontSize: 30, fontWeight: FontWeight.w900)), const SizedBox(width: 18), const Icon(Icons.star, color: Color(0xFFFF9D18)), Text('${product.rating}  ${product.sales}+ 销量', style: const TextStyle(color: AppTheme.muted))]),
          const SizedBox(height: 16),
          Wrap(spacing: 8, runSpacing: 8, children: product.tags.map((e) => TagChip(e, soft: true)).toList()),
          const SizedBox(height: 24),
          Row(children: [
            Expanded(child: FilledButton.icon(onPressed: () {}, icon: const Icon(Icons.shopping_cart_outlined), label: const Text('加入购物车'))),
            const SizedBox(width: 12),
            Expanded(child: FilledButton.icon(onPressed: () {}, icon: const Icon(Icons.flash_on), label: const Text('立即购买'))),
            const SizedBox(width: 12),
            IconButton.filledTonal(onPressed: () {}, icon: const Icon(Icons.favorite_border)),
          ]),
          const SizedBox(height: 14),
          OutlinedButton.icon(onPressed: () => Navigator.pushNamed(context, '/compare'), icon: const Icon(Icons.compare_arrows), label: const Text('加入对比')),
          const Divider(height: 34),
          Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(color: const Color(0xFFF3F5FF), borderRadius: BorderRadius.circular(18)),
            child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              MatchScoreBadge(score: product.matchScore, size: 82),
              const SizedBox(width: 18),
              Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Text('AI 购买建议', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900)),
                const SizedBox(height: 8),
                Text('推荐购买指数 ${product.matchScore}/100。适合 ${product.recommendedFor.take(3).join('、')}。', style: const TextStyle(height: 1.6)),
                const SizedBox(height: 8),
                Text('不足：${product.cons.take(2).join('、')}。', style: const TextStyle(color: AppTheme.muted, height: 1.5)),
              ])),
            ]),
          )
        ]),
      ),
    );
  }
}

class _DeepAnalysis extends StatelessWidget {
  const _DeepAnalysis({required this.product});
  final Product product;
  @override
  Widget build(BuildContext context) {
    final blocks = [
      ('性能表现', '核心参数覆盖当前电竞外设主流水平，适合高频操作和低延迟场景。'),
      ('手感体验', '模具和重量适合较长时间游戏，具体还要结合手型与握法。'),
      ('性价比', '同价位配置完整，优先满足性能和实用性。'),
      ('适用场景', product.recommendedFor.join(' / ')),
    ];
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('AI 深度分析', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w900)),
          const SizedBox(height: 16),
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            childAspectRatio: 2.2,
            crossAxisSpacing: 14,
            mainAxisSpacing: 14,
            children: blocks
                .map(
                  (e) => Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: const Color(0xFFF7F8FC),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: AppTheme.line),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(e.$1, style: const TextStyle(fontWeight: FontWeight.w900)),
                        const SizedBox(height: 8),
                        Text(e.$2, style: const TextStyle(color: AppTheme.muted, height: 1.5)),
                      ],
                    ),
                  ),
                )
                .toList(),
          ),
          const SizedBox(height: 20),
          const Text('用户评价总结', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900)),
          const SizedBox(height: 8),
          Text(product.reviewSummary, style: const TextStyle(height: 1.7)),
        ]),
      ),
    );
  }
}

class _AudiencePanel extends StatelessWidget {
  const _AudiencePanel({required this.product});
  final Product product;
  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(22),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('适合用户群体', style: TextStyle(fontWeight: FontWeight.w900, fontSize: 18)),
          const SizedBox(height: 10),
          ...product.recommendedFor.map((e) => ListTile(leading: const Icon(Icons.check_circle, color: AppTheme.primary), title: Text(e))),
          const Divider(height: 28),
          const Text('不适合用户群体', style: TextStyle(fontWeight: FontWeight.w900, fontSize: 18)),
          const SizedBox(height: 10),
          ...product.notRecommendedFor.map((e) => ListTile(leading: const Icon(Icons.info_outline, color: AppTheme.muted), title: Text(e))),
        ]),
      ),
    );
  }
}

class _Bundle extends StatelessWidget {
  const _Bundle({required this.product});
  final Product product;
  @override
  Widget build(BuildContext context) {
    final items = product.category == 'mouse' ? ['4K接收器', '鼠标脚贴', '控制型鼠标垫'] : ['定制键帽', '静音轴体', '桌垫'];
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(22),
        child: Row(children: [
          const Text('搭配推荐', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900)),
          const SizedBox(width: 20),
          ...items.map((e) => Expanded(child: Container(margin: const EdgeInsets.only(right: 12), padding: const EdgeInsets.all(18), decoration: BoxDecoration(color: const Color(0xFFF7F8FC), borderRadius: BorderRadius.circular(16)), child: Row(children: [const Icon(Icons.add_box_outlined, color: AppTheme.primary), const SizedBox(width: 10), Text(e, style: const TextStyle(fontWeight: FontWeight.w800))])))),
        ]),
      ),
    );
  }
}
