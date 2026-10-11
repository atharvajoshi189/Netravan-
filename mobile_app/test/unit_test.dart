import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tigertrace_mobile/core/config/app_config.dart';
import 'package:tigertrace_mobile/core/models/analysis_result.dart';
import 'package:tigertrace_mobile/core/models/observation_record.dart';
import 'package:tigertrace_mobile/core/services/offline_queue.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  group('AnalysisResult Model Tests', () {
    test('Parse full API response successfully', () {
      final jsonSample = {
        'status': 'success',
        'observation_id': 101,
        'species': 'tiger',
        'species_confidence': 0.965,
        'identity_status': 'verified_match',
        'assigned_identity': 'BAJIRAO',
        'assigned_name': 'Bajirao (T-24)',
        'top_score': 0.9856,
        'sift_score': 0.85,
        'cosine_score': 0.99,
        'flank_side': 'left',
        'candidate_identities': [
          {
            'tiger_id': 'BAJIRAO',
            'name': 'Bajirao (T-24)',
            'score': 0.9856,
            'sift_score': 0.85,
            'cosine_score': 0.99,
            'flank': 'left',
          }
        ],
        'decision_reason': 'High-confidence stripe minutiae match',
        'behaviour_estimate': {
          'status': 'active',
          'current_station': 'STATION-01',
          'predicted_next_stations': ['STATION-02'],
          'notes': 'Normal corridor roaming pattern',
        },
        'location': {
          'station_id': 'STATION-01',
          'range_name': 'Turia Core',
          'zone': 'core',
          'latitude': 21.65,
          'longitude': 79.25,
        },
        'timestamp': '2026-10-10T12:00:00Z',
        'review_status': 'approved',
        'model_versions': {
          'detector': 'yolov8n-pench',
          'reid': 'HotSpotter SIFT + ResNet-50',
          'flank_guard': 'Step 9A Active',
        },
      };

      final result = AnalysisResult.fromJson(jsonSample);

      expect(result.status, 'success');
      expect(result.observationId, 101);
      expect(result.species, 'tiger');
      expect(result.speciesConfidence, 0.965);
      expect(result.identityStatus, 'verified_match');
      expect(result.assignedIdentity, 'BAJIRAO');
      expect(result.candidateIdentities.length, 1);
      expect(result.candidateIdentities.first.tigerId, 'BAJIRAO');
      expect(result.topScore, 0.9856);
      expect(result.behaviourEstimate?.status, 'active');
      expect(result.location?.stationId, 'STATION-01');
      expect(result.modelVersions['reid'], 'HotSpotter SIFT + ResNet-50');
    });

    test('Parse unknown / blank detection result gracefully', () {
      final jsonBlank = {
        'status': 'success',
        'species': 'unknown',
        'identity_status': 'no_animal_detected',
        'decision_reason': 'No animal detected in field frame',
        'candidate_identities': [],
      };

      final result = AnalysisResult.fromJson(jsonBlank);
      expect(result.species, 'unknown');
      expect(result.identityStatus, 'no_animal_detected');
      expect(result.candidateIdentities.isEmpty, true);
    });
  });

  group('OfflineQueue & ObservationRecord Tests', () {
    test('Save and retrieve offline observation records', () async {
      await AppConfig.init();

      final record = ObservationRecord(
        localId: 'LOC-001',
        capturedAt: '2026-10-10T15:30:00Z',
        stationId: 'STATION-01',
        syncStatus: 'pending_upload',
        notes: 'Offline capture',
      );

      await OfflineQueue.saveObservation(record);

      final stored = await OfflineQueue.getAllObservations();
      expect(stored.length, 1);
      expect(stored.first.localId, 'LOC-001');
      expect(stored.first.isSynced, false);

      final pending = await OfflineQueue.getPendingSync();
      expect(pending.length, 1);

      // Mark synced
      await OfflineQueue.markAsSynced('LOC-001', 'SRV-001');
      final updated = await OfflineQueue.getAllObservations();
      expect(updated.first.isSynced, true);
      expect(updated.first.serverId, 'SRV-001');

      final pendingAfter = await OfflineQueue.getPendingSync();
      expect(pendingAfter.isEmpty, true);
    });
  });
}
