import 'package:flutter/material.dart';

import '../mock/mock_products.dart';
import '../models/product.dart';
import '../theme/app_theme.dart';
import '../widgets/app_nav_bar.dart';
import '../widgets/product_card.dart';
import '../widgets/tag_chip.dart';

class ImageRecognitionPage extends StatelessWidget {
  const ImageRecognitionPage({super.key});

  @override
  Widget build(BuildContext context) {
    final recognized = findMockProduct('k001');
    final similar = mockProducts
        .where((p) => p.category == 'keyboard' && p.id != recognized.id)
        .take(6)
        .toList();
    return Scaffold(
      appBar: const AppNavBar(),
      body: LayoutBuilder(
        builder: (context, viewport) {
          final padding = viewport.maxWidth < 720 ? 16.0 : 28.0;

          return SingleChildScrollView(
            padding: EdgeInsets.all(padding),
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 1480),
                child: _RecognitionLayout(
                    recognized: recognized, similar: similar),
              ),
            ),
          );
        },
      ),
    );
  }
}

class _RecognitionLayout extends StatelessWidget {
  const _RecognitionLayout({required this.recognized, required this.similar});

  final Product recognized;
  final List<Product> similar;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final width = constraints.maxWidth;

        if (width >= 1600) {
          return Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SizedBox(width: 350, child: _UploadPanel(recognized: recognized)),
              const SizedBox(width: 22),
              Expanded(
                  child:
                      _ResultPanel(recognized: recognized, similar: similar)),
              const SizedBox(width: 22),
              const SizedBox(width: 260, child: _RightNav()),
            ],
          );
        }

        if (width >= 860) {
          return Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SizedBox(
                  width: width < 1040 ? 310 : 350,
                  child: _UploadPanel(recognized: recognized)),
              const SizedBox(width: 22),
              Expanded(
                child: Column(
                  children: [
                    _ResultPanel(recognized: recognized, similar: similar),
                    const SizedBox(height: 18),
                    const _RightNav(),
                  ],
                ),
              ),
            ],
          );
        }

        return Column(
          children: [
            _UploadPanel(recognized: recognized),
            const SizedBox(height: 18),
            _ResultPanel(recognized: recognized, similar: similar),
            const SizedBox(height: 18),
            const _RightNav(),
          ],
        );
      },
    );
  }
}

class _UploadPanel extends StatelessWidget {
  const _UploadPanel({required this.recognized});
  final Product recognized;
  @override
  Widget build(BuildContext context) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      const Text('图片识物',
          style: TextStyle(fontSize: 30, fontWeight: FontWeight.w900)),
      const SizedBox(height: 8),
      const Text('上传图片，AI 帮你识别外设，找到同款或更优选择',
          style: TextStyle(color: AppTheme.muted)),
      const SizedBox(height: 20),
      Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(children: [
            ClipRRect(
                borderRadius: BorderRadius.circular(16),
                child: Image.network(recognized.imageUrl,
                    height: 260, width: double.infinity, fit: BoxFit.cover)),
            const SizedBox(height: 12),
            OutlinedButton.icon(
                onPressed: () {},
                icon: const Icon(Icons.refresh),
                label: const Text('重新上传')),
            const SizedBox(height: 10),
            const Text('支持 JPG / PNG / WEBP，大小不超过 10MB',
                style: TextStyle(color: AppTheme.muted, fontSize: 12)),
          ]),
        ),
      ),
      const SizedBox(height: 18),
      Card(
        child: Padding(
          padding: const EdgeInsets.all(18),
          child:
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('识别历史',
                style: TextStyle(fontWeight: FontWeight.w900, fontSize: 18)),
            const SizedBox(height: 12),
            ...[
              ('机械键盘 75% 配列', '刚刚识别'),
              ('罗技 G Pro X Superlight 2', '2小时前'),
              ('森海塞尔 HD 660S2', '1天前'),
            ].map((e) => Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: Row(
                    children: [
                      ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: Image.network(recognized.imageUrl,
                              width: 54, height: 42, fit: BoxFit.cover)),
                      const SizedBox(width: 12),
                      Expanded(
                          child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                            Text(e.$1,
                                maxLines: 1, overflow: TextOverflow.ellipsis),
                            Text(e.$2,
                                style: const TextStyle(color: AppTheme.muted)),
                          ])),
                    ],
                  ),
                )),
          ]),
        ),
      )
    ]);
  }
}

class _ResultPanel extends StatelessWidget {
  const _ResultPanel({required this.recognized, required this.similar});
  final Product recognized;
  final List<Product> similar;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const _ResultHeader(),
          const Divider(height: 28),
          _RecognizedProductSummary(recognized: recognized),
          const SizedBox(height: 24),
          const Text('AI 推荐操作',
              style: TextStyle(fontWeight: FontWeight.w900, fontSize: 18)),
          const SizedBox(height: 12),
          const _ActionGrid(),
          const Divider(height: 34),
          const Text('相似外设推荐列表',
              style: TextStyle(fontWeight: FontWeight.w900, fontSize: 18)),
          const SizedBox(height: 14),
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: similar.length,
            gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
                maxCrossAxisExtent: 230,
                mainAxisExtent: 380,
                crossAxisSpacing: 14,
                mainAxisSpacing: 14),
            itemBuilder: (_, i) =>
                ProductCard(product: similar[i], compact: true),
          ),
          const SizedBox(height: 18),
          Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
                color: const Color(0xFFF3F5FF),
                borderRadius: BorderRadius.circular(16)),
            child: const Row(children: [
              Icon(Icons.smart_toy_outlined, color: AppTheme.primary),
              SizedBox(width: 12),
              Expanded(
                  child: Text(
                      'AI 分析总结：这是一款 75% 配列的客制化机械键盘，采用 Gasket 结构设计，整体风格偏桌搭和电竞氛围，适合追求手感和颜值的玩家。'))
            ]),
          )
        ]),
      ),
    );
  }
}

