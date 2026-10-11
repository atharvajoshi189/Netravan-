import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tigertrace_mobile/app/app.dart';
import 'package:tigertrace_mobile/core/config/app_config.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    await AppConfig.init();
  });

  testWidgets('TigerTraceApp renders navigation and field scanner', (WidgetTester tester) async {
    await tester.pumpWidget(const TigerTraceApp());
    // Use pump with finite duration because camera scan has a repeating reticle animation
    await tester.pump(const Duration(milliseconds: 300));

    // Verify app bar title
    expect(find.text('Field Biometric Scanner'), findsOneWidget);

    // Verify bottom navigation items
    expect(find.text('Field Scan'), findsOneWidget);
    expect(find.text('Observations'), findsOneWidget);
    expect(find.text('Settings'), findsOneWidget);

    // Verify analyze button
    expect(find.text('Analyze Field Capture'), findsOneWidget);
  });
}
