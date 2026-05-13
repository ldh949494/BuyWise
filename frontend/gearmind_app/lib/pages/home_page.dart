import 'package:flutter/material.dart';

import '../models/product.dart';
import '../services/product_api.dart';
import '../theme/app_theme.dart';
import '../widgets/ai_assistant_card.dart';
import '../widgets/app_nav_bar.dart';
import '../widgets/product_card.dart';
import '../widgets/section_header.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  late final Future<List<Product>> _products = ProductApi().listProducts();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const AppNavBar(),
      body: LayoutBuilder(
        builder: (context, viewport) {
          final width = viewport.maxWidth;
          final compact = width < 980;
          final wide = width >= 1280;
          final padding = width < 720 ? 16.0 : (wide ? 34.0 : 24.0);
          final contentMaxWidth = width >= 1500 ? 1680.0 : 1380.0;
          final showFloatingAssistant = width >= 1180;

          return Stack(
            children: [
              FutureBuilder<List<Product>>(
                future: _products,
                builder: (context, snapshot) {
                  final products = snapshot.data ?? const <Product>[];
                  return SingleChildScrollView(
                    padding: EdgeInsets.fromLTRB(padding, padding, padding, 48),
                    child: Center(
                      child: ConstrainedBox(
                        constraints: BoxConstraints(maxWidth: contentMaxWidth),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            if (wide)
                              Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Expanded(flex: 4, child: _HeroBanner()),
                                  const SizedBox(width: 24),
                                  const SizedBox(
                                      width: 270,
                                      child: _QuickPanel(compact: true)),
                                ],
                              )
                            else
                              Column(
                                children: [
                                  _HeroBanner(compact: compact),
                                  const SizedBox(height: 18),
                                  const _QuickPanel(horizontal: true),
                                ],
                              ),
                            const SizedBox(height: 28),
                            _ScenarioStrip(),
                            const SizedBox(height: 34),
                            SectionHeader(
                              'AI 精选推荐',
                              subtitle: '围绕 FPS、宿舍静音、程序员桌搭和桌面氛围精选外设',
                              action: OutlinedButton.icon(
                                  onPressed: () {},
                                  icon: const Icon(Icons.tune),
                                  label: const Text('筛选')),
                            ),
                            const SizedBox(height: 16),
                            GridView.builder(
                              shrinkWrap: true,
                              physics: const NeverScrollableScrollPhysics(),
                              itemCount: products.take(8).length,
                              gridDelegate:
                                  SliverGridDelegateWithMaxCrossAxisExtent(
                                maxCrossAxisExtent: width >= 1500 ? 330 : 300,
                                mainAxisExtent: width < 720 ? 380 : 410,
                                crossAxisSpacing: 18,
                                mainAxisSpacing: 18,
                              ),
                              itemBuilder: (_, i) =>
                                  ProductCard(product: products[i]),
                            ),
                            const SizedBox(height: 40),
                            const SectionHeader('AI 导购工具区',
                                subtitle: '在关键决策节点使用 Agent 缩短选购路径'),
                            const SizedBox(height: 16),
                            _ToolGrid(),
                            const SizedBox(height: 28),
                            _TrustBar(),
                          ],
                        ),
                      ),
                    ),
                  );
                },
              ),
              if (showFloatingAssistant)
                Positioned(
                    right: padding, bottom: 24, child: const AiAssistantCard()),
            ],
          );
        },
      ),
    );
  }
}

class _HeroBanner extends StatelessWidget {
  const _HeroBanner({this.compact = false});

  final bool compact;

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: BoxConstraints(minHeight: compact ? 360 : 380),
      padding: EdgeInsets.all(compact ? 24 : 42),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(28),
        gradient: const LinearGradient(
            colors: [Color(0xFFEAF0FF), Color(0xFFF8FAFF)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight),
        border: Border.all(color: AppTheme.line),
        boxShadow: [
          BoxShadow(
              color: AppTheme.primary.withValues(alpha: .08),
              blurRadius: 34,
              offset: const Offset(0, 18))
        ],
      ),
      child: compact
          ? Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const _HeroCopy(fontSize: 32),
                const SizedBox(height: 22),
                _HeroVisual(compact: true),
              ],
            )
          : Row(
              children: [
                const Expanded(child: _HeroCopy(fontSize: 38)),
                Expanded(child: _HeroVisual()),
              ],
            ),
    );
  }
}

class _HeroCopy extends StatelessWidget {
  const _HeroCopy({required this.fontSize});

