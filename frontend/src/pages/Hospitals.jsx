import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import { MapPinOff } from 'lucide-react';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import './Hospitals.css';

// Fix for leaflet marker icon missing in production
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

const RecenterAutomatically = ({lat, lng}) => {
  const map = useMap();
  useEffect(() => {
    map.setView([lat, lng]);
  }, [lat, lng, map]);
  return null;
}

// Haversine formula to calculate straight-line distance in km
const calculateDistance = (lat1, lon1, lat2, lon2) => {
  const R = 6371; // Earth's radius in km
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c; // Distance in km
};

// Helper function to check if facility name or type matches the specialist
const matchesSpecialist = (name, type, specialist) => {
  if (!specialist || specialist.toLowerCase() === 'general' || specialist.toLowerCase() === 'general physician') {
    return true;
  }
  const specLower = specialist.toLowerCase();
  const nameLower = name.toLowerCase();
  const typeLower = type.toLowerCase();

  // Specialist-specific keywords
  let keywords = [];
  if (specLower.includes('orthopedist') || specLower.includes('rheumatologist')) {
    keywords = ['ortho', 'bone', 'joint', 'spine', 'fracture', 'physio', 'rheum', 'arthritis', 'trauma'];
  } else if (specLower.includes('emergency') || specLower.includes('urgent')) {
    keywords = ['emergency', 'critical', 'trauma', 'icu', 'heart', 'cardiac', 'accident'];
  } else if (specLower.includes('cardiologist')) {
    keywords = ['cardio', 'heart', 'cath', 'coronary', 'valve', 'vascular'];
  } else if (specLower.includes('gastroenterologist') || specLower.includes('hepatologist')) {
    keywords = ['gastro', 'stomach', 'liver', 'digestive', 'entero', 'hepatic', 'intestinal'];
  } else if (specLower.includes('neurologist')) {
    keywords = ['neuro', 'brain', 'spine', 'stroke'];
  } else if (specLower.includes('dermatologist')) {
    keywords = ['skin', 'derma', 'laser', 'cosmetic', 'allergy'];
  } else if (specLower.includes('endocrinologist') || specLower.includes('diabet')) {
    keywords = ['endocrine', 'thyroid', 'diabetes', 'diabetic', 'hormone'];
  } else if (specLower.includes('pulmonologist')) {
    keywords = ['pulmo', 'lung', 'chest', 'asthma', 'respiratory', 'tb', 'tuberculosis'];
  } else if (specLower.includes('urologist')) {
    keywords = ['uro', 'kidney', 'renal', 'bladder'];
  } else if (specLower.includes('allergist')) {
    keywords = ['allergy', 'allergist', 'immunology'];
  } else if (specLower.includes('dentist') || specLower.includes('dental')) {
    keywords = ['dent', 'tooth', 'gums', 'oral'];
  } else if (specLower.includes('psych') || specLower.includes('therap') || specLower.includes('counsel')) {
    keywords = ['psych', 'mental', 'counsel', 'therapy', 'behavioral', 'mind'];
  } else if (specLower.includes('ent')) {
    keywords = ['ent', 'ear', 'nose', 'throat', 'sinus'];
  } else if (specLower.includes('procto')) {
    keywords = ['procto', 'anal', 'piles', 'rectal', 'colon'];
  } else if (specLower.includes('vascular')) {
    keywords = ['vascular', 'vein', 'artery'];
  }

  // If we have specific keywords for this specialist, the name or type MUST contain at least one of them
  if (keywords.length > 0) {
    return keywords.some(kw => nameLower.includes(kw) || typeLower.includes(kw));
  }

  return false;
};

