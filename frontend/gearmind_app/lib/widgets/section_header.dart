import 'package:flutter/material.dart';

import '../theme/app_theme.dart';

class SectionHeader extends StatelessWidget {
  const SectionHeader(this.title, {super.key, this.subtitle, this.action});

  final String title;
  final String? subtitle;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w900, color: AppTheme.ink)),
              if (subtitle != null) ...[
                const SizedBox(height: 6),
                Text(subtitle!, style: const TextStyle(color: AppTheme.muted)),
              ],
            ],
          ),
        ),
        if (action != null) action!,
      ],
    );
  }
}
