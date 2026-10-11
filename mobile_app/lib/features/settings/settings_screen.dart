import 'package:flutter/material.dart';
import '../../core/api/api_client.dart';
import '../../core/config/app_config.dart';
import '../../core/config/theme.dart';
import '../../core/services/offline_queue.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final ApiClient _apiClient = ApiClient();
  late TextEditingController _urlController;
  late TextEditingController _officerController;

  bool _isTesting = false;
  Map<String, dynamic>? _healthInfo;
  String? _testError;

  @override
  void initState() {
    super.initState();
    _urlController = TextEditingController(text: AppConfig.baseUrl);
    _officerController = TextEditingController(text: AppConfig.officerId);
  }

  @override
  void dispose() {
    _urlController.dispose();
    _officerController.dispose();
    super.dispose();
  }

  Future<void> _saveSettings() async {
    await AppConfig.setBaseUrl(_urlController.text.trim());
    await AppConfig.setOfficerId(_officerController.text.trim());

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('✓ Server configuration saved'),
          backgroundColor: WildlifeTheme.primaryEmerald,
        ),
      );
    }
  }

  Future<void> _testHealth() async {
    setState(() {
      _isTesting = true;
      _healthInfo = null;
      _testError = null;
    });

    await AppConfig.setBaseUrl(_urlController.text.trim());

    try {
      final res = await _apiClient.checkHealth();
      setState(() {
        _healthInfo = res;
        _isTesting = false;
      });
    } catch (e) {
      setState(() {
        _testError = e.toString();
        _isTesting = false;
      });
    }
  }

  Future<void> _clearLocalQueue() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: WildlifeTheme.cardSurface,
        title: const Text('Clear Local Cache?', style: TextStyle(color: WildlifeTheme.textPrimary)),
        content: const Text(
          'This will purge all local offline observation records on this phone. Ensure synced observations are on the server first.',
          style: TextStyle(color: WildlifeTheme.textSecondary),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel', style: TextStyle(color: WildlifeTheme.textMuted)),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: ElevatedButton.styleFrom(backgroundColor: WildlifeTheme.dangerRed),
            child: const Text('Clear All'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      await OfflineQueue.clearAll();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Local observation storage cleared.')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: WildlifeTheme.darkBg,
      appBar: AppBar(
        title: const Text('Mobile App & AI Backend Settings'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Backend URL Card
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                color: WildlifeTheme.cardSurface,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: WildlifeTheme.cardBorder),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Shared FastAPI Backend URL',
                    style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.bold,
                      color: WildlifeTheme.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    'Base URL for YOLOv8 detection, HotSpotter Re-ID and Pench database sync.',
                    style: TextStyle(fontSize: 12, color: WildlifeTheme.textMuted),
                  ),
                  const SizedBox(height: 14),
                  TextField(
                    controller: _urlController,
                    decoration: const InputDecoration(
                      labelText: 'API Endpoint Host',
                      hintText: 'http://127.0.0.1:8000',
                      prefixIcon: Icon(Icons.dns_rounded, color: WildlifeTheme.primaryEmerald),
                    ),
                  ),
                  const SizedBox(height: 12),

                  // Quick presets
                  Wrap(
                    spacing: 8,
                    children: [
                      ActionChip(
                        label: const Text('Localhost (127.0.0.1:8000)', style: TextStyle(fontSize: 11)),
                        backgroundColor: WildlifeTheme.cardSurfaceLight,
                        onPressed: () {
                          setState(() => _urlController.text = 'http://127.0.0.1:8000');
                        },
                      ),
                      ActionChip(
                        label: const Text('Android Emulator (10.0.2.2:8000)', style: TextStyle(fontSize: 11)),
                        backgroundColor: WildlifeTheme.cardSurfaceLight,
                        onPressed: () {
                          setState(() => _urlController.text = 'http://10.0.2.2:8000');
                        },
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),

                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: _isTesting ? null : _testHealth,
                          icon: _isTesting
                              ? const SizedBox(
                                  width: 16,
                                  height: 16,
                                  child: CircularProgressIndicator(strokeWidth: 2, color: WildlifeTheme.accentCyan),
                                )
                              : const Icon(Icons.bolt_rounded, size: 18),
                          label: const Text('Test Connection & AI Health'),
                          style: OutlinedButton.styleFrom(
                            foregroundColor: WildlifeTheme.accentCyan,
                            side: const BorderSide(color: WildlifeTheme.accentCyan),
                            padding: const EdgeInsets.symmetric(vertical: 12),
                          ),
                        ),
                      ),
                      const SizedBox(width: 10),
                      ElevatedButton(
                        onPressed: _saveSettings,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: WildlifeTheme.primaryEmerald,
                          foregroundColor: Colors.black,
                          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
                        ),
                        child: const Text('Save'),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Health Result Banner
            if (_healthInfo != null)
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: WildlifeTheme.primaryEmerald.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: WildlifeTheme.primaryEmerald),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Row(
                      children: [
                        Icon(Icons.check_circle, color: WildlifeTheme.primaryEmerald, size: 20),
                        SizedBox(width: 8),
                        Text(
                          'Backend Connected & Healthy',
                          style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.bold,
                            color: WildlifeTheme.primaryEmerald,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    Text(
                      '• Landscape: ${_healthInfo!['landscape'] ?? 'Pench Tiger Reserve'}\n'
                      '• Device: ${_healthInfo!['device'] ?? 'CPU Edge'}\n'
                      '• Models: ${_healthInfo!['models']?['reid'] ?? 'SIFT + ResNet-50'}\n'
                      '• Flank Guard: ${_healthInfo!['models']?['step_9a_guard'] ?? 'Active'}\n'
                      '• BBox Resolver: ${_healthInfo!['models']?['step_9b_resolver'] ?? 'Active'}',
                      style: const TextStyle(fontSize: 12, color: WildlifeTheme.textPrimary, height: 1.5),
                    ),
                  ],
                ),
              ),

            if (_testError != null)
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: WildlifeTheme.dangerRed.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: WildlifeTheme.dangerRed),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.error_outline, color: WildlifeTheme.dangerRed, size: 20),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'Connection Error: $_testError',
                        style: const TextStyle(fontSize: 12, color: WildlifeTheme.dangerRed),
                      ),
                    ),
                  ],
                ),
              ),
            const SizedBox(height: 16),

            // Field Officer Config Card
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                color: WildlifeTheme.cardSurface,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: WildlifeTheme.cardBorder),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Field Officer Identity',
                    style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: WildlifeTheme.textPrimary),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _officerController,
                    decoration: const InputDecoration(
                      labelText: 'Patrol Officer ID / Badge',
                      prefixIcon: Icon(Icons.badge_outlined, color: WildlifeTheme.tigerAmber),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Maintenance / Reset
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                color: WildlifeTheme.cardSurface,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: WildlifeTheme.cardBorder),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Local Storage Maintenance',
                    style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: WildlifeTheme.textPrimary),
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    'Manage local image references and queued unsynced logs.',
                    style: TextStyle(fontSize: 12, color: WildlifeTheme.textMuted),
                  ),
                  const SizedBox(height: 14),
                  OutlinedButton.icon(
                    onPressed: _clearLocalQueue,
                    icon: const Icon(Icons.delete_outline, size: 18),
                    label: const Text('Purge Local Cache'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: WildlifeTheme.dangerRed,
                      side: const BorderSide(color: WildlifeTheme.dangerRed),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }
}
