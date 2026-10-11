import '../config/app_config.dart';

class Endpoints {
  static String get health => '${AppConfig.baseUrl}/api/health';
  static String get analyze => '${AppConfig.baseUrl}/api/analyze';
  static String get mobileObservations => '${AppConfig.baseUrl}/api/mobile/observations';
  static String get mobileCatalogue => '${AppConfig.baseUrl}/api/mobile/catalogue';
  static String get mobileSyncBatch => '${AppConfig.baseUrl}/api/mobile/sync_batch';
  static String get telemetry => '${AppConfig.baseUrl}/api/telemetry';

  static String resolveImageUrl(String? relativePathOrUrl) {
    if (relativePathOrUrl == null || relativePathOrUrl.isEmpty) {
      return '';
    }
    if (relativePathOrUrl.startsWith('http://') || relativePathOrUrl.startsWith('https://')) {
      return relativePathOrUrl;
    }
    if (relativePathOrUrl.startsWith('/')) {
      return '${AppConfig.baseUrl}$relativePathOrUrl';
    }
    return '${AppConfig.baseUrl}/$relativePathOrUrl';
  }
}
