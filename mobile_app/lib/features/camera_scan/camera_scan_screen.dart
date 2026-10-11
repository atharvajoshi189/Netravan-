import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../../core/api/api_client.dart';
import '../../core/config/app_config.dart';
import '../../core/config/theme.dart';
import '../../core/models/observation_record.dart';
import '../../core/services/offline_queue.dart';
import '../animal_analysis/result_screen.dart';

class CameraScanScreen extends StatefulWidget {
  const CameraScanScreen({super.key});

  @override
  State<CameraScanScreen> createState() => _CameraScanScreenState();
}

class _CameraScanScreenState extends State<CameraScanScreen> with SingleTickerProviderStateMixin {
  final ImagePicker _picker = ImagePicker();
  final ApiClient _apiClient = ApiClient();

  File? _selectedImage;
  String? _selectedImagePath;
  String _flankHint = 'unknown';
  String _selectedStation = 'STATION-01';
  bool _isAnalyzing = false;
  String _analyzingStep = '';
  late AnimationController _reticleAnimation;

  final List<Map<String, String>> _stations = [
    {'id': 'STATION-01', 'name': 'STATION-01: Karmajhiri Gate'},
    {'id': 'STATION-02', 'name': 'STATION-02: Turia Core Track'},
    {'id': 'STATION-03', 'name': 'STATION-03: Alikatta Grasslands'},
    {'id': 'STATION-04', 'name': 'STATION-04: Bodanala Waterhole'},
    {'id': 'STATION-05', 'name': 'STATION-05: Jamtara Corridor'},
    {'id': 'PTR_STN_01', 'name': 'PTR_STN_01: Turia Core'},
    {'id': 'PTR_STN_02', 'name': 'PTR_STN_02: Karmajhiri Gate'},
    {'id': 'PTR_STN_03', 'name': 'PTR_STN_03: Bodanala Waterhole'},
    {'id': 'MOBILE-PATROL', 'name': 'MOBILE-PATROL: Live GPS Coordinate'},
  ];

