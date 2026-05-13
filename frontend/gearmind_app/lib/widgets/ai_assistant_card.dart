import 'package:flutter/material.dart';

import '../theme/app_theme.dart';

class AiAssistantCard extends StatelessWidget {
  const AiAssistantCard({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 330,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: AppTheme.line),
        boxShadow: [BoxShadow(color: AppTheme.primary.withValues(alpha: .10), blurRadius: 28, offset: const Offset(0, 12))],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const CircleAvatar(backgroundColor: Color(0xFFE8ECFF), child: Icon(Icons.smart_toy, color: AppTheme.primary)),
              const SizedBox(width: 10),
              const Expanded(child: Text('GearMind 导购助手', style: TextStyle(fontWeight: FontWeight.w900))),
              IconButton(onPressed: () {}, icon: const Icon(Icons.close, size: 18)),
            ],
          ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(color: const Color(0xFFF4F6FB), borderRadius: BorderRadius.circular(14)),
            child: const Text('嗨，我可以帮你根据游戏类型、预算和手型快速找到合适外设。', style: TextStyle(color: AppTheme.ink)),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: ['预算 300 内鼠标', '宿舍静音键盘', 'FPS 耳机推荐']
                .map((e) => ActionChip(label: Text(e), onPressed: () => Navigator.pushNamed(context, '/agent')))
                .toList(),
          ),
          const SizedBox(height: 12),
          TextField(
            onSubmitted: (_) => Navigator.pushNamed(context, '/agent'),
            decoration: const InputDecoration(hintText: '输入你的需求...', suffixIcon: Icon(Icons.send_rounded)),
          ),
        ],
      ),
    );
  }
}
