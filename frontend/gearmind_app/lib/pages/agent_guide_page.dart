import 'package:flutter/material.dart';

import '../models/agent_recommendation.dart';
import '../models/product.dart';
import '../services/agent_api.dart';
import '../theme/app_theme.dart';
import '../widgets/app_nav_bar.dart';
import '../widgets/match_score_badge.dart';
import '../widgets/tag_chip.dart';

class AgentGuidePage extends StatefulWidget {
  const AgentGuidePage({super.key, this.initialResponse});

  final Future<AgentResponse>? initialResponse;

  @override
  State<AgentGuidePage> createState() => _AgentGuidePageState();
}

class _AgentGuidePageState extends State<AgentGuidePage> {
  late Future<AgentResponse> _future;

  @override
  void initState() {
    super.initState();
    _future = widget.initialResponse ??
        AgentApi().recommend('预算300以内，适合FPS游戏，轻量低延迟的无线鼠标');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const AppNavBar(),
      body: LayoutBuilder(
        builder: (context, viewport) {
          final padding = viewport.maxWidth < 720 ? 16.0 : 28.0;

          return FutureBuilder<AgentResponse>(
            future: _future,
            builder: (context, snapshot) {
              final data = snapshot.data;
              if (data == null) {
                return const Center(child: CircularProgressIndicator());
              }

              return SingleChildScrollView(
                padding: EdgeInsets.all(padding),
                child: Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 1480),
                    child: _AgentGuideLayout(
                      data: data,
                      onRecommend: () => setState(() =>
                          _future = AgentApi().recommend('预算300以内 FPS 无线轻量鼠标')),
                    ),
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}

class _AgentGuideLayout extends StatelessWidget {
  const _AgentGuideLayout({required this.data, required this.onRecommend});

  final AgentResponse data;
  final VoidCallback onRecommend;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final width = constraints.maxWidth;

        if (width >= 1320) {
          return Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SizedBox(
                  width: 340, child: _LeftWorkbench(onRecommend: onRecommend)),
              const SizedBox(width: 18),
              Expanded(child: _RecommendationList(data: data)),
              const SizedBox(width: 18),
              SizedBox(width: 320, child: _AnalysisPanel(data: data)),
            ],
          );
        }

        if (width >= 920) {
          return Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SizedBox(
                  width: width < 1080 ? 310 : 340,
                  child: _LeftWorkbench(onRecommend: onRecommend)),
              const SizedBox(width: 18),
              Expanded(
                child: Column(
                  children: [
                    _RecommendationList(data: data),
                    const SizedBox(height: 18),
                    _AnalysisPanel(data: data),
                  ],
                ),
              ),
            ],
          );
        }

        return Column(
          children: [
            _LeftWorkbench(onRecommend: onRecommend),
            const SizedBox(height: 18),
            _RecommendationList(data: data),
            const SizedBox(height: 18),
            _AnalysisPanel(data: data),
          ],
        );
      },
    );
  }
}

class _LeftWorkbench extends StatelessWidget {
  const _LeftWorkbench({required this.onRecommend});
  final VoidCallback onRecommend;