  @override
  void initState() {
    super.initState();
    final hasMatch = _stations.any((s) => s['id'] == AppConfig.defaultStation);
    _selectedStation = hasMatch ? AppConfig.defaultStation : 'STATION-01';
    _reticleAnimation = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);
    _retrieveLostData();
  }

  Future<void> _retrieveLostData() async {
    try {
      final LostDataResponse response = await _picker.retrieveLostData();
      if (response.isEmpty) return;
      if (response.file != null) {
        final f = File(response.file!.path);
        if (f.existsSync() && f.lengthSync() > 0) {
          setState(() {
            _selectedImage = f;
            _selectedImagePath = f.path;
          });
        }
      }
    } catch (_) {}
  }

  @override
  void dispose() {
    _reticleAnimation.dispose();
    super.dispose();
  }

  Future<void> _pickImage(ImageSource source) async {
    try {
      final XFile? pickedFile = await _picker.pickImage(
        source: source,
        maxWidth: 1920,
        maxHeight: 1920,
        imageQuality: 90,
      );

      if (pickedFile != null) {
        final file = File(pickedFile.path);
        if (file.existsSync() && file.lengthSync() > 0) {
          setState(() {
            _selectedImage = file;
            _selectedImagePath = pickedFile.path;
          });
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Selected image is empty (0 bytes). Please try another image.'),
              backgroundColor: WildlifeTheme.dangerRed,
            ),
          );
        }
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Camera/Gallery error: $e'),
          backgroundColor: WildlifeTheme.dangerRed,
        ),
      );
    }
  }

  /// Preset sample images for rapid desktop/emulator evaluation
  void _selectPresetSample(String sampleType) {
    // Relative paths in workspace to test samples
    String path;
    switch (sampleType) {
      case 'bajirao':
        path = File('/data/data/com.tigertrace.ai.tigertrace_mobile/files/Bajirao_001.png').existsSync()
            ? '/data/data/com.tigertrace.ai.tigertrace_mobile/files/Bajirao_001.png'
            : (File('/sdcard/Download/Bajirao_001.png').existsSync()
                ? '/sdcard/Download/Bajirao_001.png'
                : 'd:\\TigerTraceAI-main\\data\\reference\\bajirao_left.jpg');
        _flankHint = 'left';
        break;
      case 'patdev':
        path = 'd:\\TigerTraceAI-main\\data\\reference\\patdev_left.jpg';
        _flankHint = 'left';
        break;
      case 'atrw_sample':
        path = 'd:\\TigerTraceAI-main\\data\\staging\\atrw_pilot\\images\\000008.jpg';
        _flankHint = 'unknown';
        break;
      case 'blank':
        path = 'd:\\TigerTraceAI-main\\data\\raw\\blank_1.jpg';
        _flankHint = 'unknown';
        break;
      default:
        return;
    }

    final file = File(path);
    if (file.existsSync() && file.lengthSync() > 0) {
      setState(() {
        _selectedImage = file;
        _selectedImagePath = file.path;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Loaded test sample: $sampleType'),
          backgroundColor: WildlifeTheme.primaryEmerald,
          duration: const Duration(seconds: 1),
        ),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Sample file not found at: $path'),
          backgroundColor: WildlifeTheme.dangerRed,
        ),
      );
    }
  }

  Future<void> _analyzeCapture() async {
    if (_selectedImage == null || !_selectedImage!.existsSync() || _selectedImage!.lengthSync() == 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please capture or select a valid animal image first'),
          backgroundColor: WildlifeTheme.tigerAmber,
        ),
      );
      return;
    }

    setState(() {
      _isAnalyzing = true;
      _analyzingStep = 'Connecting to TigerTrace AI backend (${AppConfig.baseUrl})...';
    });

    try {
      await Future.delayed(const Duration(milliseconds: 200));
      if (!mounted) return;
      setState(() => _analyzingStep = 'Running YOLOv8 animal detection & Step 9B BBox scaling...');

      final result = await _apiClient.analyzeImage(
        imageFile: _selectedImage!,
        flankHint: _flankHint,
        stationId: _selectedStation,
      );

      if (!mounted) return;
      setState(() => _analyzingStep = 'SIFT minutiae & deep cosine matching (Step 9A guard)...');
      await Future.delayed(const Duration(milliseconds: 200));

      if (!mounted) return;

      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => ResultScreen(
            result: result,
            localImagePath: _selectedImagePath,
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      _showErrorDialog(e.toString());
    } finally {
      if (mounted) {
        setState(() {
          _isAnalyzing = false;
        });
      }
    }
  }

  void _showErrorDialog(String error) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: WildlifeTheme.cardSurface,
        title: const Row(
          children: [
            Icon(Icons.cloud_off, color: WildlifeTheme.dangerRed),
            SizedBox(width: 8),
            Text('Network / Backend Issue', style: TextStyle(color: WildlifeTheme.textPrimary, fontSize: 18)),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Could not connect to shared AI backend at:\n${AppConfig.baseUrl}',
              style: const TextStyle(color: WildlifeTheme.textMuted, fontSize: 13),
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: Colors.black.withOpacity(0.4),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                error,
                style: const TextStyle(color: WildlifeTheme.dangerRed, fontSize: 12, fontFamily: 'monospace'),
              ),
            ),
            const SizedBox(height: 16),
            const Text(
              'You can save this capture locally in your offline queue. It will automatically sync once connectivity to the command server is restored.',
              style: TextStyle(color: WildlifeTheme.textSecondary, fontSize: 12),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel', style: TextStyle(color: WildlifeTheme.textMuted)),
          ),
          ElevatedButton.icon(
            onPressed: () async {
              Navigator.pop(ctx);
              await _saveOfflineQueueRecord();
            },
            icon: const Icon(Icons.archive, size: 16),
            label: const Text('Save Offline'),
            style: ElevatedButton.styleFrom(
              backgroundColor: WildlifeTheme.tigerAmber,
              foregroundColor: Colors.black,
            ),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(ctx);
              _analyzeCapture();
            },
            child: const Text('Retry'),
          ),
        ],
      ),
    );
  }

  Future<void> _saveOfflineQueueRecord() async {
    final record = ObservationRecord(
      localId: DateTime.now().millisecondsSinceEpoch.toString(),
      capturedAt: DateTime.now().toIso8601String(),
      stationId: _selectedStation,
      localImagePath: _selectedImagePath,
      syncStatus: 'pending_upload',
      notes: 'Captured offline in field. Awaiting server triage sync.',
    );

    await OfflineQueue.saveObservation(record);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('✓ Stored in offline upload queue for future sync'),
          backgroundColor: WildlifeTheme.tigerAmber,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: WildlifeTheme.darkBg,
      appBar: AppBar(
        title: const Row(
          children: [
            Text('🐅 '),
            Text('Field Biometric Scanner'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings_outlined),
            tooltip: 'Server Settings',
            onPressed: () {
              Navigator.pushNamed(context, '/settings');
            },
          ),
        ],
      ),
      body: Stack(
        children: [
          SingleChildScrollView(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Viewfinder / Image Preview Canvas
                Container(
                  height: 280,
                  decoration: BoxDecoration(
                    color: WildlifeTheme.cardSurface,
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(
                      color: _selectedImage != null
                          ? WildlifeTheme.primaryEmerald
                          : WildlifeTheme.cardBorder,
                      width: 2,
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.5),
                        blurRadius: 10,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(18),
                    child: Stack(
                      fit: StackFit.expand,
                      children: [
                        if (_selectedImage != null && _selectedImage!.existsSync())
                          Image.file(
                            _selectedImage!,
                            fit: BoxFit.cover,
                          )
                        else
                          Center(
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(
                                  Icons.camera_alt_rounded,
                                  size: 64,
                                  color: WildlifeTheme.textMuted.withOpacity(0.5),
                                ),
                                const SizedBox(height: 12),
                                const Text(
                                  'Align Animal Flank in Frame',
                                  style: TextStyle(
                                    color: WildlifeTheme.textSecondary,
                                    fontSize: 16,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                const Text(
                                  'Tap Capture or Select Test Sample below',
                                  style: TextStyle(
                                    color: WildlifeTheme.textMuted,
                                    fontSize: 12,
                                  ),
                                ),
                              ],
                            ),
                          ),

                        // Viewfinder Corner Brackets
                        _buildViewfinderReticles(),

                        // Clear Button if Image Selected
                        if (_selectedImage != null)
                          Positioned(
                            top: 12,
                            right: 12,
                            child: CircleAvatar(
                              backgroundColor: Colors.black.withOpacity(0.6),
                              child: IconButton(
                                icon: const Icon(Icons.close, color: Colors.white, size: 20),
                                onPressed: () {
                                  setState(() {
                                    _selectedImage = null;
                                    _selectedImagePath = null;
                                  });
                                },
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                // Capture Action Bar (Camera / Gallery)
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: () => _pickImage(ImageSource.camera),
                        icon: const Icon(Icons.photo_camera_rounded),
                        label: const Text('Live Camera'),
                        style: OutlinedButton.styleFrom(
                          foregroundColor: WildlifeTheme.primaryEmerald,
                          side: const BorderSide(color: WildlifeTheme.primaryEmerald),
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: () => _pickImage(ImageSource.gallery),
                        icon: const Icon(Icons.photo_library_rounded),
                        label: const Text('Photo Gallery'),
                        style: OutlinedButton.styleFrom(
                          foregroundColor: WildlifeTheme.accentCyan,
                          side: const BorderSide(color: WildlifeTheme.accentCyan),
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),

                // Rapid Sample Selectors (Desktop & Field Evaluation)
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: WildlifeTheme.cardSurface,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: WildlifeTheme.cardBorder),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Row(
                        children: [
                          Icon(Icons.science_outlined, size: 16, color: WildlifeTheme.tigerAmber),
                          SizedBox(width: 6),
                          Text(
                            'Quick Evaluation Presets:',
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                              color: WildlifeTheme.textSecondary,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      SingleChildScrollView(
                        scrollDirection: Axis.horizontal,
                        child: Row(
                          children: [
                            _buildPresetChip('🐅 Bajirao (T-24)', () => _selectPresetSample('bajirao')),
                            const SizedBox(width: 8),
                            _buildPresetChip('🐅 Patdev (T-15)', () => _selectPresetSample('patdev')),
                            const SizedBox(width: 8),
                            _buildPresetChip('🔍 ATRW Crop', () => _selectPresetSample('atrw_sample')),
                            const SizedBox(width: 8),
                            _buildPresetChip('🍂 Forest Blank', () => _selectPresetSample('blank')),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),

                // Flank Orientation Selector (Step 9A Guard)
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: WildlifeTheme.cardSurface,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: WildlifeTheme.cardBorder),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Flexible(
                            child: Text(
                              'Flank Side (Step 9A Guard)',
                              style: TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.w600,
                                color: WildlifeTheme.textPrimary,
                              ),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          SizedBox(width: 4),
                          Text(
                            'Mandatory Match Check',
                            style: TextStyle(fontSize: 11, color: WildlifeTheme.tigerAmber),
                          ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      Row(
                        children: [
                          _buildFlankRadio('Auto-Detect', 'unknown'),
                          const SizedBox(width: 8),
                          _buildFlankRadio('Left Flank', 'left'),
                          const SizedBox(width: 8),
                          _buildFlankRadio('Right Flank', 'right'),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),

                // Station Provenance Dropdown
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: WildlifeTheme.cardSurface,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: WildlifeTheme.cardBorder),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Camera Trap / Patrol Location Provenance',
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                          color: WildlifeTheme.textPrimary,
                        ),
                      ),
                      const SizedBox(height: 8),
                      DropdownButtonFormField<String>(
                        value: _selectedStation,
                        dropdownColor: WildlifeTheme.cardSurfaceLight,
                        decoration: const InputDecoration(
                          contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                          border: OutlineInputBorder(),
                        ),
                        items: _stations.map((s) {
                          return DropdownMenuItem<String>(
                            value: s['id'],
                            child: Text(
                              s['name']!,
                              style: const TextStyle(fontSize: 13, color: WildlifeTheme.textPrimary),
                            ),
                          );
                        }).toList(),
                        onChanged: (val) {
                          if (val != null) {
                            setState(() => _selectedStation = val);
                          }
                        },
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 24),

                // Primary Analyze Action Button
                ElevatedButton.icon(
                  onPressed: _isAnalyzing ? null : _analyzeCapture,
                  icon: const Icon(Icons.radar_rounded, size: 22),
                  label: const Text(
                    'Analyze Field Capture',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: WildlifeTheme.primaryEmerald,
                    foregroundColor: Colors.black,
                    padding: const EdgeInsets.symmetric(vertical: 18),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                    elevation: 6,
                  ),
                ),
                const SizedBox(height: 32),
              ],
            ),
          ),

          // Loading Modal Overlay
          if (_isAnalyzing)
            Container(
              color: Colors.black.withOpacity(0.85),
              child: Center(
                child: Container(
                  padding: const EdgeInsets.all(28),
                  margin: const EdgeInsets.symmetric(horizontal: 32),
                  decoration: BoxDecoration(
                    color: WildlifeTheme.cardSurface,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: WildlifeTheme.primaryEmerald),
                  ),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const CircularProgressIndicator(
                        valueColor: AlwaysStoppedAnimation(WildlifeTheme.primaryEmerald),
                      ),
                      const SizedBox(height: 20),
                      const Text(
                        'TigerTrace AI Processing',
                        style: TextStyle(
                          color: WildlifeTheme.textPrimary,
                          fontSize: 17,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 10),
                      Text(
                        _analyzingStep,
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          color: WildlifeTheme.textSecondary,
                          fontSize: 13,
                        ),
                      ),
                      const SizedBox(height: 16),
                      TextButton.icon(
                        onPressed: () {
                          setState(() {
                            _isAnalyzing = false;
                          });
                        },
                        icon: const Icon(Icons.close, size: 16, color: WildlifeTheme.textMuted),
                        label: const Text('Cancel Analysis', style: TextStyle(color: WildlifeTheme.textMuted, fontSize: 12)),
                      ),
                    ],
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildViewfinderReticles() {
    return IgnorePointer(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Stack(
          children: [
            // Top Left
            Align(
              alignment: Alignment.topLeft,
              child: Container(
                width: 24,
                height: 24,
                decoration: const BoxDecoration(
                  border: Border(
                    top: BorderSide(color: WildlifeTheme.primaryEmerald, width: 3),
                    left: BorderSide(color: WildlifeTheme.primaryEmerald, width: 3),
                  ),
                ),
              ),
            ),
            // Top Right
            Align(
              alignment: Alignment.topRight,
              child: Container(
                width: 24,
                height: 24,
                decoration: const BoxDecoration(
                  border: Border(
                    top: BorderSide(color: WildlifeTheme.primaryEmerald, width: 3),
                    right: BorderSide(color: WildlifeTheme.primaryEmerald, width: 3),
                  ),
                ),
              ),
            ),
            // Bottom Left
            Align(
              alignment: Alignment.bottomLeft,
              child: Container(
                width: 24,
                height: 24,
                decoration: const BoxDecoration(
                  border: Border(
                    bottom: BorderSide(color: WildlifeTheme.primaryEmerald, width: 3),
                    left: BorderSide(color: WildlifeTheme.primaryEmerald, width: 3),
                  ),
                ),
              ),
            ),
            // Bottom Right
            Align(
              alignment: Alignment.bottomRight,
              child: Container(
                width: 24,
                height: 24,
                decoration: const BoxDecoration(
                  border: Border(
                    bottom: BorderSide(color: WildlifeTheme.primaryEmerald, width: 3),
                    right: BorderSide(color: WildlifeTheme.primaryEmerald, width: 3),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFlankRadio(String label, String value) {
    final isSelected = _flankHint == value;
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => _flankHint = value),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 10),
          decoration: BoxDecoration(
            color: isSelected ? WildlifeTheme.primaryEmerald.withOpacity(0.2) : WildlifeTheme.cardSurfaceLight,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(
              color: isSelected ? WildlifeTheme.primaryEmerald : WildlifeTheme.cardBorder,
            ),
          ),
          alignment: Alignment.center,
          child: Text(
            label,
            style: TextStyle(
              fontSize: 12,
              fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
              color: isSelected ? WildlifeTheme.primaryEmerald : WildlifeTheme.textSecondary,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildPresetChip(String label, VoidCallback onTap) {
    return ActionChip(
      label: Text(label, style: const TextStyle(fontSize: 11, color: WildlifeTheme.textPrimary)),
      backgroundColor: WildlifeTheme.cardSurfaceLight,
      side: const BorderSide(color: WildlifeTheme.cardBorder),
      onPressed: onTap,
    );
  }
}
