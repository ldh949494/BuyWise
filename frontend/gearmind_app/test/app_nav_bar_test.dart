import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gearmind_app/widgets/app_nav_bar.dart';

void main() {
  testWidgets('AppNavBar adapts without layout overflow', (tester) async {
    addTearDown(() => tester.view.resetPhysicalSize());

    for (final width in <double>[390, 700, 960, 1280]) {
      tester.view.physicalSize = Size(width, 720);
      tester.view.devicePixelRatio = 1;

      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(appBar: AppNavBar()),
        ),
      );
      await tester.pumpAndSettle();

      expect(tester.takeException(), isNull, reason: 'width: $width');
    }
  });
}
