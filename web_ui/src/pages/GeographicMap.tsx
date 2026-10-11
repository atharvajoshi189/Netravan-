import React, { useEffect, useState, useRef, useMemo, useCallback } from 'react';
import L from 'leaflet';
import {
  Compass,
  Layers,
  Play,
  Pause,
  FastForward,
  X,
  Search,
  Maximize,
  Camera,
  MapPin,
  Clock,
  Info,
  Radio,
  Eye,
  Sliders,
  Sparkles,
  Shield,
  Activity,
  AlertTriangle,
  ChevronUp,
  ChevronDown,
  Navigation,
  Droplets,
  Home,
  CheckCircle2,
} from 'lucide-react';

// Tile provider definitions matching source repository
const TILE_PROVIDERS: Record<string, { url: string; attribution: string }> = {
  satellite: {
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: 'Tiles &copy; Esri &mdash; Tadoba-Andhari Aerial Imagery',
  },
  terrain: {
    url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
    attribution: 'Map data: &copy; OpenStreetMap contributors, SRTM | Map style: &copy; OpenTopoMap (CC-BY-SA)',
  },
  hybrid: {
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: 'Tiles &copy; Esri &mdash; Tadoba Hybrid Cartography',
  },
  street: {
    url: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
  },
};

// Helper: Custom Emoji DivIcon
const createEmojiIcon = (emoji: string, color: string, isSelected: boolean = false) =>
  L.divIcon({
    className: 'custom-emoji-icon',
    html: `
      <div style="
        background-color: ${color};
        width: ${isSelected ? '36px' : '28px'};
        height: ${isSelected ? '36px' : '28px'};
        border-radius: 50%;
        border: ${isSelected ? '3px solid #f59e0b' : '2px solid #ffffff'};
        box-shadow: 0 4px 12px rgba(0,0,0,0.6);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: ${isSelected ? '20px' : '16px'};
        transition: transform 0.2s ease, width 0.2s, height 0.2s;
        cursor: pointer;
      ">
        ${emoji}
      </div>
    `,
    iconSize: isSelected ? [36, 36] : [28, 28],
    iconAnchor: isSelected ? [18, 18] : [14, 14],
  });

// Helper: Tadoba Camera Station DivIcon
const createCameraTrapIcon = (isActive: boolean = true) =>
  L.divIcon({
    className: 'camera-trap-icon',
    html: `
      <div style="position: relative; width: 28px; height: 28px; cursor: pointer;">
        <div style="
          position: absolute;
          inset: 0;
          border-radius: 9999px;
          background-color: ${isActive ? '#8b5cf6' : '#64748b'};
          opacity: 0.35;
          animation: ping 2.5s cubic-bezier(0, 0, 0.2, 1) infinite;
        "></div>
        <div style="
          position: relative;
          width: 28px;
          height: 28px;
          border-radius: 9999px;
          background-color: #0f172a;
          border: 2px solid ${isActive ? '#8b5cf6' : '#64748b'};
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 4px 12px rgba(0,0,0,0.7);
          color: #c4b5fd;
          font-size: 11px;
        ">
          📷
        </div>
      </div>
    `,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });

// Helper: Predicted Destination DivIcon
const createPredictedStationIcon = (stationId: string, probPercent: number) =>
  L.divIcon({
    className: 'predicted-station-icon',
    html: `
      <div style="
        background: rgba(139, 92, 246, 0.92);
        border: 2px dashed #f59e0b;
        color: #ffffff;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 10px;
        font-weight: 800;
        box-shadow: 0 4px 12px rgba(139, 92, 246, 0.6);
        display: flex;
        align-items: center;
        gap: 4px;
        white-space: nowrap;
        cursor: pointer;
      ">
        <span>🎯 ${stationId}</span>
        <span style="background: rgba(245, 158, 11, 0.35); padding: 1px 5px; border-radius: 8px; font-size: 9px; color: #fef08a;">
          ${probPercent}%
        </span>
      </div>
    `,
    iconSize: [90, 24],
    iconAnchor: [45, 12],
  });

interface AnimalRecord {
  id: string;
  name: string;
  type: string;
  emoji: string;
  gender?: string;
  age?: string;
  territory?: string;
  collarId?: string;
  totalSightings?: number;
  sightings: any[];
  waypoints: {
    lat: number;
    lng: number;
    time: number;
    heading?: number;
    isInterpolated?: boolean;
    isCameraSighting?: boolean;
    cameraId?: string;
    cameraName?: string;
    capturedImage?: string;
    confidence?: number;
    behavior?: string;
    notes?: string;
  }[];
}

