import 'package:flutter/material.dart';

import '../theme/app_theme.dart';

class AppNavBar extends StatelessWidget implements PreferredSizeWidget {
  const AppNavBar({super.key});

  @override
  Size get preferredSize => const Size.fromHeight(72);

  @override
  Widget build(BuildContext context) {
    return AppBar(
      titleSpacing: 0,
      title: const _NavBarContent(),
      bottom: const PreferredSize(
        preferredSize: Size.fromHeight(1),
        child: Divider(height: 1, color: AppTheme.line),
      ),
    );
  }
}

class _NavBarContent extends StatelessWidget {
  const _NavBarContent();

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final width = constraints.maxWidth;
        final showFullLogo = width >= 520;
        final showNav = width >= 860;
        final showMoreNav = width >= 1120;
        final showSearch = width >= 680;
        final showAiText = width >= 1060;
        final showUtilityIcons = width >= 760;
        final horizontalPadding = width < 720 ? 12.0 : 24.0;
        final navItems = (showMoreNav
            ? ['首页', '键盘', '鼠标', '耳机', '显示器']
            : ['首页', '键盘', '鼠标']);

        return Padding(
          padding: EdgeInsets.symmetric(horizontal: horizontalPadding),
          child: Row(
            children: [
              _Brand(showText: showFullLogo),
              if (showNav) ...[
                SizedBox(width: showMoreNav ? 30 : 18),
                Flexible(
                  flex: 0,
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: navItems.map((e) => _NavItem(e)).toList(),
                  ),
                ),
              ],
              const SizedBox(width: 16),
              if (showSearch)
                Expanded(
                  child: ConstrainedBox(
                    constraints:
                        const BoxConstraints(minWidth: 160, maxWidth: 430),
                    child: const _SearchField(),
                  ),
                )
              else
                const Spacer(),
              const SizedBox(width: 12),
              if (showAiText)
                FilledButton.icon(
                  onPressed: () => Navigator.pushNamed(context, '/agent'),
                  icon: const Icon(Icons.auto_awesome, size: 18),
                  label: const Text('AI 导购'),
                )
              else
                IconButton.filled(
                  tooltip: 'AI 导购',
                  onPressed: () => Navigator.pushNamed(context, '/agent'),
                  icon: const Icon(Icons.auto_awesome, size: 20),
                ),
              if (showUtilityIcons) ...[
                IconButton(
                    onPressed: () {}, icon: const Icon(Icons.favorite_border)),
                IconButton(
                    onPressed: () {},
                    icon: const Icon(Icons.shopping_cart_outlined)),
                const CircleAvatar(
                  radius: 20,
                  backgroundColor: Color(0xFFE8ECFF),
                  child: Icon(Icons.person, color: AppTheme.primary),
                ),
              ] else
                IconButton(
                  tooltip: '搜索',
                  onPressed: () {},
                  icon: const Icon(Icons.search),
                ),
            ],
          ),
        );
      },
    );
  }
}

class _Brand extends StatelessWidget {
  const _Brand({required this.showText});

  final bool showText;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () => Navigator.pushNamed(context, '/'),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 38,
            height: 38,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                  colors: [AppTheme.primary, AppTheme.violet]),
              borderRadius: BorderRadius.circular(11),
            ),
            child: const Icon(Icons.gamepad_rounded, color: Colors.white),
          ),
          if (showText) ...[
            const SizedBox(width: 10),
            const Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('GearMind',
                    style: TextStyle(
                        fontWeight: FontWeight.w900,
                        color: AppTheme.ink,
                        fontSize: 20)),
                Text('AI 外设导购',
                    style: TextStyle(color: AppTheme.muted, fontSize: 11)),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

class _NavItem extends StatelessWidget {
  const _NavItem(this.label);

  final String label;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 9),
      child: Text(
        label,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
        style: const TextStyle(
            fontSize: 14, fontWeight: FontWeight.w700, color: AppTheme.ink),
      ),
    );
  }
}

class _SearchField extends StatelessWidget {
  const _SearchField();

  @override
  Widget build(BuildContext context) {
    return TextField(
      decoration: InputDecoration(
        hintText: '搜索外设、品牌、型号、关键词...',
        prefixIcon: const Icon(Icons.search),
        suffixIcon: Container(
          margin: const EdgeInsets.all(6),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
                colors: [AppTheme.primary, AppTheme.violet]),
            borderRadius: BorderRadius.circular(10),
          ),
          child: const Icon(Icons.arrow_forward, color: Colors.white, size: 18),
        ),
      ),
    );
  }
}