  @override
  Widget build(BuildContext context) {
    final needs = [
      (Icons.sports_esports, '使用场景', 'FPS游戏 / CS2 / Valorant'),
      (Icons.account_balance_wallet_outlined, '预算范围', '300 元以内'),
      (Icons.auto_awesome, '偏好特点', '轻量化 / 低延迟'),
      (Icons.wifi, '连接方式', '无线优先'),
      (Icons.back_hand_outlined, '其他要求', '适合中小手'),
    ];
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: const [
              CircleAvatar(child: Icon(Icons.smart_toy)),
              SizedBox(width: 10),
              Text('AI 导购助手',
                  style: TextStyle(fontWeight: FontWeight.w900, fontSize: 18))
            ]),
            const SizedBox(height: 16),
            _Bubble('告诉我你的游戏类型、预算、手型和品牌偏好，我会把推荐理由讲清楚。'),
            const Divider(height: 34),
            const Text('已识别需求', style: TextStyle(fontWeight: FontWeight.w900)),
            const SizedBox(height: 12),
            ...needs.map((e) => Container(
                  margin: const EdgeInsets.only(bottom: 10),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                      color: const Color(0xFFF7F8FC),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: AppTheme.line)),
                  child: Row(children: [
                    Icon(e.$1, color: AppTheme.primary, size: 18),
                    const SizedBox(width: 10),
                    Expanded(
                        child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                          Text(e.$2,
                              style:
                                  const TextStyle(fontWeight: FontWeight.w800)),
                          Text(e.$3,
                              style: const TextStyle(
                                  color: AppTheme.muted, fontSize: 12))
                        ])),
                    const Icon(Icons.check, color: AppTheme.primary, size: 18)
                  ]),
                )),
            const SizedBox(height: 12),
            _Bubble('根据你的需求，我找到了 12 款高匹配鼠标，你可以继续告诉我更多偏好。'),
            const SizedBox(height: 16),
            Wrap(
                spacing: 8,
                runSpacing: 8,
                children: ['对比几款差异', '推荐更轻的', '200元以内', '适合趴握的']
                    .map((e) =>
                        ActionChip(label: Text(e), onPressed: onRecommend))
                    .toList()),
            const SizedBox(height: 16),
            TextField(
              minLines: 3,
              maxLines: 4,
              decoration: InputDecoration(
                hintText: '继续描述你的需求...',
                prefixIcon: IconButton(
                    onPressed: () {}, icon: const Icon(Icons.mic_none)),
                suffixIcon: IconButton(
                    onPressed: onRecommend,
                    icon: const Icon(Icons.send_rounded,
                        color: AppTheme.primary)),
              ),
            ),
            const SizedBox(height: 10),
            OutlinedButton.icon(
                onPressed: () {},
                icon: const Icon(Icons.upload_file),
                label: const Text('上传图片')),
          ],
        ),
      ),
    );
  }
}

class _Bubble extends StatelessWidget {
  const _Bubble(this.text);
  final String text;
  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
            color: const Color(0xFFF1F4FA),
            borderRadius: BorderRadius.circular(14)),
        child: Text(text, style: const TextStyle(height: 1.5)),
      );
}

class _RecommendationList extends StatelessWidget {
  const _RecommendationList({required this.data});
  final AgentResponse data;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(22),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('为你推荐的鼠标',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900)),
            const SizedBox(height: 6),
            const Text('基于你的需求和外设知识库分析',
                style: TextStyle(color: AppTheme.muted)),
            const SizedBox(height: 18),
            Wrap(
                spacing: 10,
                children: ['综合推荐', '匹配度', '价格', '重量', '延迟', '评分']
                    .map((e) =>
                        ChoiceChip(label: Text(e), selected: e == '综合推荐'))
                    .toList()),
            const SizedBox(height: 18),
            ...data.recommendations.asMap().entries.map((entry) {
              final i = entry.key;
              final rec = entry.value;
              return _RecommendationCard(rank: i + 1, recommendation: rec);
            }),
            Center(
                child: OutlinedButton.icon(
                    onPressed: () {},
                    icon: const Icon(Icons.keyboard_arrow_down),
                    label: const Text('查看更多推荐（共 12 款）'))),
          ],
        ),
      ),
    );
  }
}

class _RecommendationCard extends StatelessWidget {
  const _RecommendationCard({required this.rank, required this.recommendation});

  final int rank;
  final AgentRecommendation recommendation;

  @override
  Widget build(BuildContext context) {
    final product = recommendation.product;

    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppTheme.line),
      ),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final compact = constraints.maxWidth < 620;
          final imageWidth = compact ? double.infinity : 130.0;
          final imageHeight = compact ? 170.0 : 120.0;
          final badge = MatchScoreBadge(
              score: recommendation.matchScore, size: compact ? 58 : 64);
          final rankBadge = _RankBadge(rank: rank);
          final image = ClipRRect(
            borderRadius: BorderRadius.circular(14),
            child: Image.network(product.imageUrl,
                width: imageWidth, height: imageHeight, fit: BoxFit.cover),
          );
          final details =
              _ProductSummary(product: product, maxTags: compact ? 3 : 4);
          final actions = Wrap(
            spacing: 10,
            runSpacing: 8,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              badge,
              TextButton(
                onPressed: () =>
                    Navigator.pushNamed(context, '/product/${product.id}'),
                child: const Text('查看详情'),
              ),
            ],
          );

          if (compact) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(children: [rankBadge, const Spacer(), badge]),
                const SizedBox(height: 12),
                image,
                const SizedBox(height: 14),
                details,
                const SizedBox(height: 12),
                Text(recommendation.reason,
                    style: const TextStyle(height: 1.6, color: AppTheme.ink)),
                Align(
                  alignment: Alignment.centerRight,
                  child: TextButton(
                    onPressed: () =>
                        Navigator.pushNamed(context, '/product/${product.id}'),
                    child: const Text('查看详情'),
                  ),
                ),
              ],
            );
          }

          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  rankBadge,
                  const SizedBox(width: 16),
                  image,
                  const SizedBox(width: 18),
                  Expanded(child: details),
                  const SizedBox(width: 16),
                  actions,
                ],
              ),
              const SizedBox(height: 12),
              Padding(
                padding: const EdgeInsets.only(left: 192),
                child: Text(recommendation.reason,
                    style: const TextStyle(height: 1.6, color: AppTheme.ink)),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _RankBadge extends StatelessWidget {
  const _RankBadge({required this.rank});

  final int rank;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 28,
      height: 28,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: rank == 1 ? const Color(0xFFFFC542) : const Color(0xFFD9DEE8),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text('$rank',
          style: const TextStyle(
              color: Colors.white, fontWeight: FontWeight.w900)),
    );
  }
}