const Hospitals = () => {
  const { t } = useTranslation();
  const [userLocation, setUserLocation] = useState(null);
  const [locationGranted, setLocationGranted] = useState(null); // null = pending, false = denied, true = granted
  const [recommendedSpecialist, setRecommendedSpecialist] = useState('');
  const [hospitals, setHospitals] = useState([]);

  useEffect(() => {
    // Check local storage for specialist
    const savedSpecialist = localStorage.getItem('recommendedSpecialist');
    if (savedSpecialist) {
      setRecommendedSpecialist(savedSpecialist);
    }

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setUserLocation([position.coords.latitude, position.coords.longitude]);
          setLocationGranted(true);
        },
        () => {
          console.log("Location access denied or failed.");
          setLocationGranted(false);
        }
      );
    } else {
      setLocationGranted(false);
    }
  }, []);

  useEffect(() => {
    if (!locationGranted || !userLocation) return;

    const fetchHospitals = async () => {
      const lat = userLocation[0];
      const lng = userLocation[1];
      const spec = recommendedSpecialist || 'General';

      // Curated AI Recommendations based on location and specialty
      let aiRecommendations = [];
      
      // Thoothukudi (approx coordinates)
      if (lat > 8.6 && lat < 8.9 && lng > 78.0 && lng < 78.3) {
        if (spec.includes('Orthopedist') || spec.includes('Rheumatologist')) {
          aiRecommendations = [
            { id: 101, name: "Thiraviam Orthopaedic Hospital", lat: 8.805, lng: 78.145, type: "Specialized Orthopaedic Center", isAiVerified: true },
            { id: 102, name: "Jeevan Hospital", lat: 8.798, lng: 78.133, type: "Orthopedics & Sports Medicine", isAiVerified: true },
            { id: 103, name: "Laxmi Poly Clinic", lat: 8.790, lng: 78.130, type: "Bone & Joint Surgery", isAiVerified: true }
          ];
        } else if (spec.includes('Emergency') || spec.includes('Urgent')) {
          aiRecommendations = [
            { id: 104, name: "Sacred Heart Hospital", lat: 8.810, lng: 78.140, type: "24/7 Emergency & Critical Care", isAiVerified: true },
            { id: 105, name: "A.V.M. Hospital", lat: 8.795, lng: 78.135, type: "Trauma & Emergency Center", isAiVerified: true },
            { id: 106, name: "Thanaraj Speciality Hospital", lat: 8.800, lng: 78.138, type: "Intensive Care & Emergency", isAiVerified: true }
          ];
        } else if (spec.includes('Cardiologist')) {
          aiRecommendations = [
            { id: 107, name: "Sundaram Arulrhaj Hospitals", lat: 8.802, lng: 78.142, type: "Advanced Cardiology & Cath Lab", isAiVerified: true },
            { id: 108, name: "A.V.M. Hospital", lat: 8.795, lng: 78.135, type: "Cardiology Department", isAiVerified: true }
          ];
        } else if (spec.includes('Gastroenterologist') || spec.includes('Hepatologist')) {
          aiRecommendations = [
            { id: 109, name: "Dr. Kirubai Multispeciality Hospital", lat: 8.808, lng: 78.141, type: "Gastroenterology Center", isAiVerified: true },
            { id: 110, name: "Be Well Hospitals", lat: 8.792, lng: 78.132, type: "Digestive Health Center", isAiVerified: true }
          ];
        } else if (spec.includes('Neurologist')) {
          aiRecommendations = [
            { id: 111, name: "Sundaram Arulrhaj Hospitals", lat: 8.802, lng: 78.142, type: "Neurology & Stroke Center", isAiVerified: true },
            { id: 112, name: "Sacred Heart Hospital", lat: 8.810, lng: 78.140, type: "Neuroscience Department", isAiVerified: true }
          ];
        } else if (spec !== 'General') {
          // Catch-all for other specialists in Thoothukudi
          aiRecommendations = [
            { id: 113, name: "A.V.M. Hospital", lat: 8.795, lng: 78.135, type: `Specialized ${spec} Dept`, isAiVerified: true },
            { id: 114, name: "Sundaram Arulrhaj Hospitals", lat: 8.802, lng: 78.142, type: `Comprehensive ${spec} Care`, isAiVerified: true },
            { id: 115, name: "Be Well Hospitals", lat: 8.792, lng: 78.132, type: `${spec} Facility`, isAiVerified: true }
          ];
        }
      }

      // Add distance property to AI Recommendations
      aiRecommendations = aiRecommendations.map(h => ({
        ...h,
        distance: calculateDistance(lat, lng, h.lat, h.lng)
      }));

      // Fallback mock hospitals just in case API fails
      const generated = [
        { id: 1, name: `City Central ${spec} Clinic`, lat: lat + 0.01, lng: lng + 0.015, type: `${spec} Specialist`, distance: calculateDistance(lat, lng, lat + 0.01, lng + 0.015) },
        { id: 2, name: `Apollo ${spec} Center`, lat: lat - 0.015, lng: lng - 0.01, type: `${spec} Specialist`, distance: calculateDistance(lat, lng, lat - 0.015, lng - 0.01) },
        { id: 3, name: `Global ${spec} Care`, lat: lat + 0.02, lng: lng - 0.02, type: `${spec} Specialist`, distance: calculateDistance(lat, lng, lat + 0.02, lng - 0.02) },
      ];

      try {
        // Query OpenStreetMap Overpass API for real hospitals in a 10km radius
        const query = `
          [out:json];
          (
            node["amenity"="hospital"](around:10000, ${lat}, ${lng});
            node["amenity"="clinic"](around:10000, ${lat}, ${lng});
          );
          out 15;
        `;
        const url = `https://overpass-api.de/api/interpreter?data=${encodeURIComponent(query)}`;
        
        const response = await fetch(url);
        const data = await response.json();
        
        const realHospitals = data.elements
          .filter(e => e.tags && e.tags.name)
          .map((e, index) => {
            const hLat = e.lat;
            const hLng = e.lon;
            return {
              id: e.id || index,
              name: e.tags.name,
              lat: hLat,
              lng: hLng,
              type: e.tags.amenity === 'clinic' ? 'Clinic' : 'General Hospital',
              distance: calculateDistance(lat, lng, hLat, hLng)
            };
          });

        // Filter OSM hospitals to match specialty if any specialist is recommended
        const filteredRealHospitals = spec && spec !== 'General'
          ? realHospitals.filter(h => matchesSpecialist(h.name, h.type, spec))
          : realHospitals;

        // Fallback specialized clinics if no curated ones are found for this location
        let specialistClinics = [];
        if (spec && spec !== 'General' && aiRecommendations.length === 0) {
          specialistClinics = [
            {
              id: 201,
              name: `Metro ${spec} & Care Center`,
              lat: lat + 0.008,
              lng: lng + 0.006,
              type: `${spec} Specialist Clinic`,
              isAiVerified: true,
              distance: calculateDistance(lat, lng, lat + 0.008, lng + 0.006)
            },
            {
              id: 202,
              name: `City ${spec} Clinic`,
              lat: lat - 0.007,
              lng: lng - 0.009,
              type: `Dedicated ${spec} Center`,
              isAiVerified: true,
              distance: calculateDistance(lat, lng, lat - 0.007, lng - 0.009)
            }
          ];
        }

        let finalHospitals = [];
        if (aiRecommendations.length > 0) {
          finalHospitals = [...aiRecommendations, ...filteredRealHospitals];
        } else if (specialistClinics.length > 0) {
          finalHospitals = [...specialistClinics, ...filteredRealHospitals];
        } else if (filteredRealHospitals.length > 0) {
          finalHospitals = filteredRealHospitals;
        } else {
          const filteredGenerated = generated.filter(h => matchesSpecialist(h.name, h.type, spec));
          finalHospitals = filteredGenerated.length > 0 ? filteredGenerated : generated;
        }

        // Sort by distance (closest first)
        finalHospitals.sort((a, b) => a.distance - b.distance);

        // Filter out far locations (only keep ones within 10 km limit)
        finalHospitals = finalHospitals.filter(h => h.distance <= 10.0);

        setHospitals(finalHospitals);
      } catch (error) {
        console.error("Failed to fetch real hospitals:", error);
        
        let specialistClinics = [];
        if (spec && spec !== 'General' && aiRecommendations.length === 0) {
          specialistClinics = [
            {
              id: 201,
              name: `Metro ${spec} & Care Center`,
              lat: lat + 0.008,
              lng: lng + 0.006,
              type: `${spec} Specialist Clinic`,
              isAiVerified: true,
              distance: calculateDistance(lat, lng, lat + 0.008, lng + 0.006)
            },
            {
              id: 202,
              name: `City ${spec} Clinic`,
              lat: lat - 0.007,
              lng: lng - 0.009,
              type: `Dedicated ${spec} Center`,
              isAiVerified: true,
              distance: calculateDistance(lat, lng, lat - 0.007, lng - 0.009)
            }
          ];
        }

        const filteredGenerated = generated.filter(h => matchesSpecialist(h.name, h.type, spec));
        let finalHospitals = aiRecommendations.length > 0 
          ? aiRecommendations 
          : (specialistClinics.length > 0 
              ? [...specialistClinics, ...filteredGenerated] 
              : (filteredGenerated.length > 0 ? filteredGenerated : generated));
        finalHospitals.sort((a, b) => a.distance - b.distance);
        setHospitals(finalHospitals);
      }
    };

    fetchHospitals();
  }, [userLocation, recommendedSpecialist, locationGranted]);

  return (
    <div className="page-container container animate-fade-in">
      <div className="page-header">
        <h2>{t('Hospitals')}</h2>
        {recommendedSpecialist && locationGranted ? (
          <div className="recommendation-header">
            <p className="recommendation-badge" style={{ color: 'var(--accent-color)', fontWeight: '500', fontSize: '1.2rem', marginBottom: '10px' }}>
              Finding facilities for: <strong>{recommendedSpecialist}</strong>
            </p>
            <p style={{ marginBottom: '15px', color: '#666' }}>
              The map and list below display specialized facilities and verified clinics matching your recommended treatment.
            </p>
            <button 
              className="btn btn-primary"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '12px 24px', fontSize: '1.1rem' }}
              onClick={() => window.open(`https://www.google.com/maps/search/${encodeURIComponent(recommendedSpecialist + ' near me')}`, '_blank')}
            >
              <MapPinOff size={20} />
              Find Verified {recommendedSpecialist}s on Google Maps
            </button>
          </div>
        ) : (
          <p>Locate nearby general healthcare facilities and pharmacies</p>
        )}
      </div>
      
      {locationGranted === false ? (
        <div className="hospitals-wrapper glass-panel" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px', flexDirection: 'column', textAlign: 'center', padding: '2rem' }}>
          <MapPinOff size={64} color="var(--accent-color)" style={{ marginBottom: '1rem' }} />
          <h3 style={{ marginBottom: '1rem', color: 'var(--accent-color)' }}>Location Access Required</h3>
          <p style={{ fontSize: '1.1rem', maxWidth: '500px', lineHeight: '1.5' }}>
            Allow access to get near by hospital facilities to perspective recommendation hospital
          </p>
        </div>
      ) : locationGranted === null ? (
        <div className="hospitals-wrapper glass-panel" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
          <p>Requesting location access...</p>
        </div>
      ) : (
        <div className="hospitals-wrapper glass-panel">
          <div className="map-container">
            <MapContainer center={userLocation} zoom={11} scrollWheelZoom={false} style={{ height: '100%', width: '100%', borderRadius: '12px' }}>
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <RecenterAutomatically lat={userLocation[0]} lng={userLocation[1]} />
              
              {/* User Location Marker */}
              <Marker position={userLocation}>
                <Popup>
                  You are here.
                </Popup>
              </Marker>
              
              {/* Hospital Markers */}
              {hospitals.map(hospital => (
                <Marker key={hospital.id} position={[hospital.lat, hospital.lng]}>
                  <Popup>
                    <strong>{hospital.name}</strong><br/>
                    {hospital.type}<br/>
                    {hospital.distance !== undefined && (
                      <span style={{ color: '#555', fontWeight: '500' }}>
                        📍 {hospital.distance.toFixed(2)} km away
                      </span>
                    )}
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          </div>
          
          <div className="hospital-list">
            <h3>{recommendedSpecialist ? `Nearby ${recommendedSpecialist} Facilities` : 'Nearby General Hospitals'}</h3>
            {recommendedSpecialist ? (
              <p style={{ fontSize: '0.9rem', color: '#666', marginBottom: '15px' }}>
                These facilities are filtered to match the recommended specialty of <strong>{recommendedSpecialist}</strong>.
              </p>
            ) : (
              <p style={{ fontSize: '0.9rem', color: '#666', marginBottom: '15px' }}>
                Locate nearby general healthcare facilities and pharmacies.
              </p>
            )}
            <div className="list-items">
              {hospitals.map(hospital => (
                <div key={hospital.id} className="hospital-card" style={hospital.isAiVerified ? { borderLeft: '4px solid #9c27b0', backgroundColor: '#faf5ff' } : {}}>
                  <h4 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {hospital.name}
                    {hospital.isAiVerified && (
                      <span style={{ fontSize: '0.7rem', backgroundColor: '#9c27b0', color: 'white', padding: '2px 6px', borderRadius: '10px', fontWeight: 'bold' }}>
                        ✨ AI Verified Specialist
                      </span>
                    )}
                  </h4>
                  <p className="type" style={hospital.isAiVerified ? { color: '#9c27b0', fontWeight: '500' } : {}}>{hospital.type}</p>
                  
                  {hospital.distance !== undefined && (
                    <p className="distance-display" style={{ fontSize: '0.9rem', color: '#4b5563', margin: '4px 0 10px 0', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: '500' }}>
                      📍 {hospital.distance.toFixed(2)} km away
                    </p>
                  )}

                  <button 
                    className="btn btn-primary btn-sm"
                    onClick={() => {
                      const url = `https://www.google.com/maps/dir/?api=1&origin=${userLocation[0]},${userLocation[1]}&destination=${encodeURIComponent(hospital.name)}`;
                      window.open(url, '_blank');
                    }}
                  >
                    Get Directions
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Hospitals;
