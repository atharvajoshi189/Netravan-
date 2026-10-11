import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

import 'endpoints.dart';
import '../config/app_config.dart';
import '../models/analysis_result.dart';
import '../models/observation_record.dart';

class ApiException implements Exception {
  final String message;
  final int? statusCode;
  final dynamic details;

  ApiException(this.message, {this.statusCode, this.details});

  @override
  String toString() => 'ApiException: $message (Status: $statusCode)';
}

class ApiClient {
  final http.Client _client;

  ApiClient({http.Client? client}) : _client = client ?? http.Client();

  /// Tests connectivity and retrieves backend model health status.
  Future<Map<String, dynamic>> testConnection() async {
    try {
      final uri = Uri.parse(Endpoints.health);
      final res = await _client.get(uri).timeout(const Duration(seconds: 8));

      if (res.statusCode == 200) {
        return jsonDecode(res.body) as Map<String, dynamic>;
      } else {
        throw ApiException(
          'Server returned HTTP ${res.statusCode}',
          statusCode: res.statusCode,
        );
      }
    } on TimeoutException {
      throw ApiException('Connection timed out. Ensure the backend server is running at ${AppConfig.baseUrl}');
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Unable to connect to server: ${e.toString()}');
    }
  }

  /// Alias for testConnection
  Future<Map<String, dynamic>> checkHealth() => testConnection();

  /// Sends a single photo as File for automated AI detection, flank crop & Re-ID.
  Future<AnalysisResult> analyzeImage({
    required File imageFile,
    double? latitude,
    double? longitude,
    String? stationId,
    String? flankHint,
    String? fieldOfficer,
    String? notes,
  }) async {
    final bytes = await imageFile.readAsBytes();
    final filename = imageFile.uri.pathSegments.isNotEmpty
        ? imageFile.uri.pathSegments.last
        : 'capture.jpg';

    return analyzePhoto(
      imageBytes: bytes,
      filename: filename,
      latitude: latitude,
      longitude: longitude,
      stationId: stationId,
      flankHint: flankHint,
      fieldOfficer: fieldOfficer,
      notes: notes,
    );
  }

  /// Sends a single photo for automated AI detection, flank crop & Re-ID.
  Future<AnalysisResult> analyzePhoto({
    required Uint8List imageBytes,
    required String filename,
    double? latitude,
    double? longitude,
    String? stationId,
    String? flankHint,
    String? fieldOfficer,
    String? notes,
  }) async {
    if (imageBytes.isEmpty) {
      throw ApiException('Selected photo is empty (0 bytes). Please pick or capture a valid image.');
    }

    try {
      final uri = Uri.parse(Endpoints.analyze);
      final req = http.MultipartRequest('POST', uri);

      // Determine content-type
      String mimeType = 'image/jpeg';
      if (filename.toLowerCase().endsWith('.png')) {
        mimeType = 'image/png';
      } else if (filename.toLowerCase().endsWith('.webp')) {
        mimeType = 'image/webp';
      }

      final splitType = mimeType.split('/');
      req.files.add(http.MultipartFile.fromBytes(
        'file',
        imageBytes,
        filename: filename,
        contentType: MediaType(splitType[0], splitType[1]),
      ));

      if (stationId != null) req.fields['station_id'] = stationId;
      if (latitude != null) req.fields['latitude'] = latitude.toString();
      if (longitude != null) req.fields['longitude'] = longitude.toString();
      if (flankHint != null) req.fields['flank_hint'] = flankHint;
      if (fieldOfficer != null) req.fields['field_officer'] = fieldOfficer;
      if (notes != null) req.fields['notes'] = notes;
      req.fields['timestamp'] = DateTime.now().toUtc().toIso8601String();

      final streamedRes = await _client.send(req).timeout(const Duration(seconds: 40));
      final res = await http.Response.fromStream(streamedRes).timeout(const Duration(seconds: 40));

      if (res.statusCode == 200) {
        final Map<String, dynamic> data = jsonDecode(res.body);
        return AnalysisResult.fromJson(data);
      } else {
        String errMsg = 'Failed to analyze photo (HTTP ${res.statusCode})';
        try {
          final errBody = jsonDecode(res.body);
          if (errBody is Map && errBody.containsKey('detail')) {
            errMsg = errBody['detail'].toString();
          }
        } catch (_) {}
        throw ApiException(errMsg, statusCode: res.statusCode);
      }
    } on TimeoutException {
      throw ApiException('Analysis request timed out after 40s. Verify server at ${AppConfig.baseUrl}');
    } on SocketException catch (e) {
      throw ApiException('Cannot connect to AI backend at ${AppConfig.baseUrl}: ${e.message}');
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Network error during analysis: ${e.toString()}');
    }
  }

  /// Fetches recent observation records from server.
  Future<List<Map<String, dynamic>>> fetchRecentObservations({int limit = 50}) async {
    try {
      final uri = Uri.parse('${Endpoints.mobileObservations}?limit=$limit');
      final res = await _client.get(uri).timeout(const Duration(seconds: 10));

      if (res.statusCode == 200) {
        final dynamic data = jsonDecode(res.body);
        if (data is List) {
          return data.map((item) => item as Map<String, dynamic>).toList();
        } else if (data is Map && data['observations'] is List) {
          return (data['observations'] as List).map((item) => item as Map<String, dynamic>).toList();
        }
      }
      return [];
    } catch (_) {
      return [];
    }
  }

  /// Fetches resident tiger catalogue for offline field reference.
  Future<List<Map<String, dynamic>>> fetchResidentCatalogue() async {
    try {
      final uri = Uri.parse(Endpoints.mobileCatalogue);
      final res = await _client.get(uri).timeout(const Duration(seconds: 10));

      if (res.statusCode == 200) {
        final dynamic data = jsonDecode(res.body);
        if (data is List) {
          return data.map((item) => item as Map<String, dynamic>).toList();
        }
      }
      return [];
    } catch (_) {
      return [];
    }
  }

  /// Submits an offline batch for sync acknowledgment.
  Future<Map<String, dynamic>> syncBatchObservations(List<dynamic> items) async {
    try {
      final uri = Uri.parse(Endpoints.mobileSyncBatch);
      final body = jsonEncode({'items': items});
      final res = await _client
          .post(uri, headers: {'Content-Type': 'application/json'}, body: body)
          .timeout(const Duration(seconds: 15));
      if (res.statusCode == 200) {
        return jsonDecode(res.body) as Map<String, dynamic>;
      }
      return {'status': 'error', 'acknowledged_count': 0};
    } catch (_) {
      return {'status': 'error', 'acknowledged_count': 0};
    }
  }

  /// Submits an offline batch for sync acknowledgment (typed records).
  Future<bool> syncOfflineBatch(List<ObservationRecord> records) async {
    if (records.isEmpty) return true;
    final res = await syncBatchObservations(records.map((r) => r.toJson()).toList());
    return res['status'] == 'success';
  }
}