  final double fontSize;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Text('让 AI 帮你找到\n真正适合你的电竞外设',
            style: TextStyle(
                fontSize: fontSize,
                height: 1.2,
                fontWeight: FontWeight.w900,
                color: AppTheme.ink)),
        const SizedBox(height: 18),
        const Text('基于你的游戏习惯、预算和偏好，为你推荐最合适的装备组合',
            style: TextStyle(fontSize: 17, color: AppTheme.muted, height: 1.6)),
        const SizedBox(height: 28),
        FilledButton.icon(
          onPressed: () => Navigator.pushNamed(context, '/agent'),
          icon: const Icon(Icons.auto_awesome),
          label: const Text('开始智能导购'),
        ),
      ],
    );
  }
}

class _HeroVisual extends StatelessWidget {
  const _HeroVisual({this.compact = false});

  final bool compact;

  @override
  Widget build(BuildContext context) {
    return AspectRatio(
      aspectRatio: compact ? 1.55 : 1.38,
      child: LayoutBuilder(
        builder: (context, constraints) {
          final imageWidth = constraints.maxWidth.clamp(260.0, 360.0);
          final imageHeight = (imageWidth * .72).clamp(190.0, 260.0);

          return Stack(
            alignment: Alignment.center,
            children: [
              Container(
                width: imageWidth * .94,
                height: imageHeight,
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: .72),
                  borderRadius: BorderRadius.circular(28),
                ),
              ),
              ClipRRect(
                borderRadius: BorderRadius.circular(24),
                child: Image.network(
                  'https://images.unsplash.com/photo-1618384887929-16ec33fab9ef?auto=format&fit=crop&w=900&q=80',
                  width: imageWidth,
                  height: imageHeight,
                  fit: BoxFit.cover,
                ),
              ),
              Positioned(
                  top: 24,
                  left: compact ? 0 : 10,
                  child: const _FloatPill(
                      icon: Icons.sports_esports, text: 'FPS / CS2')),
              Positioned(
                  bottom: 22,
                  right: 0,
                  child: const _FloatPill(icon: Icons.bolt, text: '低延迟无线')),
            ],
          );
        },
      ),
    );
  }
}

class _FloatPill extends StatelessWidget {
  const _FloatPill({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: .9),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.line),
      ),
      child: Row(children: [
        Icon(icon, size: 18, color: AppTheme.primary),
        const SizedBox(width: 8),
        Text(text, style: const TextStyle(fontWeight: FontWeight.w800))
      ]),
    );
  }
}

class _QuickPanel extends StatelessWidget {
  const _QuickPanel({this.horizontal = false, this.compact = false});

  final bool horizontal;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final items = [
      (Icons.smart_toy_outlined, '智能导购', 'AI 为你精准推荐', '/agent'),
      (Icons.image_search, '图片识物', '上传图片找同款', '/image-recognition'),
      (Icons.compare_arrows, '商品对比', '多款商品对比分析', '/compare'),
      (Icons.rate_review_outlined, '评论总结', 'AI 提炼真实评价', '/agent'),
    ];
    return Card(
      child: Padding(
        padding: EdgeInsets.all(compact ? 18 : 22),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('我的快捷入口',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900)),
            const SizedBox(height: 16),
            if (horizontal)
              LayoutBuilder(
                builder: (context, constraints) {
                  final columns = constraints.maxWidth >= 900 ? 4 : 2;
                  final gap = 12.0;
                  final itemWidth =
                      (constraints.maxWidth - gap * (columns - 1)) / columns;
                  return Wrap(
                    spacing: gap,
                    runSpacing: gap,
                    children: items
                        .map((item) => SizedBox(
                              width: itemWidth,
                              child: _QuickPanelItem(item: item, dense: true),
                            ))
                        .toList(),
                  );
                },
              )
            else
              ...items
                  .map((item) => _QuickPanelItem(item: item, dense: compact)),
          ],
        ),
      ),
    );
  }
}

class _QuickPanelItem extends StatelessWidget {
  const _QuickPanelItem({required this.item, this.dense = false});

