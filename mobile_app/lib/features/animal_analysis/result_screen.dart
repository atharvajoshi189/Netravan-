import 'dart:io';
import 'package:flutter/material.dart';
import '../../core/config/theme.dart';
import '../../core/models/analysis_result.dart';
import '../../core/models/observation_record.dart';
import '../../core/services/offline_queue.dart';

class ResultScreen extends StatefulWidget {
  final AnalysisResult result;
  final String? localImagePath;

  const ResultScreen({
    super.key,
    required this.result,
    this.localImagePath,
  });

  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen> {
  bool _saved = false;

  Future<void> _saveToLocalHistory() async {
    final res = widget.result;

    final record = ObservationRecord(
      localId: DateTime.now().millisecondsSinceEpoch.toString(),
      serverId: res.observationId?.toString(),
      capturedAt: res.timestamp,
      stationId: res.location?.stationId ?? 'MOBILE-PATROL',
      result: res,
      localImagePath: widget.localImagePath,
      syncStatus: 'synced',
    );

    await OfflineQueue.saveObservation(record);
    setState(() {
      _saved = true;
    });

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('✓ Observation saved to local field log'),
          backgroundColor: WildlifeTheme.primaryEmerald,
        ),
      );
    }
  }

  Color _getStatusColor(String status) {
    switch (status.toLowerCase()) {
      case 'verified_match':
      case 'verified':
        return WildlifeTheme.primaryEmerald;
      case 'candidate_match':
        return WildlifeTheme.tigerAmber;
      case 'review_required':
      case 'ambiguous':
        return const Color(0xFFF97316);
      case 'unknown_new_enrollment':
      case 'new_identity_candidate':
      case 'unknown':
        return WildlifeTheme.accentCyan;
      case 'no_animal_detected':
      case 'blank':
        return WildlifeTheme.textMuted;
      default:
        return WildlifeTheme.tigerAmber;
    }
  }

  String _formatStatusLabel(String status) {
    return status.replaceAll('_', ' ').toUpperCase();
  }

  @override
  Widget build(BuildContext context) {
    final res = widget.result;
    final statusColor = _getStatusColor(res.identityStatus);
    final topCand = res.candidateIdentities.isNotEmpty ? res.candidateIdentities.first : null;
    final displayId = res.assignedIdentity ?? topCand?.tigerId;
    final displayName = res.assignedName ?? topCand?.name;

    return Scaffold(
      backgroundColor: WildlifeTheme.darkBg,
      appBar: AppBar(
        title: const Text('Field Biometric Result'),
        actions: [
          IconButton(
            icon: Icon(_saved ? Icons.bookmark_added : Icons.bookmark_border),
            color: _saved ? WildlifeTheme.primaryEmerald : WildlifeTheme.textPrimary,
            tooltip: 'Save Observation',
            onPressed: _saved ? null : _saveToLocalHistory,
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Image Preview & Quick Tag
            if (widget.localImagePath != null && File(widget.localImagePath!).existsSync()) ...[
              ClipRRect(
                borderRadius: BorderRadius.circular(16),
                child: Container(
                  height: 220,
                  decoration: BoxDecoration(
                    color: WildlifeTheme.cardSurface,
                    border: Border.all(color: statusColor.withOpacity(0.5), width: 1.5),
                  ),
                  child: Stack(
                    fit: StackFit.expand,
                    children: [
                      Image.file(
                        File(widget.localImagePath!),
                        fit: BoxFit.cover,
                      ),
                      Positioned(
                        top: 12,
                        left: 12,
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: Colors.black.withOpacity(0.75),
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(color: statusColor),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(Icons.radar, size: 14, color: statusColor),
                              const SizedBox(width: 6),
                              Text(
                                _formatStatusLabel(res.identityStatus),
                                style: TextStyle(
                                  color: statusColor,
                                  fontSize: 11,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                      if (res.speciesConfidence > 0)
                        Positioned(
                          bottom: 12,
                          right: 12,
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(
                              color: Colors.black.withOpacity(0.75),
                              borderRadius: BorderRadius.circular(20),
                            ),
                            child: Text(
                              '${res.species.toUpperCase()} ${(res.speciesConfidence * 100).toStringAsFixed(1)}%',
                              style: const TextStyle(
                                color: WildlifeTheme.textPrimary,
                                fontSize: 11,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
            ],

            // Main Identity Card
            Container(
              decoration: BoxDecoration(
                color: WildlifeTheme.cardSurface,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: statusColor.withOpacity(0.4), width: 1.5),
                boxShadow: [
                  BoxShadow(
                    color: statusColor.withOpacity(0.1),
                    blurRadius: 16,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              displayId != null ? 'ID: $displayId' : 'SPECIES: ${res.species.toUpperCase()}',
                              style: const TextStyle(
                                fontSize: 22,
                                fontWeight: FontWeight.w800,
                                color: WildlifeTheme.textPrimary,
                              ),
                            ),
                            if (displayName != null) ...[
                              const SizedBox(height: 2),
                              Text(
                                displayName,
                                style: const TextStyle(
                                  fontSize: 15,
                                  fontWeight: FontWeight.w600,
                                  color: WildlifeTheme.tigerAmber,
                                ),
                              ),
                            ],
                          ],
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: statusColor.withOpacity(0.15),
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(color: statusColor),
                        ),
                        child: Text(
                          _formatStatusLabel(res.identityStatus),
                          style: TextStyle(
                            color: statusColor,
                            fontWeight: FontWeight.bold,
                            fontSize: 12,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  const Divider(color: WildlifeTheme.cardBorder, height: 1),
                  const SizedBox(height: 16),

                  // Confidence Metrics
                  Row(
                    children: [
                      Expanded(
                        child: _buildMetricTile(
                          'Composite Match',
                          '${((res.topScore > 0 ? res.topScore : (topCand?.score ?? 0.0)) * 100).toStringAsFixed(1)}%',
                          statusColor,
                        ),
                      ),
                      Expanded(
                        child: _buildMetricTile(
                          'SIFT Inliers',
                          (res.siftScore > 0 ? res.siftScore : (topCand?.siftScore ?? 0.0)).toStringAsFixed(2),
                          WildlifeTheme.accentCyan,
                        ),
                      ),
                      Expanded(
                        child: _buildMetricTile(
                          'ResNet Cosine',
                          (res.cosineScore > 0 ? res.cosineScore : (topCand?.cosineScore ?? 0.0)).toStringAsFixed(3),
                          WildlifeTheme.textSecondary,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),

                  // Decision Reason
                  Text(
                    'Biometric Decision:',
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: WildlifeTheme.textMuted,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: WildlifeTheme.cardSurfaceLight.withOpacity(0.5),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: WildlifeTheme.cardBorder),
                    ),
                    child: Text(
                      res.decisionReason,
                      style: const TextStyle(
                        fontSize: 13,
                        color: WildlifeTheme.textSecondary,
                        height: 1.4,
                      ),
                    ),
                  ),

                  // Review Queue Status
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Icon(
                        res.reviewStatus == 'approved' ? Icons.check_circle : Icons.pending_actions,
                        size: 16,
                        color: res.reviewStatus == 'approved'
                            ? WildlifeTheme.primaryEmerald
                            : WildlifeTheme.tigerAmber,
                      ),
                      const SizedBox(width: 6),
                      Text(
                        'Review Status: ${res.reviewStatus.toUpperCase()}',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: res.reviewStatus == 'approved'
                              ? WildlifeTheme.primaryEmerald
                              : WildlifeTheme.tigerAmber,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Behavior / Movement Intelligence Card
            if (res.behaviourEstimate != null && res.behaviourEstimate!.status != 'unavailable') ...[
              Container(
                decoration: BoxDecoration(
                  color: WildlifeTheme.cardSurface,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: WildlifeTheme.cardBorder),
                ),
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Row(
                      children: [
                        Text('🔮', style: TextStyle(fontSize: 18)),
                        SizedBox(width: 8),
                        Text(
                          'Behavioral & Spatial Forecast',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: WildlifeTheme.textPrimary,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    if (res.behaviourEstimate!.predictedNextStations.isNotEmpty)
                      _buildInfoRow(
                        'Projected Next Station:',
                        res.behaviourEstimate!.predictedNextStations.first.toString(),
                      ),
                    if (res.behaviourEstimate!.currentStation != null)
                      _buildInfoRow(
                        'Last Active Station:',
                        res.behaviourEstimate!.currentStation!,
                      ),
                    if (res.behaviourEstimate!.notes != null)
                      _buildInfoRow(
                        'Movement Notes:',
                        res.behaviourEstimate!.notes!,
                      ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
            ],

            // Provenance & Metadata Card
            Container(
              decoration: BoxDecoration(
                color: WildlifeTheme.cardSurface,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: WildlifeTheme.cardBorder),
              ),
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Provenance & Verification Audit',
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                      color: WildlifeTheme.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 12),
                  _buildInfoRow('Station ID:', res.location?.stationId ?? 'MOBILE-PATROL'),
                  _buildInfoRow('Timestamp:', res.timestamp),
                  _buildInfoRow('Observation Ref:', '${res.observationId ?? 'N/A'}'),
                  if (res.location != null)
                    _buildInfoRow(
                      'Location Coords:',
                      '${res.location!.latitude.toStringAsFixed(3)}, ${res.location!.longitude.toStringAsFixed(3)}',
                    ),
                  const SizedBox(height: 8),
                  const Divider(color: WildlifeTheme.cardBorder, height: 1),
                  const SizedBox(height: 8),
                  const Text(
                    'AI Pipeline Security & Guards:',
                    style: TextStyle(fontSize: 11, color: WildlifeTheme.textMuted, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '• YOLOv8 Detector (${res.modelVersions['detector'] ?? 'yolov8n'})\n'
                    '• Step 9B Bounding-Box Normalizer & CLAHE Extractor\n'
                    '• Step 9A Flank Compatibility Guard (Active)\n'
                    '• SIFT Stripe Minutiae + Deep Cosine ResNet-50\n'
                    '• Zero Fabricated Coordinates or Trajectories',
                    style: const TextStyle(fontSize: 11, color: WildlifeTheme.textMuted, height: 1.5),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // Bottom Action
            ElevatedButton.icon(
              onPressed: _saved ? () => Navigator.pop(context) : _saveToLocalHistory,
              icon: Icon(_saved ? Icons.done_all : Icons.save_alt_rounded),
              label: Text(_saved ? 'Close & Return to Scanner' : 'Save Field Observation'),
              style: ElevatedButton.styleFrom(
                backgroundColor: WildlifeTheme.primaryEmerald,
                foregroundColor: Colors.black,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Widget _buildMetricTile(String label, String value, Color color) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontSize: 11,
            color: WildlifeTheme.textMuted,
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          value,
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
      ],
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(fontSize: 12, color: WildlifeTheme.textMuted)),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              value,
              textAlign: TextAlign.end,
              style: const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: WildlifeTheme.textPrimary,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
