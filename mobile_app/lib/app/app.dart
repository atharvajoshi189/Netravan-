import 'package:flutter/material.dart';
import '../core/config/theme.dart';
import '../features/camera_scan/camera_scan_screen.dart';
import '../features/observation_history/history_screen.dart';
import '../features/settings/settings_screen.dart';

class TigerTraceApp extends StatelessWidget {
  const TigerTraceApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'TigerTrace AI Mobile',
      debugShowCheckedModeBanner: false,
      theme: WildlifeTheme.darkTheme,
      routes: {
        '/settings': (context) => const SettingsScreen(),
        '/history': (context) => const HistoryScreen(),
      },
      home: const MainNavigationShell(),
    );
  }
}

class MainNavigationShell extends StatefulWidget {
  const MainNavigationShell({super.key});

  @override
  State<MainNavigationShell> createState() => _MainNavigationShellState();
}

class _MainNavigationShellState extends State<MainNavigationShell> {
  int _currentIndex = 0;

  final List<Widget> _screens = const [
    CameraScanScreen(),
    HistoryScreen(),
    SettingsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _screens,
      ),
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          border: Border(top: BorderSide(color: WildlifeTheme.cardBorder, width: 1)),
        ),
        child: BottomNavigationBar(
          currentIndex: _currentIndex,
          onTap: (index) => setState(() => _currentIndex = index),
          backgroundColor: WildlifeTheme.cardSurface,
          selectedItemColor: WildlifeTheme.primaryEmerald,
          unselectedItemColor: WildlifeTheme.textMuted,
          selectedFontSize: 12,
          unselectedFontSize: 12,
          type: BottomNavigationBarType.fixed,
          items: const [
            BottomNavigationBarItem(
              icon: Icon(Icons.radar_rounded),
              activeIcon: Icon(Icons.radar_rounded, color: WildlifeTheme.primaryEmerald),
              label: 'Field Scan',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.history_edu_rounded),
              activeIcon: Icon(Icons.history_edu_rounded, color: WildlifeTheme.primaryEmerald),
              label: 'Observations',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.tune_rounded),
              activeIcon: Icon(Icons.tune_rounded, color: WildlifeTheme.primaryEmerald),
              label: 'Settings',
            ),
          ],
        ),
      ),
    );
  }
}
