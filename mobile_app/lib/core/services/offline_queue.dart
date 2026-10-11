import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/observation_record.dart';

/// Manages local offline storage and sync queue for field observations.
class OfflineQueue {
  static const String _storageKey = 'tigertrace_offline_observations';

  /// Save an observation record locally.
  static Future<void> saveObservation(ObservationRecord record) async {
    final prefs = await SharedPreferences.getInstance();
    final list = await getAllObservations();
    
    // Replace if exists, else prepend
    final existingIndex = list.indexWhere((r) => r.localId == record.localId);
    if (existingIndex >= 0) {
      list[existingIndex] = record;
    } else {
      list.insert(0, record);
    }

    final encodedList = list.map((r) => jsonEncode(r.toJson())).toList();
    await prefs.setStringList(_storageKey, encodedList);
  }

  /// Retrieve all stored observations (newest first).
  static Future<List<ObservationRecord>> getAllObservations() async {
    final prefs = await SharedPreferences.getInstance();
    final stringList = prefs.getStringList(_storageKey) ?? [];
    
    final records = <ObservationRecord>[];
    for (final item in stringList) {
      try {
        final map = jsonDecode(item) as Map<String, dynamic>;
        records.add(ObservationRecord.fromJson(map));
      } catch (_) {
        // Skip corrupted entries
      }
    }
    return records;
  }

  /// Retrieve unsynced observations.
  static Future<List<ObservationRecord>> getPendingSync() async {
    final all = await getAllObservations();
    return all.where((r) => !r.isSynced).toList();
  }

  /// Mark a local observation as synced with its remote ID.
  static Future<void> markAsSynced(String localId, String remoteId) async {
    final list = await getAllObservations();
    final idx = list.indexWhere((r) => r.localId == localId);
    if (idx >= 0) {
      list[idx] = list[idx].copyWith(
        syncStatus: 'synced',
        serverId: remoteId,
      );
      final prefs = await SharedPreferences.getInstance();
      final encodedList = list.map((r) => jsonEncode(r.toJson())).toList();
      await prefs.setStringList(_storageKey, encodedList);
    }
  }

  /// Remove an observation from local storage.
  static Future<void> deleteObservation(String localId) async {
    final list = await getAllObservations();
    list.removeWhere((r) => r.localId == localId);
    final prefs = await SharedPreferences.getInstance();
    final encodedList = list.map((r) => jsonEncode(r.toJson())).toList();
    await prefs.setStringList(_storageKey, encodedList);
  }

  /// Clear all local observations.
  static Future<void> clearAll() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_storageKey);
  }
}
