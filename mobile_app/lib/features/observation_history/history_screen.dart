import 'dart:io';
import 'package:flutter/material.dart';
import '../../core/api/api_client.dart';
import '../../core/config/theme.dart';
import '../../core/models/observation_record.dart';
import '../../core/services/offline_queue.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final ApiClient _apiClient = ApiClient();

  List<ObservationRecord> _localObservations = [];
  List<Map<String, dynamic>> _remoteObservations = [];
  bool _isLoading = false;
  bool _isSyncing = false;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadAll();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadAll() async {
    setState(() => _isLoading = true);

    final locals = await OfflineQueue.getAllObservations();
    _localObservations = locals;

    try {
      final remoteList = await _apiClient.fetchRecentObservations(limit: 30);
      _remoteObservations = remoteList;
    } catch (_) {
      // Backend might be offline; local data still works
    }

    if (mounted) {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _syncPendingObservations() async {
    final pending = await OfflineQueue.getPendingSync();
    if (pending.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('All local observations are already synced!'),
          backgroundColor: WildlifeTheme.primaryEmerald,
        ),
      );
      return;
    }

    setState(() => _isSyncing = true);

    try {
      final payload = pending.map((r) => r.toJson()).toList();
      final res = await _apiClient.syncBatchObservations(payload);

      // Mark locally as synced
      for (final p in pending) {
        await OfflineQueue.markAsSynced(p.localId, 'REMOTE-${p.localId}');
      }

      await _loadAll();

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('✓ Successfully synced ${res['acknowledged_count'] ?? pending.length} records!'),
            backgroundColor: WildlifeTheme.primaryEmerald,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Batch sync failed: $e'),
            backgroundColor: WildlifeTheme.dangerRed,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isSyncing = false);
      }
    }
  }

  Color _getStatusColor(String? status) {
    if (status == null) return WildlifeTheme.textMuted;
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
      case 'unknown':
        return WildlifeTheme.accentCyan;
      case 'pending_sync':
      case 'pending_upload':
        return WildlifeTheme.tigerAmber;
      default:
        return WildlifeTheme.textMuted;
    }
  }

  @override
  Widget build(BuildContext context) {
    final pendingCount = _localObservations.where((r) => !r.isSynced).length;

    return Scaffold(
      backgroundColor: WildlifeTheme.darkBg,
      appBar: AppBar(
        title: const Text('Field Observations History'),
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: WildlifeTheme.primaryEmerald,
          labelColor: WildlifeTheme.primaryEmerald,
          unselectedLabelColor: WildlifeTheme.textMuted,
          tabs: [
            Tab(
              icon: const Icon(Icons.phone_android, size: 20),
              text: 'Device Logs (${_localObservations.length})',
            ),
            Tab(
              icon: const Icon(Icons.cloud_done, size: 20),
              text: 'Server Ingested (${_remoteObservations.length})',
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: _isSyncing
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2, color: WildlifeTheme.primaryEmerald),
                  )
                : const Icon(Icons.sync),
            tooltip: 'Sync Offline Queue',
            onPressed: _isSyncing ? null : _syncPendingObservations,
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Reload',
            onPressed: _loadAll,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: WildlifeTheme.primaryEmerald))
          : TabBarView(
              controller: _tabController,
              children: [
                _buildLocalTab(pendingCount),
                _buildRemoteTab(),
              ],
            ),
    );
  }

  Widget _buildLocalTab(int pendingCount) {
    if (_localObservations.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.history_toggle_off, size: 64, color: WildlifeTheme.textMuted.withOpacity(0.4)),
            const SizedBox(height: 12),
            const Text(
              'No field observations recorded on device yet',
              style: TextStyle(color: WildlifeTheme.textSecondary, fontSize: 15),
            ),
            const SizedBox(height: 4),
            const Text(
              'Use the Scanner tab to capture tiger images',
              style: TextStyle(color: WildlifeTheme.textMuted, fontSize: 12),
            ),
          ],
        ),
      );
    }

    return Column(
      children: [
        if (pendingCount > 0)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            color: WildlifeTheme.tigerAmber.withOpacity(0.15),
            child: Row(
              children: [
                const Icon(Icons.cloud_upload_outlined, color: WildlifeTheme.tigerAmber, size: 20),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    '$pendingCount offline observation(s) awaiting server sync.',
                    style: const TextStyle(
                      color: WildlifeTheme.tigerAmber,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                TextButton(
                  onPressed: _syncPendingObservations,
                  child: const Text('SYNC NOW', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                ),
              ],
            ),
          ),
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.all(12),
            itemCount: _localObservations.length,
            itemBuilder: (context, index) {
              final obs = _localObservations[index];
              return _buildLocalCard(obs);
            },
          ),
        ),
      ],
    );
  }

  Widget _buildLocalCard(ObservationRecord obs) {
    final statusColor = _getStatusColor(obs.identityStatus);

    return Card(
      color: WildlifeTheme.cardSurface,
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: const BorderSide(color: WildlifeTheme.cardBorder),
      ),
      child: Padding(
        padding: const EdgeInsets.all(14.0),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Thumbnail
            ClipRRect(
              borderRadius: BorderRadius.circular(10),
              child: Container(
                width: 64,
                height: 64,
                color: WildlifeTheme.cardSurfaceLight,
                child: obs.localImagePath != null && File(obs.localImagePath!).existsSync()
                    ? Image.file(File(obs.localImagePath!), fit: BoxFit.cover)
                    : const Icon(Icons.pets, color: WildlifeTheme.textMuted),
              ),
            ),
            const SizedBox(width: 14),

            // Content
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        obs.candidateId ?? obs.species.toUpperCase(),
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: WildlifeTheme.textPrimary,
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: statusColor.withOpacity(0.15),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: statusColor, width: 0.8),
                        ),
                        child: Text(
                          obs.identityStatus.replaceAll('_', ' ').toUpperCase(),
                          style: TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                            color: statusColor,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Station: ${obs.stationId ?? "FIELD"} • ${obs.capturedAt.split('T').first}',
                    style: const TextStyle(fontSize: 12, color: WildlifeTheme.textMuted),
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      Icon(
                        obs.isSynced ? Icons.cloud_done : Icons.cloud_off,
                        size: 14,
                        color: obs.isSynced ? WildlifeTheme.primaryEmerald : WildlifeTheme.tigerAmber,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        obs.isSynced ? 'Synced to Command' : 'Stored Locally',
                        style: TextStyle(
                          fontSize: 11,
                          color: obs.isSynced ? WildlifeTheme.primaryEmerald : WildlifeTheme.tigerAmber,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      if (obs.topScore != null) ...[
                        const Spacer(),
                        Text(
                          'Score: ${(obs.topScore! * 100).toStringAsFixed(1)}%',
                          style: const TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                            color: WildlifeTheme.textSecondary,
                          ),
                        ),
                      ],
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRemoteTab() {
    if (_remoteObservations.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.cloud_sync, size: 64, color: WildlifeTheme.textMuted.withOpacity(0.4)),
            const SizedBox(height: 12),
            const Text(
              'No remote observations fetched from server',
              style: TextStyle(color: WildlifeTheme.textSecondary, fontSize: 15),
            ),
            const SizedBox(height: 4),
            const Text(
              'Verify server connection in Settings',
              style: TextStyle(color: WildlifeTheme.textMuted, fontSize: 12),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(12),
      itemCount: _remoteObservations.length,
      itemBuilder: (context, index) {
        final obs = _remoteObservations[index];
        final tigerId = obs['tiger_id'] as String?;
        final stationId = obs['station_id'] as String? ?? 'N/A';
        final status = obs['review_status'] as String? ?? 'pending';
        final timestamp = obs['timestamp'] as String? ?? '';
        final score = (obs['confidence'] as num?)?.toDouble();

        return Card(
          color: WildlifeTheme.cardSurface,
          margin: const EdgeInsets.only(bottom: 12),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
            side: const BorderSide(color: WildlifeTheme.cardBorder),
          ),
          child: ListTile(
            leading: const CircleAvatar(
              backgroundColor: WildlifeTheme.cardSurfaceLight,
              child: Text('🐅'),
            ),
            title: Text(
              tigerId ?? 'UNKNOWN TIGER',
              style: const TextStyle(fontWeight: FontWeight.bold, color: WildlifeTheme.textPrimary),
            ),
            subtitle: Text(
              'Station: $stationId\nTime: $timestamp',
              style: const TextStyle(fontSize: 11, color: WildlifeTheme.textMuted),
            ),
            trailing: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: status == 'approved'
                        ? WildlifeTheme.primaryEmerald.withOpacity(0.15)
                        : WildlifeTheme.tigerAmber.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: status == 'approved' ? WildlifeTheme.primaryEmerald : WildlifeTheme.tigerAmber,
                    ),
                  ),
                  child: Text(
                    status.toUpperCase(),
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      color: status == 'approved' ? WildlifeTheme.primaryEmerald : WildlifeTheme.tigerAmber,
                    ),
                  ),
                ),
                if (score != null) ...[
                  const SizedBox(height: 4),
                  Text(
                    '${(score * 100).toStringAsFixed(1)}%',
                    style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: WildlifeTheme.textSecondary),
                  ),
                ],
              ],
            ),
          ),
        );
      },
    );
  }
}
