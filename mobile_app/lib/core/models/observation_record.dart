import 'dart:convert';
import 'analysis_result.dart';

class ObservationRecord {
  final String localId;
  final String? serverId;
  final String? localImagePath;
  final String capturedAt;
  final String syncStatus; // 'synced', 'pending_upload', 'failed'
  final AnalysisResult? result;
  final double? latitude;
  final double? longitude;
  final String? stationId;
  final String flankHint;
  final String? notes;

  ObservationRecord({
    required this.localId,
    this.serverId,
    this.localImagePath,
    required this.capturedAt,
    this.syncStatus = 'synced',
    this.result,
    this.latitude,
    this.longitude,
    this.stationId,
    this.flankHint = 'unknown',
    this.notes,
  });

  bool get isSynced => syncStatus == 'synced';
  bool get isPending => syncStatus == 'pending_upload';

  String get species => result?.species ?? 'tiger';
  String get identityStatus => result?.identityStatus ?? (isSynced ? 'verified_match' : 'pending_sync');
  String? get candidateId => result?.assignedIdentity ?? (result?.candidateIdentities.isNotEmpty == true ? result!.candidateIdentities.first.tigerId : null);
  double? get topScore => (result?.topScore ?? 0) > 0 ? result!.topScore : (result?.candidateIdentities.isNotEmpty == true ? result!.candidateIdentities.first.score : null);

  ObservationRecord copyWith({
    String? localId,
    String? serverId,
    String? localImagePath,
    String? capturedAt,
    String? syncStatus,
    AnalysisResult? result,
    double? latitude,
    double? longitude,
    String? stationId,
    String? flankHint,
    String? notes,
  }) {
    return ObservationRecord(
      localId: localId ?? this.localId,
      serverId: serverId ?? this.serverId,
      localImagePath: localImagePath ?? this.localImagePath,
      capturedAt: capturedAt ?? this.capturedAt,
      syncStatus: syncStatus ?? this.syncStatus,
      result: result ?? this.result,
      latitude: latitude ?? this.latitude,
      longitude: longitude ?? this.longitude,
      stationId: stationId ?? this.stationId,
      flankHint: flankHint ?? this.flankHint,
      notes: notes ?? this.notes,
    );
  }

  factory ObservationRecord.fromJson(Map<String, dynamic> json) {
    return ObservationRecord(
      localId: json['local_id'] ?? DateTime.now().millisecondsSinceEpoch.toString(),
      serverId: json['server_id'],
      localImagePath: json['local_image_path'],
      capturedAt: json['captured_at'] ?? DateTime.now().toIso8601String(),
      syncStatus: json['sync_status'] ?? 'synced',
      result: json['result'] != null ? AnalysisResult.fromJson(json['result']) : null,
      latitude: (json['latitude'] as num?)?.toDouble(),
      longitude: (json['longitude'] as num?)?.toDouble(),
      stationId: json['station_id'],
      flankHint: json['flank_hint'] ?? 'unknown',
      notes: json['notes'],
    );
  }

  Map<String, dynamic> toJson() => {
    'local_id': localId,
    'server_id': serverId,
    'local_image_path': localImagePath,
    'captured_at': capturedAt,
    'sync_status': syncStatus,
    'result': result?.toJson(),
    'latitude': latitude,
    'longitude': longitude,
    'station_id': stationId,
    'flank_hint': flankHint,
    'notes': notes,
  };

  static String encodeList(List<ObservationRecord> records) {
    return jsonEncode(records.map((r) => r.toJson()).toList());
  }

  static List<ObservationRecord> decodeList(String jsonStr) {
    if (jsonStr.isEmpty) return [];
    try {
      final List<dynamic> list = jsonDecode(jsonStr);
      return list.map((item) => ObservationRecord.fromJson(item as Map<String, dynamic>)).toList();
    } catch (_) {
      return [];
    }
  }
}