  final (IconData, String, String, String) item;
  final bool dense;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () => Navigator.pushNamed(context, item.$4),
      borderRadius: BorderRadius.circular(14),
      child: Padding(
        padding: EdgeInsets.symmetric(vertical: dense ? 8 : 10, horizontal: 4),
        child: Row(
          children: [
            Container(
              width: dense ? 40 : 46,
              height: dense ? 40 : 46,
              decoration: BoxDecoration(
                  color: AppTheme.primary.withValues(alpha: .08),
                  borderRadius: BorderRadius.circular(14)),
              child: Icon(item.$1, color: AppTheme.primary),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(item.$2,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontWeight: FontWeight.w800)),
                  const SizedBox(height: 2),
                  Text(item.$3,
                      maxLines: dense ? 1 : 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(color: AppTheme.muted)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ScenarioStrip extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final cards = [
      (Icons.gps_fixed, 'FPS 玩家必备', '轻量鼠标 + 控制垫'),
      (Icons.volume_off, '宿舍静音搭配', '低噪键盘与耳机'),
      (Icons.code, '程序员桌搭', '75% 配列效率装备'),
      (Icons.light_mode, '电竞氛围灯效', 'RGB 与显示器联动'),
      (Icons.savings, '入门性价比', '300 元内稳定选择'),
    ];
    return LayoutBuilder(
      builder: (context, constraints) {
        final columns = constraints.maxWidth >= 1180
            ? 5
            : constraints.maxWidth >= 760
                ? 3
                : 1;
        final gap = 14.0;
        final itemWidth =
            (constraints.maxWidth - gap * (columns - 1)) / columns;

        return Wrap(
          spacing: gap,
          runSpacing: gap,
          children: cards
              .map((e) => SizedBox(
                    width: itemWidth,
                    child: Container(
                      padding: const EdgeInsets.all(18),
                      decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(18),
                          border: Border.all(color: AppTheme.line)),
                      child: Row(
                        children: [
                          Icon(e.$1, color: AppTheme.primary),
                          const SizedBox(width: 12),
                          Expanded(
                              child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                Text(e.$2,
                                    style: const TextStyle(
                                        fontWeight: FontWeight.w900)),
                                Text(e.$3,
                                    style: const TextStyle(
                                        color: AppTheme.muted, fontSize: 12))
                              ])),
                        ],
                      ),
                    ),
                  ))
              .toList(),
        );
      },
    );
  }
}

class _ToolGrid extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final tools = [
      (Icons.image_search, '图片识物', '上传商品图片，快速找同款或平替', '/image-recognition'),
      (Icons.compare_arrows, '商品对比', '多维度对比外设，AI 解释差异', '/compare'),
      (Icons.tune, '配置推荐', '按预算生成整套桌面装备清单', '/agent'),
      (Icons.summarize, '评论总结', '快速了解优缺点和翻车点', '/agent'),
    ];
    return LayoutBuilder(
      builder: (context, constraints) {
        final columns = constraints.maxWidth >= 1120
            ? 4
            : constraints.maxWidth >= 680
                ? 2
                : 1;
        return GridView.count(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisCount: columns,
          childAspectRatio: columns == 1 ? 3.2 : 1.9,
          crossAxisSpacing: 18,
          mainAxisSpacing: 18,
          children: tools
              .map((e) => InkWell(
                    onTap: () => Navigator.pushNamed(context, e.$4),
                    borderRadius: BorderRadius.circular(20),
                    child: Container(
                      padding: const EdgeInsets.all(22),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: AppTheme.line),
                      ),
                      child: Row(
                        children: [
                          Icon(e.$1, color: AppTheme.violet, size: 34),
                          const SizedBox(width: 16),
                          Expanded(
                              child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                Text(e.$2,
                                    style: const TextStyle(
                                        fontSize: 18,
                                        fontWeight: FontWeight.w900)),
                                Text(e.$3,
                                    maxLines: 2,
                                    overflow: TextOverflow.ellipsis,
                                    style:
                                        const TextStyle(color: AppTheme.muted))
                              ])),
                        ],
                      ),
                    ),
                  ))
              .toList(),
        );
      },
    );
  }
}

class _TrustBar extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 20),
        child: Wrap(
          alignment: WrapAlignment.spaceAround,
          spacing: 24,
          runSpacing: 14,
          children: const [
            _Trust(icon: Icons.verified_user_outlined, text: '正品保障'),
            _Trust(icon: Icons.refresh, text: '30 天无忧退换'),
            _Trust(icon: Icons.local_shipping_outlined, text: '闪电发货'),
            _Trust(icon: Icons.auto_awesome, text: 'AI 智能推荐'),
          ],
        ),
      ),
    );
  }
}

class _Trust extends StatelessWidget {
  const _Trust({required this.icon, required this.text});
  final IconData icon;
  final String text;
  @override
  Widget build(BuildContext context) => Row(children: [
        Icon(icon, color: AppTheme.muted),
        const SizedBox(width: 10),
        Text(text, style: const TextStyle(fontWeight: FontWeight.w800))
      ]);
}
