import 'package:flutter/material.dart';

import '../models/compare_result.dart';
import '../theme/app_theme.dart';

class CompareTable extends StatelessWidget {
  const CompareTable({super.key, required this.result});

  final CompareResult result;

  @override
  Widget build(BuildContext context) {
    final columns = result.products;
    return Card(
      child: ClipRRect(
        borderRadius: BorderRadius.circular(18),
        child: Table(
          border: TableBorder.symmetric(
            inside: const BorderSide(color: AppTheme.line),
            outside: BorderSide.none,
          ),
          columnWidths: {
            0: const FixedColumnWidth(150),
            for (var i = 0; i < columns.length; i++) i + 1: const FlexColumnWidth(),
          },
          children: [
            TableRow(
              decoration: const BoxDecoration(color: Color(0xFFF7F8FD)),
              children: [
                _cell('对比维度', head: true),
                ...columns.map((p) => _cell(p.name, head: true)),
              ],
            ),
            ...result.table.entries.map((entry) {
              return TableRow(
                children: [
                  _cell(entry.key, dim: true),
                  ...columns.map((p) {
                    final value = entry.value[p.id];
                    if (entry.key == '商品图') {
                      return Padding(
                        padding: const EdgeInsets.all(12),
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(12),
                          child: Image.network('$value', height: 82, fit: BoxFit.cover),
                        ),
                      );
                    }
                    return _cell('$value');
                  }),
                ],
              );
            }),
          ],
        ),
      ),
    );
  }

  Widget _cell(String text, {bool head = false, bool dim = false}) {
    return Padding(
      padding: const EdgeInsets.all(14),
      child: Text(
        text,
        style: TextStyle(
          color: dim ? AppTheme.muted : AppTheme.ink,
          fontWeight: head || dim ? FontWeight.w900 : FontWeight.w600,
          height: 1.45,
        ),
      ),
    );
  }
}
