import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class AppConfig {
  static const String defaultLocalHost = '127.0.0.1';
  static const String defaultAndroidEmulatorHost = '10.0.2.2';
  static const int defaultPort = 8000;

  static String getDefaultBaseUrl() {
    // 127.0.0.1 works on Web, Desktop, and physical Android devices via USB ADB reverse
    return 'http://$defaultLocalHost:$defaultPort';
  }

  static String _baseUrl = getDefaultBaseUrl();
  static String _fieldOfficerId = 'Ranger_Sharma_PTR_04';
  static String _defaultStationId = 'PTR_STN_02';
  static bool _gpsEnabled = true;

  static String get baseUrl => _baseUrl;
  static String get fieldOfficerId => _fieldOfficerId;
  static String get officerId => _fieldOfficerId;
  static String get defaultStationId => _defaultStationId;
  static String get defaultStation => _defaultStationId;
  static bool get gpsEnabled => _gpsEnabled;

  static Future<void> init() async {
    await loadSettings();
  }

  static Future<void> loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    final savedUrl = prefs.getString('base_url');
    if (savedUrl != null && savedUrl.trim().isNotEmpty) {
      _baseUrl = savedUrl.trim();
    } else {
      // Auto-detect reachable backend: test 127.0.0.1 (USB adb reverse / local) first
      _baseUrl = await _detectReachableBaseUrl();
    }
    _fieldOfficerId = prefs.getString('field_officer_id') ?? 'Ranger_Sharma_PTR_04';
    _defaultStationId = prefs.getString('default_station_id') ?? 'PTR_STN_02';
    _gpsEnabled = prefs.getBool('gps_enabled') ?? true;
  }

  static Future<String> _detectReachableBaseUrl() async {
    final localUrl = 'http://$defaultLocalHost:$defaultPort';
    if (!kIsWeb && defaultTargetPlatform == TargetPlatform.android) {
      // Test 127.0.0.1 (ADB reverse for physical phone)
      try {
        final res = await http.get(Uri.parse('$localUrl/api/health')).timeout(const Duration(milliseconds: 600));
        if (res.statusCode == 200) return localUrl;
      } catch (_) {}

      // If 127.0.0.1 didn't respond, test 10.0.2.2 (Android Studio emulator)
      final emuUrl = 'http://$defaultAndroidEmulatorHost:$defaultPort';
      try {
        final res = await http.get(Uri.parse('$emuUrl/api/health')).timeout(const Duration(milliseconds: 600));
        if (res.statusCode == 200) return emuUrl;
      } catch (_) {}
    }
    return localUrl;
  }

  static Future<void> setBaseUrl(String url) async {
    await updateSettings(baseUrl: url);
  }

  static Future<void> setOfficerId(String id) async {
    await updateSettings(fieldOfficerId: id);
  }

  static Future<void> updateSettings({
    String? baseUrl,
    String? fieldOfficerId,
    String? defaultStationId,
    bool? gpsEnabled,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    if (baseUrl != null) {
      _baseUrl = baseUrl.trim();
      await prefs.setString('base_url', _baseUrl);
    }
    if (fieldOfficerId != null) {
      _fieldOfficerId = fieldOfficerId.trim();
      await prefs.setString('field_officer_id', _fieldOfficerId);
    }
    if (defaultStationId != null) {
      _defaultStationId = defaultStationId.trim();
      await prefs.setString('default_station_id', _defaultStationId);
    }
    if (gpsEnabled != null) {
      _gpsEnabled = gpsEnabled;
      await prefs.setBool('gps_enabled', _gpsEnabled);
    }
  }
}