class _ResultHeader extends StatelessWidget {
  const _ResultHeader();

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final compact = constraints.maxWidth < 520;

        return Wrap(
          spacing: 14,
          runSpacing: 10,
          crossAxisAlignment: WrapCrossAlignment.center,
          children: [
            const Text('识别结果',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900)),
            const TagChip('识别成功', soft: true),
            SizedBox(
                width: compact
                    ? 0
                    : (constraints.maxWidth - 300).clamp(0.0, 9999.0)),
            const Text('置信度', style: TextStyle(color: AppTheme.muted)),
            const Text('92%',
                style: TextStyle(
                    color: AppTheme.primary,
                    fontSize: 24,
                    fontWeight: FontWeight.w900)),
          ],
        );
      },
    );
  }
}

class _RecognizedProductSummary extends StatelessWidget {
  const _RecognizedProductSummary({required this.recognized});

  final Product recognized;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final compact = constraints.maxWidth < 760;
        final imageWidth = compact ? double.infinity : 210.0;
        final image = ClipRRect(
          borderRadius: BorderRadius.circular(16),
          child: Image.network(recognized.imageUrl,
              width: imageWidth,
              height: compact ? 210 : 140,
              fit: BoxFit.cover),
        );
        final detail = Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(recognized.name,
                style:
                    const TextStyle(fontSize: 22, fontWeight: FontWeight.w900)),
            const SizedBox(height: 10),
            Wrap(
                spacing: 8,
                runSpacing: 8,
                children: ['75%配列', 'Gasket结构', '客制化机械键盘', 'PBT键帽']
                    .map((e) => TagChip(e, soft: true))
                    .toList()),
            const SizedBox(height: 12),
            Text(
                '￥${recognized.price.toStringAsFixed(0)} 起  ·  ${recognized.rating} 分  ·  ${recognized.sales}+ 评价'),
          ],
        );
        final points = Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            'Gasket 结构，手感软弹',
            '全铝 CNC 机身，质感出色',
            'RGB 灯效，支持驱动自定义',
            '多种配色可选，颜值在线'
          ]
              .map((e) => Padding(
                  padding: const EdgeInsets.only(bottom: 9),
                  child: Text('• $e')))
              .toList(),
        );

        if (compact) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              image,
              const SizedBox(height: 18),
              detail,
              const SizedBox(height: 16),
              points,
            ],
          );
        }

        return Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            image,
            const SizedBox(width: 20),
            Expanded(flex: 3, child: detail),
            const SizedBox(width: 16),
            Expanded(flex: 2, child: points),
          ],
        );
      },
    );
  }
}

class _ActionGrid extends StatelessWidget {
  const _ActionGrid();

  @override
  Widget build(BuildContext context) {
    const actions = [
      (Icons.keyboard, '找同款', '查找完全相同的产品'),
      (Icons.savings, '找平替', '找性价比更高的替代选择'),
      (Icons.rocket_launch, '找升级款', '性能更强的升级选择'),
      (Icons.extension, '找搭配', '推荐搭配的外设组合'),
    ];

    return LayoutBuilder(
      builder: (context, constraints) {
        final columns = constraints.maxWidth >= 920
            ? 4
            : constraints.maxWidth >= 520
                ? 2
                : 1;
        final gap = 12.0;
        final itemWidth =
            (constraints.maxWidth - gap * (columns - 1)) / columns;

        return Wrap(
          spacing: gap,
          runSpacing: gap,
          children: actions
              .map((action) => SizedBox(
                  width: itemWidth,
                  child: _Action(
                      icon: action.$1, title: action.$2, desc: action.$3)))
              .toList(),
        );
      },
    );
  }
}

class _Action extends StatelessWidget {
  const _Action({required this.icon, required this.title, required this.desc});
  final IconData icon;
  final String title;
  final String desc;
  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final compact = constraints.maxWidth < 180;
        final child = compact
            ? Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(icon, color: AppTheme.primary),
                  const SizedBox(height: 8),
                  Text(title,
                      textAlign: TextAlign.center,
                      style: const TextStyle(fontWeight: FontWeight.w900)),
                  const SizedBox(height: 4),
                  Text(desc,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      textAlign: TextAlign.center,
                      style:
                          const TextStyle(color: AppTheme.muted, fontSize: 12)),
                ],
              )
            : Row(
                children: [
                  Icon(icon, color: AppTheme.primary),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(title,
                              style:
                                  const TextStyle(fontWeight: FontWeight.w900)),
                          Text(desc,
                              style: const TextStyle(
                                  color: AppTheme.muted, fontSize: 12)),
                        ]),
                  ),
                ],
              );

        return Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
              color: const Color(0xFFF7F8FC),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppTheme.line)),
          child: child,
        );
      },
    );
  }
}

class _RightNav extends StatelessWidget {
  const _RightNav();
  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(18),
        child:
            Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          const Text('快速导航',
              style: TextStyle(fontWeight: FontWeight.w900, fontSize: 18)),
          const SizedBox(height: 12),
          ...['找同款', '找平替', '找同配列', '找同风格', '参数查询']
              .map((e) => OutlinedButton(onPressed: () {}, child: Text(e))),
          const Divider(height: 28),
          OutlinedButton.icon(
              onPressed: () {},
              icon: const Icon(Icons.share_outlined),
              label: const Text('分享结果')),
        ]),
      ),
    );
  }
}