class _ProductSummary extends StatelessWidget {
  const _ProductSummary({required this.product, required this.maxTags});

  final Product product;
  final int maxTags;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(product.name,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900)),
        const SizedBox(height: 8),
        Text('￥${product.price.toStringAsFixed(0)}',
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900)),
        const SizedBox(height: 6),
        Wrap(
          spacing: 4,
          crossAxisAlignment: WrapCrossAlignment.center,
          children: [
            const Icon(Icons.star, size: 16, color: Color(0xFFFF9D18)),
            Text('${product.rating}  ${product.sales}+ 评价',
                style: const TextStyle(color: AppTheme.muted)),
          ],
        ),
        const SizedBox(height: 10),
        Wrap(
            spacing: 8,
            runSpacing: 8,
            children:
                product.tags.take(maxTags).map((e) => TagChip(e)).toList()),
      ],
    );
  }
}

class _AnalysisPanel extends StatelessWidget {
  const _AnalysisPanel({required this.data});
  final AgentResponse data;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child:
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('AI 分析摘要',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900)),
              const SizedBox(height: 14),
              Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                      color: const Color(0xFFF3F5FF),
                      borderRadius: BorderRadius.circular(16)),
                  child:
                      Text(data.summary, style: const TextStyle(height: 1.6))),
              const SizedBox(height: 18),
              const Text('需求匹配雷达图',
                  style: TextStyle(fontWeight: FontWeight.w900)),
              const SizedBox(height: 12),
              _RadarMock(),
              const Divider(height: 32),
              const Text('选购建议', style: TextStyle(fontWeight: FontWeight.w900)),
              const SizedBox(height: 8),
              ...[
                '追求极致轻量：VXE R1 Pro Max',
                '预算更低：罗技 G304',
                '品牌信任：雷蛇 V3 精英版',
                '不确定：建议对比 Top3'
              ].map((e) => Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Text('• $e'))),
            ]),
          ),
        ),
        const SizedBox(height: 14),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Text('下一步你可以',
                      style: TextStyle(fontWeight: FontWeight.w900)),
                  const SizedBox(height: 12),
                  OutlinedButton.icon(
                      onPressed: () => Navigator.pushNamed(context, '/compare'),
                      icon: const Icon(Icons.compare_arrows),
                      label: const Text('对比所选鼠标')),
                  OutlinedButton.icon(
                      onPressed: () {},
                      icon: const Icon(Icons.tune),
                      label: const Text('调整需求重新推荐')),
                  OutlinedButton.icon(
                      onPressed: () {},
                      icon: const Icon(Icons.menu_book),
                      label: const Text('查看鼠标选购指南')),
                ]),
          ),
        )
      ],
    );
  }
}

class _RadarMock extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final rows = [
      ('性能', .94),
      ('重量', .92),
      ('延迟', .90),
      ('价格', .88),
      ('手感', .84)
    ];
    return Column(
      children: rows
          .map((e) => Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: Row(children: [
                  SizedBox(width: 44, child: Text(e.$1)),
                  Expanded(
                      child: LinearProgressIndicator(
                          value: e.$2,
                          minHeight: 8,
                          borderRadius: BorderRadius.circular(8),
                          color: AppTheme.primary,
                          backgroundColor:
                              AppTheme.primary.withValues(alpha: .1))),
                ]),
              ))
          .toList(),
    );
  }
}
