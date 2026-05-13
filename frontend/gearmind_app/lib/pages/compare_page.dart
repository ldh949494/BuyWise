import 'package:flutter/material.dart';

import '../models/compare_result.dart';
import '../services/agent_api.dart';
import '../theme/app_theme.dart';
import '../widgets/app_nav_bar.dart';
import '../widgets/compare_table.dart';
import '../widgets/tag_chip.dart';

class ComparePage extends StatelessWidget {
  const ComparePage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const AppNavBar(),
      body: FutureBuilder<CompareResult>(
        future: AgentApi().compare(const ['k003', 'k004', 'k005']),
        builder: (context, snapshot) {
          final result = snapshot.data;
          if (result == null) return const Center(child: CircularProgressIndicator());
          return SingleChildScrollView(
            padding: const EdgeInsets.all(28),
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 1500),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('商品对比', style: TextStyle(fontSize: 32, fontWeight: FontWeight.w900, color: AppTheme.ink)),
                    const SizedBox(height: 8),
                    const Text('AI 辅助你从参数、场景和短板里找到更稳的选择', style: TextStyle(color: AppTheme.muted)),
                    const SizedBox(height: 20),
                    _SelectedProducts(result: result),
                    const SizedBox(height: 18),
                    Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Expanded(flex: 4, child: CompareTable(result: result)),
                      const SizedBox(width: 18),
                      Expanded(child: _Summary(result: result)),
                    ]),
                    const SizedBox(height: 18),
                    _FinalRecommendation(result: result),
                    const SizedBox(height: 18),
                    Row(children: [
                      OutlinedButton.icon(onPressed: () {}, icon: const Icon(Icons.tune), label: const Text('重新筛选对比')),
                      const SizedBox(width: 12),
                      OutlinedButton.icon(onPressed: () {}, icon: const Icon(Icons.description_outlined), label: const Text('生成对比报告')),
                      const SizedBox(width: 12),
                      FilledButton.icon(onPressed: () => Navigator.pushNamed(context, '/agent'), icon: const Icon(Icons.smart_toy_outlined), label: const Text('去 AI 导购问问')),
                    ])
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

class _SelectedProducts extends StatelessWidget {
  const _SelectedProducts({required this.result});
  final CompareResult result;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Row(
          children: [
            ...result.products.asMap().entries.map((entry) {
              final p = entry.value;
              return Expanded(
                child: Container(
                  margin: const EdgeInsets.only(right: 14),
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(color: const Color(0xFFF7F8FC), borderRadius: BorderRadius.circular(16), border: Border.all(color: AppTheme.line)),
                  child: Row(children: [
                    TagChip('${entry.key + 1}', soft: true),
                    const SizedBox(width: 12),
                    ClipRRect(borderRadius: BorderRadius.circular(12), child: Image.network(p.imageUrl, width: 82, height: 82, fit: BoxFit.cover)),
                    const SizedBox(width: 14),
                    Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(p.name, style: const TextStyle(fontWeight: FontWeight.w900)), const SizedBox(height: 8), Text('￥${p.price.toStringAsFixed(0)}  ·  ${p.rating}分', style: const TextStyle(color: AppTheme.muted))])),
                    IconButton(onPressed: () {}, icon: const Icon(Icons.close, size: 18)),
                  ]),
                ),
              );
            }),
            Container(
              width: 210,
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(color: const Color(0xFFF7F8FC), borderRadius: BorderRadius.circular(16), border: Border.all(color: AppTheme.line)),
              child: const Row(mainAxisAlignment: MainAxisAlignment.center, children: [Icon(Icons.add, color: AppTheme.primary), SizedBox(width: 10), Text('添加产品', style: TextStyle(fontWeight: FontWeight.w900))]),
            )
          ],
        ),
      ),
    );
  }
}

class _Summary extends StatelessWidget {
  const _Summary({required this.result});
  final CompareResult result;

  @override
  Widget build(BuildContext context) {
    return Column(children: [
      Card(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('AI 对比总结', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900)),
            const SizedBox(height: 14),
            Container(padding: const EdgeInsets.all(16), decoration: BoxDecoration(color: const Color(0xFFF3F5FF), borderRadius: BorderRadius.circular(16)), child: Text(result.summary, style: const TextStyle(height: 1.6))),
            const SizedBox(height: 18),
            const Text('场景推荐', style: TextStyle(fontWeight: FontWeight.w900)),
            const SizedBox(height: 10),
            ...['宿舍静音：1 > 2 > 3', '办公日常：2 > 1 > 3', '游戏体验：3 > 1 > 2', '预算优先：2 > 1 > 3'].map((e) => Padding(padding: const EdgeInsets.only(bottom: 10), child: Text(e))),
          ]),
        ),
      ),
      const SizedBox(height: 14),
      Card(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('优缺点对比', style: TextStyle(fontWeight: FontWeight.w900)),
            const SizedBox(height: 12),
            ...['性能表现', '噪音控制', '连接完整度', '性价比', '品牌售后'].map((e) => Row(children: [const Icon(Icons.check, color: AppTheme.primary, size: 18), const SizedBox(width: 8), Expanded(child: Text(e)), const Text('优秀', style: TextStyle(color: AppTheme.primary))])),
          ]),
        ),
      ),
    ]);
  }
}

class _FinalRecommendation extends StatelessWidget {
  const _FinalRecommendation({required this.result});
  final CompareResult result;
  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(22),
        child: Row(children: [
          Container(width: 48, height: 48, decoration: BoxDecoration(color: AppTheme.primary.withValues(alpha: .08), borderRadius: BorderRadius.circular(14)), child: const Icon(Icons.emoji_events_outlined, color: AppTheme.primary)),
          const SizedBox(width: 16),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [const Text('底部最终推荐结论', style: TextStyle(fontWeight: FontWeight.w900, fontSize: 18)), const SizedBox(height: 6), Text(result.finalRecommendation, style: const TextStyle(color: AppTheme.muted, height: 1.5))])),
          FilledButton(onPressed: () {}, child: const Text('查看推荐商品')),
        ]),
      ),
    );
  }
}
