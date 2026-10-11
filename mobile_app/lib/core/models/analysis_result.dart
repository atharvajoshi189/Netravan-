class CandidateIdentity {
  final String tigerId;
  final String name;
  final double score;
  final double siftScore;
  final double cosineScore;
  final String flank;

  CandidateIdentity({
    required this.tigerId,
    required this.name,
    required this.score,
    required this.siftScore,
    required this.cosineScore,
    required this.flank,
  });

  factory CandidateIdentity.fromJson(Map<String, dynamic> json) {
    return CandidateIdentity(
      tigerId: json['tiger_id'] ?? '',
      name: json['name'] ?? json['tiger_id'] ?? '',
      score: (json['score'] as num?)?.toDouble() ?? 0.0,
      siftScore: (json['sift_score'] as num?)?.toDouble() ?? 0.0,
      cosineScore: (json['cosine_score'] as num?)?.toDouble() ?? 0.0,
      flank: json['flank'] ?? 'unknown',
    );
  }

  Map<String, dynamic> toJson() => {
    'tiger_id': tigerId,
    'name': name,
    'score': score,
    'sift_score': siftScore,
    'cosine_score': cosineScore,
    'flank': flank,
  };
}

class LocationInfo {
  final String stationId;
  final String rangeName;
  final String zone;
  final double latitude;
  final double longitude;

  LocationInfo({
    required this.stationId,
    required this.rangeName,
    required this.zone,
    required this.latitude,
    required this.longitude,
  });

  factory LocationInfo.fromJson(Map<String, dynamic> json) {
    return LocationInfo(
      stationId: json['station_id'] ?? 'PTR_STN_01',
      rangeName: json['range_name'] ?? 'Turia',
      zone: json['zone'] ?? 'core',
      latitude: (json['latitude'] as num?)?.toDouble() ?? 21.675,
      longitude: (json['longitude'] as num?)?.toDouble() ?? 79.245,
    );
  }

  Map<String, dynamic> toJson() => {
    'station_id': stationId,
    'range_name': rangeName,
    'zone': zone,
    'latitude': latitude,
    'longitude': longitude,
  };
}

class BehaviourEstimate {
  final String status;
  final String? currentStation;
  final List<dynamic> predictedNextStations;
  final Map<String, dynamic>? directionalTrend;
  final List<dynamic>? peakLocation;
  final String? evidenceType;
  final String? notes;

  BehaviourEstimate({
    required this.status,
    this.currentStation,
    this.predictedNextStations = const [],
    this.directionalTrend,
    this.peakLocation,
    this.evidenceType,
    this.notes,
  });

  factory BehaviourEstimate.fromJson(Map<String, dynamic> json) {
    return BehaviourEstimate(
      status: json['status'] ?? 'unknown',
      currentStation: json['current_station'],
      predictedNextStations: json['predicted_next_stations'] as List<dynamic>? ?? [],
      directionalTrend: json['directional_trend'] as Map<String, dynamic>?,
      peakLocation: json['peak_location'] as List<dynamic>?,
      evidenceType: json['evidence_type'],
      notes: json['notes'],
    );
  }

  Map<String, dynamic> toJson() => {
    'status': status,
    'current_station': currentStation,
    'predicted_next_stations': predictedNextStations,
    'directional_trend': directionalTrend,
    'peak_location': peakLocation,
    'evidence_type': evidenceType,
    'notes': notes,
  };
}

class AnalysisResult {
  final String status;
  final int? observationId;
  final String imageName;
  final String? imageUrl;
  final String? cropUrl;
  final bool isBlank;
  final String species;
  final double speciesConfidence;
  final String identityStatus;
  final String? assignedIdentity;
  final String? assignedName;
  final double topScore;
  final double siftScore;
  final double cosineScore;
  final String flankSide;
  final List<CandidateIdentity> candidateIdentities;
  final String decisionReason;
  final String reviewStatus;
  final BehaviourEstimate? behaviourEstimate;
  final LocationInfo? location;
  final String timestamp;
  final Map<String, dynamic> modelVersions;
  final String? error;

  AnalysisResult({
    required this.status,
    this.observationId,
    required this.imageName,
    this.imageUrl,
    this.cropUrl,
    required this.isBlank,
    required this.species,
    required this.speciesConfidence,
    required this.identityStatus,
    this.assignedIdentity,
    this.assignedName,
    required this.topScore,
    required this.siftScore,
    required this.cosineScore,
    required this.flankSide,
    required this.candidateIdentities,
    required this.decisionReason,
    required this.reviewStatus,
    this.behaviourEstimate,
    this.location,
    required this.timestamp,
    required this.modelVersions,
    this.error,
  });

  bool get isMatch => identityStatus == 'verified_match';
  bool get isReviewRequired => identityStatus == 'review_required';
  bool get isNewCandidate => identityStatus == 'new_identity_candidate';
  bool get isUnknown => identityStatus == 'unknown';

  factory AnalysisResult.fromJson(Map<String, dynamic> json) {
    return AnalysisResult(
      status: json['status'] ?? 'success',
      observationId: json['observation_id'] as int?,
      imageName: json['image_name'] ?? 'capture.jpg',
      imageUrl: json['image_url'],
      cropUrl: json['crop_url'],
      isBlank: json['is_blank'] ?? false,
      species: json['species'] ?? 'tiger',
      speciesConfidence: (json['species_confidence'] as num?)?.toDouble() ?? 0.0,
      identityStatus: json['identity_status'] ?? 'unknown',
      assignedIdentity: json['assigned_identity'],
      assignedName: json['assigned_name'],
      topScore: (json['top_score'] as num?)?.toDouble() ?? 0.0,
      siftScore: (json['sift_score'] as num?)?.toDouble() ?? 0.0,
      cosineScore: (json['cosine_score'] as num?)?.toDouble() ?? 0.0,
      flankSide: json['flank_side'] ?? 'unknown',
      candidateIdentities: (json['candidate_identities'] as List<dynamic>?)
              ?.map((c) => CandidateIdentity.fromJson(c as Map<String, dynamic>))
              .toList() ??
          [],
      decisionReason: json['decision_reason'] ?? 'processed',
      reviewStatus: json['review_status'] ?? 'pending_review',
      behaviourEstimate: json['behaviour_estimate'] != null
          ? BehaviourEstimate.fromJson(json['behaviour_estimate'])
          : null,
      location: json['location'] != null ? LocationInfo.fromJson(json['location']) : null,
      timestamp: json['timestamp'] ?? DateTime.now().toUtc().toIso8601String(),
      modelVersions: json['model_versions'] as Map<String, dynamic>? ?? {},
      error: json['error'],
    );
  }

  Map<String, dynamic> toJson() => {
    'status': status,
    'observation_id': observationId,
    'image_name': imageName,
    'image_url': imageUrl,
    'crop_url': cropUrl,
    'is_blank': isBlank,
    'species': species,
    'species_confidence': speciesConfidence,
    'identity_status': identityStatus,
    'assigned_identity': assignedIdentity,
    'assigned_name': assignedName,
    'top_score': topScore,
    'sift_score': siftScore,
    'cosine_score': cosineScore,
    'flank_side': flankSide,
    'candidate_identities': candidateIdentities.map((c) => c.toJson()).toList(),
    'decision_reason': decisionReason,
    'review_status': reviewStatus,
    'behaviour_estimate': behaviourEstimate?.toJson(),
    'location': location?.toJson(),
    'timestamp': timestamp,
    'model_versions': modelVersions,
    'error': error,
  };
}
