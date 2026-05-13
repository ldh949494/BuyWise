import 'package:flutter/material.dart';

import '../theme/app_theme.dart';

class TagChip extends StatelessWidget {
  const TagChip(this.label, {super.key, this.soft = false});

  final String label;
  final bool soft;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: soft ? AppTheme.primary.withValues(alpha: .08) : const Color(0xFFF3F5FA),
        borderRadius: BorderRadius.circular(9),
        border: Border.all(color: soft ? AppTheme.primary.withValues(alpha: .18) : AppTheme.line),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: soft ? AppTheme.primary : AppTheme.muted,
          fontSize: 12,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}
