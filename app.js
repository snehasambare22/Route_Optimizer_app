import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView, StyleSheet, Alert } from 'react-native';
import MapView, { Marker, Polyline } from 'react-native-maps';
import axios from 'axios';

export default function App() {
  const [stops, setStops] = useState(['']);
  const [routeData, setRouteData] = useState(null);
  const [loading, setLoading] = useState(false);

  // ✅ Replace this with your backend FastAPI/Streamlit API endpoint
  const API_URL = "http://10.10.62.159:8000/optimize_route"; // 👈 change this to your backend IP:port

  const handleAddStop = () => {
    setStops([...stops, '']);
  };

  const handleInputChange = (text, index) => {
    const updated = [...stops];
    updated[index] = text;
    setStops(updated);
  };

  const handleOptimize = async () => {
    try {
      setLoading(true);
      const response = await axios.post(API_URL, { stops });
      setRouteData(response.data);
    } catch (error) {
      Alert.alert('Error', 'Failed to connect to backend. Check your IP and backend is running.');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>🗺️ Dynamic Stop Route Optimizer</Text>

      {/* Input Section */}
      {stops.map((stop, index) => (
        <TextInput
          key={index}
          style={styles.input}
          placeholder={`Stop ${index + 1}`}
          value={stop}
          onChangeText={(text) => handleInputChange(text, index)}
        />
      ))}

      <TouchableOpacity style={styles.addButton} onPress={handleAddStop}>
        <Text style={styles.buttonText}>➕ Add Another Stop</Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.optimizeButton} onPress={handleOptimize}>
        <Text style={styles.buttonText}>{loading ? 'Optimizing...' : '📍 Optimize Route'}</Text>
      </TouchableOpacity>

      {/* Results Section */}
      {routeData && !routeData.error && (
        <View style={styles.resultContainer}>
          <Text style={styles.resultHeader}>Optimized Route:</Text>
          <Text style={styles.resultText}>
            {routeData.optimized_route.join(' → ')}
          </Text>
          <Text style={styles.resultTime}>
            ⏱ Total Travel Time: {routeData.route_cost.toFixed(1)} minutes
          </Text>

          {/* Map */}
          <MapView
            style={styles.map}
            initialRegion={{
              latitude: routeData.locations[routeData.optimized_route[0]][0],
              longitude: routeData.locations[routeData.optimized_route[0]][1],
              latitudeDelta: 0.1,
              longitudeDelta: 0.1,
            }}
          >
            {routeData.optimized_route.map((stop, idx) => (
              <Marker
                key={idx}
                coordinate={{
                  latitude: routeData.locations[stop][0],
                  longitude: routeData.locations[stop][1],
                }}
                title={`${idx + 1}. ${stop}`}
                pinColor={idx === 0 ? 'red' : 'blue'}
              />
            ))}

            <Polyline
              coordinates={routeData.optimized_route.map((stop) => ({
                latitude: routeData.locations[stop][0],
                longitude: routeData.locations[stop][1],
              }))}
              strokeWidth={4}
              strokeColor="blue"
            />
          </MapView>
        </View>
      )}

      {routeData && routeData.error && (
        <Text style={styles.errorText}>{routeData.error}</Text>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#eef2f3',
    padding: 20,
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 15,
  },
  input: {
    borderWidth: 1,
    borderColor: '#aaa',
    borderRadius: 10,
    padding: 10,
    marginVertical: 5,
    backgroundColor: 'white',
  },
  addButton: {
    backgroundColor: '#4da6ff',
    padding: 12,
    borderRadius: 10,
    alignItems: 'center',
    marginVertical: 8,
  },
  optimizeButton: {
    backgroundColor: '#0077cc',
    padding: 12,
    borderRadius: 10,
    alignItems: 'center',
    marginVertical: 5,
  },
  buttonText: {
    color: 'white',
    fontWeight: '700',
  },
  resultContainer: {
    marginTop: 20,
    padding: 10,
    backgroundColor: '#fff',
    borderRadius: 10,
  },
  resultHeader: {
    fontSize: 18,
    fontWeight: '700',
  },
  resultText: {
    fontSize: 16,
    marginVertical: 5,
  },
  resultTime: {
    fontSize: 15,
    color: '#555',
    marginBottom: 10,
  },
  map: {
    height: 300,
    borderRadius: 10,
  },
  errorText: {
    color: 'red',
    textAlign: 'center',
    marginTop: 10,
  },
});
