import 'package:flutter/material.dart';

import '../theme/app_theme.dart';

class MatchScoreBadge extends StatelessWidget {
  const MatchScoreBadge({super.key, required this.score, this.size = 72});

  final int score;
  final double size;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: Stack(
        alignment: Alignment.center,
        children: [
          CircularProgressIndicator(
            value: score / 100,
            strokeWidth: 5,
            backgroundColor: AppTheme.primary.withValues(alpha: .12),
            color: AppTheme.primary,
          ),
          Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text('$score%', style: const TextStyle(fontWeight: FontWeight.w900, color: AppTheme.primary)),
              const Text('匹配度', style: TextStyle(fontSize: 10, color: AppTheme.primary)),
            ],
          )
        ],
      ),
    );
  }
}
