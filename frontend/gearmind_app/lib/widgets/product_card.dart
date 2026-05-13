import 'package:flutter/material.dart';

import '../models/product.dart';
import '../theme/app_theme.dart';
import 'tag_chip.dart';

class ProductCard extends StatelessWidget {
  const ProductCard({super.key, required this.product, this.compact = false});

  final Product product;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () => Navigator.pushNamed(context, '/product/${product.id}'),
      borderRadius: BorderRadius.circular(18),
      child: Card(
        clipBehavior: Clip.antiAlias,
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Stack(
                children: [
                  AspectRatio(
                    aspectRatio: compact ? 1.85 : 1.25,
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(14),
                      child: Image.network(product.imageUrl, fit: BoxFit.cover),
                    ),
                  ),
                  Positioned(
                    top: 8,
                    left: 8,
                    child: TagChip('AI 推荐 ${product.matchScore}%', soft: true),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Text(
                product.name,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w900,
                    color: AppTheme.ink),
              ),
              const SizedBox(height: 6),
              Text(
                product.description,
                maxLines: compact ? 1 : 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(color: AppTheme.muted, fontSize: 12),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Text('¥${product.price.toStringAsFixed(0)}',
                      style: const TextStyle(
                          fontSize: 18, fontWeight: FontWeight.w900)),
                  const Spacer(),
                  const Icon(Icons.star, color: Color(0xFFFF9D18), size: 16),
                  Text(' ${product.rating}',
                      style:
                          const TextStyle(color: AppTheme.muted, fontSize: 12)),
                ],
              ),
              const SizedBox(height: 10),
              Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: product.tags
                      .take(compact ? 2 : 3)
                      .map((e) => TagChip(e))
                      .toList()),
            ],
          ),
        ),
      ),
    );
  }
}