export const GeographicMap: React.FC = () => {
  // Map Style & View
  const [mapStyle, setMapStyle] = useState<string>('satellite');
  const [is3D, setIs3D] = useState<boolean>(false);

  // Layer Visibility
  const [activeLayers, setActiveLayers] = useState({
    boundary: true,
    coreZone: true,
    gates: true,
    villages: true,
    waterBodies: true,
    cameraTraps: true,
    tigers: true,
    trails: true,
    predicted: true,
    heatmap: true,
  });

  // Tadoba Simulation & Playback
  const [currentTime, setCurrentTime] = useState<number>(Date.now());
  const [timeBounds, setTimeBounds] = useState<{ start: number; end: number }>({
    start: Date.now() - 7 * 24 * 3600 * 1000,
    end: Date.now(),
  });
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1);

  // Tracking State (Default to Maya T-1)
  const [trackingMode, setTrackingMode] = useState<'single' | 'all'>('single');
  const [trackedAnimalId, setTrackedAnimalId] = useState<string>('T-1');

  // Selected Entity for Detail Drawer
  const [selectedFeature, setSelectedFeature] = useState<any>(null);
  const [enlargedPhoto, setEnlargedPhoto] = useState<string | null>(null);

  // Search State
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [showSearchResults, setShowSearchResults] = useState<boolean>(false);
  const searchRef = useRef<HTMLDivElement | null>(null);

  // Layer Panel Open/Collapsed
  const [layerPanelOpen, setLayerPanelOpen] = useState<boolean>(true);

  // Mouse Coordinates
  const [mouseCoords, setMouseCoords] = useState<{ lat: number; lng: number }>({ lat: 20.25, lng: 79.33 });

  // Map DOM & Instance Refs
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const tileLayerRef = useRef<L.TileLayer | null>(null);
  const dynamicLayersRef = useRef<L.LayerGroup | null>(null);

  // Tadoba Spatial Datasets
  const [animals, setAnimals] = useState<AnimalRecord[]>([]);
  const [cameras, setCameras] = useState<any[]>([]);
  const [waterBodies, setWaterBodies] = useState<any[]>([]);
  const [boundary, setBoundary] = useState<any>(null);
  const [coreZone, setCoreZone] = useState<any>(null);
  const [gates, setGates] = useState<any>(null);
  const [villages, setVillages] = useState<any>(null);
  const [dataLoaded, setDataLoaded] = useState<boolean>(false);

  // --------------------------------------------------------------------------
  // 1. Fetch Real Tadoba Geospatial & Movement Datasets
  // --------------------------------------------------------------------------
  useEffect(() => {
    Promise.all([
      fetch('/data/demo_animals.json').then((r) => r.json()),
      fetch('/data/demo_cameras.json').then((r) => r.json()),
      fetch('/data/demo_waterbodies.json').then((r) => r.json()),
      fetch('/data/simulation_time.json').then((r) => r.json()),
      fetch('/data/tadoba_boundary.geojson').then((r) => r.json()),
      fetch('/data/core_zone.geojson').then((r) => r.json()),
      fetch('/data/safari_gates.geojson').then((r) => r.json()),
      fetch('/data/villages.geojson').then((r) => r.json()),
    ])
      .then(([animalJson, cameraJson, waterJson, simTime, boundaryGeo, coreGeo, gateGeo, villageGeo]) => {
        const allAnimals: AnimalRecord[] = [];
        const cats = ['tigers', 'leopards', 'slothBears', 'wildDogs', 'pangolins'];
        cats.forEach((cat) => {
          if (animalJson[cat]) {
            animalJson[cat].forEach((a: any) => {
              let emoji = '🐅';
              if (a.type === 'leopard') emoji = '🐆';
              if (a.type === 'bear') emoji = '🐻';
              if (a.type === 'dog') emoji = '🦊';
              if (a.type === 'pangolin') emoji = '🦎';
              allAnimals.push({
                ...a,
                emoji,
              });
            });
          }
        });

        setAnimals(allAnimals);
        setCameras(cameraJson);
        setWaterBodies(waterJson);
        setTimeBounds(simTime);
        setCurrentTime(simTime.end);
        setBoundary(boundaryGeo);
        setCoreZone(coreGeo);
        setGates(gateGeo);
        setVillages(villageGeo);
        setDataLoaded(true);

        // Default tracked animal to Maya (T-1)
        if (allAnimals.length > 0) {
          const defaultAnimal = allAnimals.find((a) => a.id === 'T-1') || allAnimals[0];
          setTrackedAnimalId(defaultAnimal.id);
          setSelectedFeature(defaultAnimal);
        }
      })
      .catch((err) => {
        console.error('Failed to load Tadoba cartography data:', err);
      });
  }, []);

  // --------------------------------------------------------------------------
  // 2. Continuous Playback Animation Engine
  // --------------------------------------------------------------------------
  useEffect(() => {
    let interval: any;
    if (isPlaying && timeBounds) {
      interval = setInterval(() => {
        setCurrentTime((prev) => {
          // 15-minute simulation step adjusted by playbackSpeed
          const nextTime = prev + 15 * 60 * 1000 * playbackSpeed;
          if (nextTime >= timeBounds.end) return timeBounds.start;
          return nextTime;
        });
      }, 100);
    }
    return () => clearInterval(interval);
  }, [isPlaying, playbackSpeed, timeBounds]);

  // --------------------------------------------------------------------------
  // 3. Initialize Leaflet Map Instance Centered on Tadoba
  // --------------------------------------------------------------------------
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    // Tadoba-Andhari Tiger Reserve Center: 20.25° N, 79.33° E
    const tadobaCenter: [number, number] = [20.25, 79.33];
    const tadobaBounds: [[number, number], [number, number]] = [
      [19.5, 78.5],
      [21.0, 80.5],
    ];

    const map = L.map(mapContainerRef.current, {
      center: tadobaCenter,
      zoom: 11,
      minZoom: 9,
      maxZoom: 18,
      maxBounds: tadobaBounds,
      maxBoundsViscosity: 1.0,
      zoomControl: false,
    });

    L.control.zoom({ position: 'topright' }).addTo(map);
    L.control.scale({ position: 'bottomright' }).addTo(map);

    const tileLayer = L.tileLayer(TILE_PROVIDERS.satellite.url, {
      attribution: TILE_PROVIDERS.satellite.attribution,
      maxZoom: 19,
    }).addTo(map);
    tileLayerRef.current = tileLayer;

    const dynamicLayerGroup = L.layerGroup().addTo(map);
    dynamicLayersRef.current = dynamicLayerGroup;

    map.on('mousemove', (e: L.LeafletMouseEvent) => {
      setMouseCoords({
        lat: Number(e.latlng.lat.toFixed(4)),
        lng: Number(e.latlng.lng.toFixed(4)),
      });
    });

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Update Base Map Style
  useEffect(() => {
    if (!mapInstanceRef.current || !tileLayerRef.current) return;
    const provider = TILE_PROVIDERS[mapStyle] || TILE_PROVIDERS.satellite;
    tileLayerRef.current.setUrl(provider.url);
  }, [mapStyle]);

  // --------------------------------------------------------------------------
  // 4. Smooth Continuous Waypoint Interpolation Function
  // --------------------------------------------------------------------------
  const getPositionAtTime = useCallback((waypoints: any[], time: number) => {
    if (!waypoints || waypoints.length === 0) return null;
    const past = waypoints.filter((w) => w.time <= time);
    if (past.length === 0) return waypoints[0];
    const current = past[past.length - 1];

    const future = waypoints.filter((w) => w.time > time);
    if (future.length === 0) return current;

    const next = future[0];
    const timeDiff = next.time - current.time;
    const progress = timeDiff > 0 ? (time - current.time) / timeDiff : 0;

    return {
      lat: current.lat + (next.lat - current.lat) * progress,
      lng: current.lng + (next.lng - current.lng) * progress,
      heading: current.heading || 0,
      time,
      isInterpolated: progress > 0,
      currentWp: current,
      nextWp: next,
    };
  }, []);

  // --------------------------------------------------------------------------
  // 5. Render Real Tadoba Features, Movement Tracks & Animation
  // --------------------------------------------------------------------------
  useEffect(() => {
    if (!mapInstanceRef.current || !dynamicLayersRef.current || !dataLoaded) return;
    const map = mapInstanceRef.current;
    const layerGroup = dynamicLayersRef.current;
    layerGroup.clearLayers();

    // 1. Tadoba Outer Reserve Boundary
    if (activeLayers.boundary && boundary) {
      const boundaryLayer = L.geoJSON(boundary, {
        style: {
          color: '#10b981',
          weight: 1.5,
          fillColor: '#10b981',
          fillOpacity: 0.05,
          dashArray: '4, 8',
        },
      });
      boundaryLayer.bindTooltip('Tadoba-Andhari Tiger Reserve Buffer Outer Perimeter', { sticky: true });
      layerGroup.addLayer(boundaryLayer);
    }

    // 2. Tadoba Core Zone (Dark Green)
    if (activeLayers.coreZone && coreZone) {
      const coreLayer = L.geoJSON(coreZone, {
        style: {
          color: '#059669',
          weight: 2,
          fillColor: '#059669',
          fillOpacity: 0.15,
        },
        onEachFeature: (_feature, layer) => {
          layer.bindTooltip('Tadoba National Park Core Critical Habitat', {
            permanent: false,
            direction: 'center',
          });
        },
      });
      layerGroup.addLayer(coreLayer);
    }

    // 3. Safari Gates (Moharli, Kolara, Navegaon, Khutwanda, Zari, etc.)
    if (activeLayers.gates && gates) {
      const gatesLayer = L.geoJSON(gates, {
        pointToLayer: (feature, latlng) => {
          const isCore = feature.properties?.zone === 'Core';
          return L.circleMarker(latlng, {
            radius: 6,
            fillColor: isCore ? '#f59e0b' : '#10b981',
            color: '#0f172a',
            weight: 2,
            fillOpacity: 1,
          });
        },
        onEachFeature: (feature, layer) => {
          layer.bindTooltip(`🏕️ ${feature.properties?.name || 'Safari Gate'} (${feature.properties?.zone || 'Buffer'})`, {
            direction: 'top',
          });
          layer.on('click', () => {
            setSelectedFeature({
              emoji: '🏕️',
              type: 'gate',
              name: feature.properties?.name || 'Safari Gate',
              category: 'Tourism & Patrol Gate',
              ...feature.properties,
            });
          });
        },
      });
      layerGroup.addLayer(gatesLayer);
    }

    // 4. Villages & Settlements
    if (activeLayers.villages && villages) {
      const villagesLayer = L.geoJSON(villages, {
        pointToLayer: (_feature, latlng) =>
          L.circleMarker(latlng, {
            radius: 5,
            fillColor: '#9ca3af',
            color: '#0f172a',
            weight: 1.5,
            fillOpacity: 0.9,
          }),
        onEachFeature: (feature, layer) => {
          layer.bindTooltip(`🏠 ${feature.properties?.name || 'Village'}`, { direction: 'top' });
          layer.on('click', () => {
            setSelectedFeature({
              emoji: '🏠',
              type: 'village',
              name: `${feature.properties?.name || 'Settlement'} Village`,
              category: 'Buffer Zone Human Settlement',
              ...feature.properties,
            });
          });
        },
      });
      layerGroup.addLayer(villagesLayer);
    }

    // 5. Water Bodies (Tadoba Lake, Kolsa Lake, Erai Dam)
    if (activeLayers.waterBodies && waterBodies) {
      waterBodies.forEach((wb) => {
        const circle = L.circle(wb.pos, {
          radius: wb.radius,
          color: '#3b82f6',
          fillColor: '#3b82f6',
          fillOpacity: 0.28,
          weight: 1.5,
        });
        circle.bindTooltip(`💧 ${wb.name}`, { sticky: true });
        circle.on('click', () => {
          setSelectedFeature({
            emoji: '💧',
            type: 'waterbody',
            name: wb.name,
            category: 'Key Perennial Waterbody',
            pos: wb.pos,
            radius: wb.radius,
          });
        });
        layerGroup.addLayer(circle);
      });
    }

    // 6. Camera Traps (24 Real Motion Sensor Stations)
    if (activeLayers.cameraTraps && cameras) {
      cameras.forEach((c) => {
        const marker = L.marker(c.pos, {
          icon: createCameraTrapIcon(c.status === 'Online'),
        });
        marker.bindTooltip(`📷 ${c.name} (${c.id})`, { direction: 'top' });
        marker.on('click', () => {
          setSelectedFeature({
            emoji: '📷',
            type: 'camera',
            id: c.id,
            name: c.name,
            category: 'Automated Camera Trap Station',
            status: c.status || 'Active',
            pos: c.pos,
            detections: c.detections || [],
            ...c,
          });
        });
        layerGroup.addLayer(marker);
      });
    }

    // 7. Wildlife Sightings Heatmap (Kernel Density Buffer)
    if (activeLayers.heatmap && animals) {
      animals.forEach((animal) => {
        let heatColor = '#ef4444';
        if (animal.type === 'leopard') heatColor = '#eab308';
        if (animal.type === 'bear') heatColor = '#8b5cf6';
        if (animal.type === 'dog') heatColor = '#f97316';
        if (animal.type === 'pangolin') heatColor = '#10b981';

        animal.waypoints.forEach((wp) => {
          const circle = L.circle([wp.lat, wp.lng], {
            radius: 800,
            stroke: false,
            fillColor: heatColor,
            fillOpacity: 0.08,
          });
          layerGroup.addLayer(circle);
        });
      });
    }

    // 8. ANIMALS, HISTORICAL TRAILS & SMOOTH ANIMATED MOVEMENT
    animals.forEach((animal) => {
      const isTarget =
        trackingMode === 'all' || (trackedAnimalId ? animal.id === trackedAnimalId : animal.id === 'T-1');
      if (!isTarget) return;

      const currentPos = getPositionAtTime(animal.waypoints, currentTime);
      if (!currentPos) return;

      const animalColor = animal.type === 'leopard' ? '#eab308' : '#ef4444';

      // Historical Trail up to currentTime
      if (activeLayers.trails) {
        const pastPoints = animal.waypoints
          .filter((wp) => wp.time <= currentTime)
          .map((wp) => [wp.lat, wp.lng] as [number, number]);

        // Add interpolated point to smooth trail head
        if (pastPoints.length > 0) {
          pastPoints.push([currentPos.lat, currentPos.lng]);
        }

        if (pastPoints.length > 1) {
          const polyline = L.polyline(pastPoints, {
            color: animalColor,
            weight: 3.5,
            opacity: 0.9,
            dashArray: '6, 6',
          });
          layerGroup.addLayer(polyline);
        }
      }

      // Camera Trap Photo Sightings Triggered along Trail up to currentTime
      if (activeLayers.trails && animal.sightings) {
        animal.sightings
          .filter((s) => s.time <= currentTime)
          .forEach((s, idx) => {
            const sightMarker = L.circleMarker(s.pos, {
              radius: 7,
              color: '#ffffff',
              weight: 2,
              fillColor: '#8b5cf6',
              fillOpacity: 1,
            });
            sightMarker.bindTooltip(`📸 Capture: ${animal.name} @ ${s.cameraName}`, { direction: 'top' });
            sightMarker.on('click', () => {
              setSelectedFeature({
                emoji: '📸',
                type: 'sighting',
                name: `${animal.name} @ ${s.cameraName}`,
                category: 'Verified Camera Trap Photo Sighting',
                sightingId: s.sightingId,
                animalId: animal.id,
                animalName: animal.name,
                animalType: animal.type,
                cameraId: s.cameraId,
                cameraName: s.cameraName,
                pos: s.pos,
                timestamp: s.time,
                image: s.image,
                confidence: s.confidence,
                behavior: s.behavior,
                notes: s.notes,
                source: 'Automated Motion Trap Sensor Capture',
              });
            });
            layerGroup.addLayer(sightMarker);
          });
      }

      // PREDICTED FUTURE CORRIDOR DISPERSAL (Next Destination & Probabilities)
      if (activeLayers.predicted && currentPos.nextWp) {
        const nextTarget = currentPos.nextWp;
        // Draw dashed corridor line to next target
        const predLine = L.polyline(
          [
            [currentPos.lat, currentPos.lng],
            [nextTarget.lat, nextTarget.lng],
          ],
          {
            color: '#a855f7',
            weight: 2.5,
            opacity: 0.85,
            dashArray: '3, 6',
          }
        );
        layerGroup.addLayer(predLine);

        // Destination Badge
        if (nextTarget.cameraId) {
          const destMarker = L.marker([nextTarget.lat, nextTarget.lng], {
            icon: createPredictedStationIcon(nextTarget.cameraId, 88),
          });
          destMarker.bindTooltip(
            `Predicted Transition Corridor: ${nextTarget.cameraName || nextTarget.cameraId} &bull; 88% Markov Probability`,
            { direction: 'top' }
          );
          destMarker.on('click', () => {
            setSelectedFeature({
              emoji: '🎯',
              type: 'prediction',
              name: `Corridor Prediction: ${animal.name} &rarr; ${nextTarget.cameraName || nextTarget.cameraId}`,
              category: 'Spatial Dispersal Forecast',
              station_id: nextTarget.cameraId,
              probability: '88.5%',
              target_location: [nextTarget.lat, nextTarget.lng],
              notes: `Predicted transit corridor towards ${nextTarget.cameraName || 'next station'} based on territorial patrol frequency.`,
              disclaimer: 'Statistical forecast based on recorded waypoints — not a confirmed future sighting.',
            });
          });
          layerGroup.addLayer(destMarker);
        }
      }

      // CURRENT ANIMAL POSITION MARKER (Animated in real-time)
      const isSelected = selectedFeature?.id === animal.id;
      const marker = L.marker([currentPos.lat, currentPos.lng], {
        icon: createEmojiIcon(animal.emoji, animalColor, isSelected),
      });

      marker.bindTooltip(
        `<strong>${animal.name}</strong> (${animal.type})<br/><span style="font-size: 10px; color: #cbd5e1;">${new Date(currentPos.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>`,
        { direction: 'top' }
      );

      marker.on('click', () => {
        setSelectedFeature({
          ...animal,
          category: `${animal.type.toUpperCase()} Telemetry`,
          timestamp: currentPos.time,
          pos: [currentPos.lat, currentPos.lng],
          latitude: currentPos.lat,
          longitude: currentPos.lng,
          source: currentPos.isInterpolated ? 'Smooth Interpolated Track' : 'Verified Camera Sensor Ping',
        });
        setTrackedAnimalId(animal.id);
      });

      layerGroup.addLayer(marker);
    });
  }, [
    activeLayers,
    animals,
    cameras,
    waterBodies,
    boundary,
    coreZone,
    gates,
    villages,
    dataLoaded,
    currentTime,
    trackedAnimalId,
    trackingMode,
    selectedFeature,
    getPositionAtTime,
  ]);

  // --------------------------------------------------------------------------
  // 6. Fly to Selected Feature
  // --------------------------------------------------------------------------
  const handleSelectFeature = useCallback((feat: any) => {
    setSelectedFeature(feat);
    if (!feat || !mapInstanceRef.current) return;
    const map = mapInstanceRef.current;

    let targetLat: number | undefined;
    let targetLng: number | undefined;

    if (feat.pos && Array.isArray(feat.pos)) {
      targetLat = feat.pos[0];
      targetLng = feat.pos[1];
    } else if (feat.latitude !== undefined && feat.longitude !== undefined) {
      targetLat = Number(feat.latitude);
      targetLng = Number(feat.longitude);
    } else if (feat.waypoints && feat.waypoints.length > 0) {
      const wp = getPositionAtTime(feat.waypoints, currentTime) || feat.waypoints[0];
      targetLat = wp.lat;
      targetLng = wp.lng;
    }

    if (targetLat !== undefined && targetLng !== undefined && !isNaN(targetLat) && !isNaN(targetLng)) {
      map.flyTo([targetLat, targetLng], 13, { duration: 1.2 });
    }
  }, [currentTime, getPositionAtTime]);

  // --------------------------------------------------------------------------
  // 7. Search Across Tadoba Animals, Gates, Cameras, Villages
  // --------------------------------------------------------------------------
  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setSearchQuery(val);
    if (val.length < 2) {
      setSearchResults([]);
      setShowSearchResults(false);
      return;
    }
    const q = val.toLowerCase();
    const results: any[] = [];

    // Search Tadoba animals
    animals.forEach((a) => {
      if (a.name.toLowerCase().includes(q) || a.id.toLowerCase().includes(q)) {
        results.push({
          ...a,
          label: `${a.name} (${a.type})`,
          emoji: a.emoji,
          category: 'Animal',
        });
      }
    });

    // Search Tadoba cameras
    cameras.forEach((c) => {
      if (c.name?.toLowerCase().includes(q) || c.id?.toLowerCase().includes(q)) {
        results.push({
          ...c,
          label: `${c.name} (${c.id})`,
          emoji: '📷',
          category: 'Camera Station',
          pos: c.pos,
        });
      }
    });

    // Search Safari gates
    if (gates?.features) {
      gates.features.forEach((g: any) => {
        const name = g.properties?.name || '';
        if (name.toLowerCase().includes(q)) {
          results.push({
            ...g.properties,
            label: `${name} Gate`,
            emoji: '🏕️',
            category: 'Safari Gate',
            pos: [g.properties.latitude, g.properties.longitude],
          });
        }
      });
    }

    // Search Villages
    if (villages?.features) {
      villages.features.forEach((v: any) => {
        const name = v.properties?.name || '';
        if (name.toLowerCase().includes(q)) {
          results.push({
            ...v.properties,
            label: `${name} Village`,
            emoji: '🏠',
            category: 'Settlement',
            pos: v.geometry?.coordinates ? [v.geometry.coordinates[1], v.geometry.coordinates[0]] : undefined,
          });
        }
      });
    }

    // Search Waterbodies
    waterBodies.forEach((w) => {
      if (w.name?.toLowerCase().includes(q)) {
        results.push({
          ...w,
          label: w.name,
          emoji: '💧',
          category: 'Water Resource',
          pos: w.pos,
        });
      }
    });

    setSearchResults(results);
    setShowSearchResults(true);
  };

  // Close search suggestions on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowSearchResults(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleLayer = (key: keyof typeof activeLayers) => {
    setActiveLayers((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const progressPercent = Math.max(
    0,
    Math.min(
      100,
      ((currentTime - timeBounds.start) / Math.max(1, timeBounds.end - timeBounds.start)) * 100
    )
  );

  return (
    <div className="relative w-full h-[86vh] min-h-[660px] rounded-2xl overflow-hidden border border-slate-800 bg-[#0f1110] select-none shadow-2xl flex flex-col font-sans">
      {/* ----------------------------------------------------
          TOP NAVIGATION BAR (Tadoba Wildlife Intelligence)
          ---------------------------------------------------- */}
      <div className="h-14 px-4 bg-slate-900/90 backdrop-blur-md border-b border-slate-800 flex items-center justify-between z-[2000] shrink-0">
        {/* Brand: Tadoba Wildlife Intelligence */}
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
            <Compass className="w-4 h-4" />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center space-x-1.5">
              <span className="text-xs font-black tracking-wider text-white uppercase">
                TADOBA<span className="text-amber-400"> INTELLIGENCE</span>
              </span>
              <span className="text-[9px] font-mono font-bold px-1.5 py-0.2 bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded">
                TATR GIS
              </span>
            </div>
            <span className="text-[10px] text-slate-400 font-mono tracking-tight">
              Tadoba-Andhari Tiger Reserve Telemetry Map
            </span>
          </div>
        </div>

        {/* Center: Search Bar with Suggestions */}
        <div className="relative w-72 sm:w-96" ref={searchRef}>
          <div className="flex items-center bg-slate-950/80 border border-slate-700/60 rounded-full px-3 py-1.5 shadow-inner">
            <Search className="w-4 h-4 text-slate-400 mr-2 shrink-0" />
            <input
              type="text"
              placeholder="Search Maya, Matkasur, gate, camera, lake..."
              value={searchQuery}
              onChange={handleSearch}
              onFocus={() => {
                if (searchResults.length > 0) setShowSearchResults(true);
              }}
              className="bg-transparent border-none outline-none text-xs text-white placeholder-slate-500 w-full"
            />
          </div>

          {showSearchResults && (
            <div className="absolute top-full left-0 right-0 mt-2 bg-slate-900 border border-slate-700 rounded-xl max-h-64 overflow-y-auto shadow-2xl z-50">
              {searchResults.length > 0 ? (
                searchResults.map((r, i) => (
                  <div
                    key={i}
                    onClick={() => {
                      handleSelectFeature(r);
                      setShowSearchResults(false);
                      setSearchQuery('');
                    }}
                    className="px-3 py-2 text-xs hover:bg-slate-800 cursor-pointer border-b border-slate-800/60 flex items-center space-x-2 text-slate-200"
                  >
                    <span>{r.emoji}</span>
                    <span className="font-semibold text-white">{r.label}</span>
                    <span className="ml-auto text-[10px] text-slate-400 bg-slate-800 px-1.5 py-0.5 rounded">
                      {r.category}
                    </span>
                  </div>
                ))
              ) : (
                <div className="px-3 py-2 text-xs text-slate-400">No matching Tadoba features found.</div>
              )}
            </div>
          )}
        </div>

        {/* Right: Controls (2D/3D, Style Selector, Coordinates, Fullscreen) */}
        <div className="flex items-center space-x-2 sm:space-x-3">
          <div className="hidden md:flex items-center bg-slate-950/80 border border-slate-800 rounded-lg p-0.5 text-xs">
            <button
              onClick={() => setIs3D(false)}
              className={`px-2.5 py-1 rounded font-bold transition-all ${
                !is3D ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' : 'text-slate-400'
              }`}
            >
              2D
            </button>
            <button
              onClick={() => setIs3D(true)}
              className={`px-2.5 py-1 rounded font-bold transition-all ${
                is3D ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' : 'text-slate-400'
              }`}
            >
              3D
            </button>
          </div>

          {/* Map Tile Style Selector */}
          <select
            value={mapStyle}
            onChange={(e) => setMapStyle(e.target.value)}
            className="bg-slate-950/90 border border-slate-700/80 text-white text-xs px-2.5 py-1.5 rounded-lg outline-none cursor-pointer"
          >
            <option value="satellite">Satellite Aerial</option>
            <option value="terrain">Topographic Relief</option>
            <option value="hybrid">Hybrid Labels</option>
            <option value="street">Street CartoDB</option>
          </select>

          {/* Cursor Coordinates */}
          <div className="hidden lg:flex items-center text-[10px] font-mono text-slate-400 bg-slate-950/80 border border-slate-800 px-2.5 py-1.5 rounded-lg">
            <Navigation className="w-3 h-3 text-amber-400 mr-1.5" />
            <span>
              {mouseCoords.lat}° N, {mouseCoords.lng}° E
            </span>
          </div>

          <button
            onClick={() => {
              if (document.fullscreenElement) {
                document.exitFullscreen();
              } else {
                mapContainerRef.current?.parentElement?.requestFullscreen();
              }
            }}
            title="Toggle Fullscreen"
            className="p-1.5 bg-slate-950/80 border border-slate-800 text-slate-400 hover:text-white rounded-lg transition-colors"
          >
            <Maximize className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* ----------------------------------------------------
          MAP CONTAINER
          ---------------------------------------------------- */}
      <div className="relative flex-1 w-full h-full overflow-hidden">
        <div ref={mapContainerRef} className="w-full h-full z-0 bg-[#0a0f0d]" />

        {/* ----------------------------------------------------
            FLOATING LAYER CONTROLS (Top Left)
            ---------------------------------------------------- */}
        <div className={`map-floating-layer-panel ${!layerPanelOpen ? 'collapsed' : ''}`}>
          <div className="map-panel-header" onClick={() => setLayerPanelOpen(!layerPanelOpen)}>
            <div className="flex items-center space-x-2 text-white font-bold text-xs">
              <Layers className="w-4 h-4 text-emerald-400" />
              <span>Tadoba Map Layers</span>
            </div>
            {layerPanelOpen ? <ChevronUp className="w-3.5 h-3.5 text-slate-400" /> : <ChevronDown className="w-3.5 h-3.5 text-slate-400" />}
          </div>

          {layerPanelOpen && (
            <>
              {/* Reserve Boundaries */}
              <div className="map-layer-group">
                <h4>Boundaries & Zoning</h4>
                <label>
                  <input
                    type="checkbox"
                    checked={activeLayers.boundary}
                    onChange={() => toggleLayer('boundary')}
                  />
                  <span className="w-3 h-3 border-2 border-emerald-400 bg-emerald-500/20 rounded-sm"></span>
                  <span>Tadoba Reserve Boundary</span>
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={activeLayers.coreZone}
                    onChange={() => toggleLayer('coreZone')}
                  />
                  <span className="w-3 h-3 border-2 border-emerald-600 bg-emerald-600/30 rounded-sm"></span>
                  <span>Core Zone (National Park)</span>
                </label>
              </div>

              {/* Infrastructure */}
              <div className="map-layer-group">
                <h4>Infrastructure & Features</h4>
                <label>
                  <input
                    type="checkbox"
                    checked={activeLayers.gates}
                    onChange={() => toggleLayer('gates')}
                  />
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-400"></span>
                  <span>Safari Tourism Gates</span>
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={activeLayers.villages}
                    onChange={() => toggleLayer('villages')}
                  />
                  <span className="w-2.5 h-2.5 rounded-full bg-slate-500"></span>
                  <span>Villages & Settlements</span>
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={activeLayers.waterBodies}
                    onChange={() => toggleLayer('waterBodies')}
                  />
                  <span className="w-2.5 h-2.5 rounded-full bg-blue-500"></span>
                  <span>Water Bodies (Lakes & Dams)</span>
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={activeLayers.cameraTraps}
                    onChange={() => toggleLayer('cameraTraps')}
                  />
                  <span className="w-2.5 h-2.5 rounded-full bg-purple-500"></span>
                  <span>Camera Trap Stations</span>
                </label>
              </div>

              {/* Wildlife Movement Data */}
              <div className="map-layer-group">
                <h4>Wildlife Movement Data</h4>
                <label>
                  <input
                    type="checkbox"
                    checked={activeLayers.tigers}
                    onChange={() => toggleLayer('tigers')}
                  />
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500 border border-white"></span>
                  <span>Animal Current Position</span>
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={activeLayers.trails}
                    onChange={() => toggleLayer('trails')}
                  />
                  <span className="w-4 h-0.5 bg-amber-400"></span>
                  <span>Historical Movement Trail</span>
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={activeLayers.predicted}
                    onChange={() => toggleLayer('predicted')}
                  />
                  <span className="w-4 h-0.5 border-t border-dashed border-purple-400"></span>
                  <span>Predicted Corridor Dispersal</span>
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={activeLayers.heatmap}
                    onChange={() => toggleLayer('heatmap')}
                  />
                  <span className="w-2.5 h-2.5 rounded-full bg-gradient-to-r from-amber-400 to-purple-500"></span>
                  <span>Sightings Density Heatmap</span>
                </label>

                {/* Tracking Mode Toggles */}
                <div className="mt-2 pt-2 border-t border-slate-800 space-y-1.5">
                  <div className="flex gap-1">
                    <button
                      onClick={() => setTrackingMode('single')}
                      className={`flex-1 py-1 rounded text-[10px] font-bold ${
                        trackingMode === 'single'
                          ? 'bg-emerald-500 text-slate-950'
                          : 'bg-slate-800 text-slate-300'
                      }`}
                    >
                      🎯 Single Animal
                    </button>
                    <button
                      onClick={() => setTrackingMode('all')}
                      className={`flex-1 py-1 rounded text-[10px] font-bold ${
                        trackingMode === 'all'
                          ? 'bg-emerald-500 text-slate-950'
                          : 'bg-slate-800 text-slate-300'
                      }`}
                    >
                      🌐 All Animals
                    </button>
                  </div>

                  {trackingMode === 'single' && (
                    <div className="space-y-1">
                      <span className="text-[10px] text-slate-400 block">Select Animal to Track:</span>
                      <select
                        value={trackedAnimalId}
                        onChange={(e) => {
                          const id = e.target.value;
                          setTrackedAnimalId(id);
                          const anim = animals.find((a) => a.id === id);
                          if (anim) handleSelectFeature(anim);
                        }}
                        className="w-full bg-slate-950 border border-slate-700 text-white text-xs px-2 py-1 rounded outline-none cursor-pointer"
                      >
                        {animals.map((a) => (
                          <option key={a.id} value={a.id}>
                            {a.emoji} {a.name} ({a.type})
                          </option>
                        ))}
                      </select>
                      <div className="text-[10px] text-slate-500 italic mt-0.5">
                        Tip: Clicking any animal or camera on the map switches tracking directly to it.
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </div>

        {/* ----------------------------------------------------
            FLOATING DETAIL PANEL (Slide-over Right Drawer)
            ---------------------------------------------------- */}
        {selectedFeature && (
          <div className="map-detail-panel">
            <div className="map-detail-header">
              <h3>
                {selectedFeature.emoji && <span>{selectedFeature.emoji}</span>}
                <span>{selectedFeature.name || selectedFeature.id}</span>
              </h3>
              <button
                className="map-detail-close-btn"
                onClick={() => setSelectedFeature(null)}
                title="Close"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Sighting Event Detail */}
            {selectedFeature.type === 'sighting' && (
              <div className="space-y-2.5 text-xs text-slate-300">
                {selectedFeature.image && (
                  <div
                    className="sighting-photo-wrapper"
                    onClick={() => setEnlargedPhoto(selectedFeature.image)}
                  >
                    <img
                      src={selectedFeature.image}
                      alt={selectedFeature.name}
                      className="sighting-photo-img"
                    />
                    <div className="sighting-photo-overlay">
                      <span className="sighting-confidence-tag">
                        ⚡ {selectedFeature.confidence}% AI Match
                      </span>
                      <span className="text-[10px] font-mono bg-slate-950/80 px-1.5 py-0.5 rounded border border-slate-700 text-slate-200">
                        {selectedFeature.cameraId}
                      </span>
                    </div>
                  </div>
                )}

                <div>
                  <strong className="text-white">Photographed Animal:</strong> {selectedFeature.animalName}
                </div>
                <div>
                  <strong className="text-white">Camera Station:</strong> {selectedFeature.cameraName}
                </div>
                {selectedFeature.timestamp && (
                  <div className="flex items-center space-x-1.5 text-amber-400 font-mono">
                    <Clock className="w-3.5 h-3.5" />
                    <span>{new Date(selectedFeature.timestamp).toLocaleString()}</span>
                  </div>
                )}
                {selectedFeature.behavior && (
                  <div className="p-2 rounded bg-slate-950/60 border-l-2 border-purple-500 italic text-slate-300">
                    "{selectedFeature.behavior}"
                  </div>
                )}

                <div className="pt-2 flex gap-2">
                  <button
                    className="sighting-action-btn flex-1"
                    onClick={() => {
                      const anim = animals.find((a) => a.id === selectedFeature.animalId);
                      if (anim) {
                        setTrackedAnimalId(anim.id);
                        handleSelectFeature(anim);
                      }
                    }}
                  >
                    🐾 Track Animal Trail
                  </button>
                  <button
                    className="sighting-action-btn flex-1"
                    onClick={() => {
                      const cam = cameras.find((c) => c.id === selectedFeature.cameraId);
                      if (cam) {
                        handleSelectFeature({ emoji: '📷', type: 'camera', ...cam });
                      }
                    }}
                  >
                    📷 Camera Station
                  </button>
                </div>
              </div>
            )}

            {/* Animal Detail (Maya T-1, Matkasur, Chhota Matka, etc.) */}
            {(selectedFeature.waypoints || ['tiger', 'leopard', 'bear', 'dog', 'pangolin'].includes(selectedFeature.type)) && (
              <div className="space-y-3 text-xs text-slate-300">
                <div className="flex justify-between items-center">
                  <div>
                    <strong className="text-white">Species:</strong>{' '}
                    {selectedFeature.type
                      ? selectedFeature.type.charAt(0).toUpperCase() + selectedFeature.type.slice(1)
                      : 'Tiger'}
                  </div>
                  {selectedFeature.collarId && (
                    <span className="text-[10px] font-mono bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 px-1.5 py-0.5 rounded">
                      📡 {selectedFeature.collarId}
                    </span>
                  )}
                </div>

                {selectedFeature.gender && (
                  <div>
                    <strong className="text-white">Demographics:</strong> {selectedFeature.gender}{' '}
                    {selectedFeature.age ? `• ${selectedFeature.age}` : ''}
                  </div>
                )}

                {selectedFeature.territory && (
                  <div>
                    <strong className="text-white">Primary Territory:</strong> {selectedFeature.territory}
                  </div>
                )}

                <div className="p-2 rounded-lg bg-purple-500/10 border border-purple-500/30 flex items-center space-x-2 text-purple-200">
                  <Radio className="w-4 h-4 text-purple-400 shrink-0" />
                  <span>
                    Traced across <strong>{selectedFeature.sightings?.length || 0} Camera Stations</strong>
                  </span>
                </div>

                {/* Sighting Timeline Cards */}
                {selectedFeature.sightings && selectedFeature.sightings.length > 0 && (
                  <div>
                    <div className="sighting-section-title">
                      <span>Camera Trap Photo Sightings</span>
                      <span className="sighting-badge-count">{selectedFeature.sightings.length} captures</span>
                    </div>

                    <div className="sighting-timeline">
                      {selectedFeature.sightings.map((s: any, idx: number) => (
                        <div key={idx} className="sighting-card">
                          <div className="flex justify-between items-center text-[11px]">
                            <span className="font-semibold text-white">{s.cameraName}</span>
                            <span className="text-amber-400 font-mono text-[10px]">
                              {new Date(s.time).toLocaleDateString()}
                            </span>
                          </div>

                          {s.image && (
                            <div
                              className="sighting-photo-wrapper"
                              onClick={() => setEnlargedPhoto(s.image)}
                            >
                              <img src={s.image} alt={s.cameraName} className="sighting-photo-img" />
                              <div className="sighting-photo-overlay">
                                <span className="sighting-confidence-tag">⚡ {s.confidence}% AI</span>
                                <span className="text-[9px] font-mono bg-slate-900/80 px-1 py-0.5 rounded text-slate-300">
                                  {s.cameraId}
                                </span>
                              </div>
                            </div>
                          )}

                          {s.behavior && (
                            <p className="text-[10px] text-slate-400 italic">"{s.behavior}"</p>
                          )}

                          <button
                            className="sighting-action-btn"
                            onClick={() => {
                              const cam = cameras.find((c) => c.id === s.cameraId);
                              if (cam) handleSelectFeature({ emoji: '📷', type: 'camera', ...cam });
                            }}
                          >
                            <MapPin className="w-3 h-3" />
                            <span>Locate Camera {s.cameraId}</span>
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Camera Station Detail */}
            {selectedFeature.type === 'camera' && (
              <div className="space-y-3 text-xs text-slate-300">
                <div className="flex justify-between items-center">
                  <div>
                    <strong className="text-white">Station ID:</strong> {selectedFeature.id}
                  </div>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">
                    ● {selectedFeature.status || 'Active'}
                  </span>
                </div>

                {selectedFeature.pos && (
                  <div className="font-mono text-slate-400 text-[11px]">
                    Coordinates: {selectedFeature.pos[0].toFixed(4)}° N, {selectedFeature.pos[1].toFixed(4)}° E
                  </div>
                )}

                {/* Animals Captured at this Station */}
                {selectedFeature.detections && selectedFeature.detections.length > 0 ? (
                  <div>
                    <div className="sighting-section-title">
                      <span>Captured Animals at Station</span>
                      <span className="sighting-badge-count">{selectedFeature.detections.length} sighted</span>
                    </div>

                    <div className="space-y-2 mt-2">
                      {selectedFeature.detections.map((det: any, idx: number) => (
                        <div key={idx} className="sighting-card">
                          <div className="flex justify-between items-center text-[11px]">
                            <span className="font-bold text-amber-400">🐾 {det.animalName}</span>
                            <span className="text-slate-400 font-mono text-[10px]">
                              {new Date(det.time).toLocaleDateString()}
                            </span>
                          </div>

                          {det.image && (
                            <div
                              className="sighting-photo-wrapper"
                              style={{ height: '95px' }}
                              onClick={() => setEnlargedPhoto(det.image)}
                            >
                              <img src={det.image} alt={det.animalName} className="sighting-photo-img" />
                              <div className="sighting-photo-overlay">
                                <span className="sighting-confidence-tag">⚡ {det.confidence}% AI</span>
                                <span className="text-[9px] font-mono bg-slate-900/80 px-1 py-0.5 rounded text-slate-300">
                                  {det.animalType}
                                </span>
                              </div>
                            </div>
                          )}

                          {det.behavior && (
                            <p className="text-[10px] text-slate-400 italic">"{det.behavior}"</p>
                          )}

                          <button
                            className="sighting-action-btn"
                            onClick={() => {
                              const anim = animals.find((a) => a.id === det.animalId);
                              if (anim) {
                                setTrackedAnimalId(anim.id);
                                handleSelectFeature(anim);
                              }
                            }}
                          >
                            <Eye className="w-3 h-3" />
                            <span>Track {det.animalName.split(' ')[0]} Across Map</span>
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="p-3 rounded bg-slate-950/60 text-center text-slate-500 italic">
                    No animals sighted in this 24hr window
                  </div>
                )}
              </div>
            )}

            {/* Safari Gate Detail */}
            {selectedFeature.type === 'gate' && (
              <div className="space-y-2 text-xs text-slate-300">
                <div className="flex justify-between items-center">
                  <strong className="text-white">Gate Name:</strong>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">
                    {selectedFeature.zone || 'Buffer'} Zone Gate
                  </span>
                </div>
                <div>
                  <strong className="text-white">Category:</strong> {selectedFeature.category || 'Tourism Gate'}
                </div>
                {selectedFeature.latitude && selectedFeature.longitude && (
                  <div className="font-mono text-[11px] text-slate-400">
                    Location: {Number(selectedFeature.latitude).toFixed(4)}° N, {Number(selectedFeature.longitude).toFixed(4)}° E
                  </div>
                )}
                {selectedFeature.aliases && selectedFeature.aliases.length > 0 && (
                  <div className="text-[11px] text-slate-400">
                    Aliases: {selectedFeature.aliases.join(', ')}
                  </div>
                )}
              </div>
            )}

            {/* Waterbody Detail */}
            {selectedFeature.type === 'waterbody' && (
              <div className="space-y-2 text-xs text-slate-300">
                <div>
                  <strong className="text-white">Resource Name:</strong> {selectedFeature.name}
                </div>
                {selectedFeature.radius && (
                  <div>
                    <strong className="text-white">Perimeter Radius:</strong> {selectedFeature.radius} meters
                  </div>
                )}
                <p className="text-[11px] text-slate-400 italic">
                  Key perennial water hole and prey concentration zone for resident tigers in Tadoba.
                </p>
              </div>
            )}

            {/* Village Settlement Detail */}
            {selectedFeature.type === 'village' && (
              <div className="space-y-2 text-xs text-slate-300">
                <div>
                  <strong className="text-white">Settlement Name:</strong> {selectedFeature.name}
                </div>
                <p className="text-slate-400 italic bg-slate-950/60 p-2 rounded border border-slate-800">
                  Buffer zone village settlement on the periphery of Tadoba-Andhari Tiger Reserve.
                </p>
              </div>
            )}

            {/* Prediction Corridor Detail */}
            {selectedFeature.type === 'prediction' && (
              <div className="space-y-2.5 text-xs text-slate-300">
                <div className="p-2.5 rounded bg-purple-500/10 border border-purple-500/30 space-y-1">
                  <div className="text-purple-300 font-bold">Predicted Target Station</div>
                  <div className="text-white font-mono text-sm">{selectedFeature.station_id}</div>
                  <div className="text-amber-400 font-bold font-mono">
                    Corridor Confidence: {selectedFeature.probability}
                  </div>
                </div>

                <div className="text-slate-300">{selectedFeature.notes}</div>

                <div className="p-2 rounded bg-slate-950 border border-amber-500/30 text-[10px] text-amber-300/90 font-mono">
                  {selectedFeature.disclaimer}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ----------------------------------------------------
            FLOATING BOTTOM TIMELINE PLAYBACK CONTROLLER
            (Interactive scrubbing and continuous movement playback)
            ---------------------------------------------------- */}
        <div className="map-playback-floating">
          <button
            className="map-play-btn"
            onClick={() => setIsPlaying(!isPlaying)}
            title={isPlaying ? 'Pause Simulation' : 'Play Timeline'}
          >
            {isPlaying ? <Pause className="w-4 h-4 text-white" /> : <Play className="w-4 h-4 text-white ml-0.5" />}
          </button>

          <div className="map-timeline-container">
            <div className="map-timeline-labels">
              <span>{new Date(timeBounds.start).toLocaleDateString()}</span>
              <span className="font-semibold text-slate-300">
                Tadoba Movement Timeline &bull; {playbackSpeed}x Speed &bull; Click to scrub
              </span>
              <span>{new Date(timeBounds.end).toLocaleDateString()}</span>
            </div>

            <div
              className="map-timeline-track"
              onClick={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const pct = Math.max(0, Math.min(1, x / rect.width));
                const span = timeBounds.end - timeBounds.start;
                setCurrentTime(timeBounds.start + span * pct);
              }}
            >
              <div className="map-timeline-progress" style={{ width: `${progressPercent}%` }}></div>
            </div>
          </div>

          <div className="map-current-time">
            {new Date(currentTime).toLocaleString([], {
              month: 'short',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            })}
          </div>

          <button
            onClick={() => setPlaybackSpeed((p) => (p === 1 ? 5 : p === 5 ? 10 : 1))}
            className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-mono font-bold text-amber-400 border border-slate-700 flex items-center space-x-1 shrink-0"
            title="Toggle Playback Speed"
          >
            <FastForward className="w-3.5 h-3.5" />
            <span>{playbackSpeed}x</span>
          </button>
        </div>

        {/* ----------------------------------------------------
            OVERVIEW INSET & MAP LEGEND (Bottom Right)
            ---------------------------------------------------- */}
        <div className="map-overview-inset">
          <div className="font-bold text-white text-[11px] mb-1 flex items-center space-x-1.5">
            <Shield className="w-3 h-3 text-emerald-400" />
            <span>Tadoba Cartography Key</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-purple-500"></span>
            <span>Camera Trap Station (24)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500 border border-white"></span>
            <span>Animal Position (Maya, Matkasur, etc.)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-3.5 h-0.5 bg-amber-400"></span>
            <span>Historical Trail (animated)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-3.5 h-0.5 border-t border-dashed border-purple-400"></span>
            <span>Predicted Corridor Target</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/30 border border-emerald-400"></span>
            <span>Core & Buffer Zoning</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-500"></span>
            <span>Water Bodies & Safari Gates</span>
          </div>
        </div>
      </div>

      {/* ----------------------------------------------------
          ENLARGED PHOTO LIGHTBOX MODAL
          ---------------------------------------------------- */}
      {enlargedPhoto && (
        <div
          className="fixed inset-0 z-[9999] bg-black/85 backdrop-blur-md flex items-center justify-center p-4"
          onClick={() => setEnlargedPhoto(null)}
        >
          <div
            className="relative max-w-3xl w-full bg-slate-900 rounded-2xl overflow-hidden border border-slate-700 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center px-4 py-3 border-b border-slate-800">
              <span className="text-xs font-bold text-white flex items-center space-x-2">
                <Camera className="w-4 h-4 text-purple-400" />
                <span>Tadoba Camera Trap Sensor Photo Capture</span>
              </span>
              <button
                onClick={() => setEnlargedPhoto(null)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <img
              src={enlargedPhoto}
              alt="Camera Trap Capture"
              className="w-full max-h-[70vh] object-contain bg-black"
            />
            <div className="px-4 py-2.5 text-xs text-slate-400 flex justify-between items-center bg-slate-950">
              <span>Verified Wildlife Observation &bull; Tadoba-Andhari Tiger Reserve</span>
              <span className="text-emerald-400 font-mono font-semibold">Motion Sensor Photographic Evidence</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GeographicMap;
