import React, { useState, useEffect, useRef } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TextInput,
  TouchableOpacity,
  ScrollView,
  SafeAreaView,
  StatusBar,
  Alert,
  Vibration,
  Linking,
  Picker,
} from 'react-native';
import axios from 'axios';
import Realm from 'realm';

// MongoDB Realm Configuration
const MONGODB_APP_ID = 'deltapricetracker-y0ipzbf';

// Scrip Schema for local storage
const ScripSchema = {
  name: 'Scrip',
  properties: {
    symbol: 'string',
    triggerPrice: 'string',
    timeframe: 'string',
    interval: 'string',
    monitoring: 'bool',
    alertActive: 'bool',
    lastPrice: 'double?',
  },
  primaryKey: 'symbol',
};

export default function App() {
  const [tabs, setTabs] = useState([
    { id: 1, symbol: 'LITUSD', triggerPrice: '', timeframe: '1H', interval: '3', monitoring: false, alertActive: false, lastPrice: null }
  ]);
  const [activeTab, setActiveTab] = useState(0);
  const [currentPrice, setCurrentPrice] = useState(null);
  const [lastUpdate, setLastUpdate] = useState('--:--:--');
  const [logs, setLogs] = useState([]);
  const [apiCalls, setApiCalls] = useState([]);
  const [nextId, setNextId] = useState(2);

  const monitoringIntervals = useRef({});
  const alertIntervals = useRef({});

  // Timeframe options
  const timeframeOptions = [
    '1m', '3m', '5m', '10m', '15m', '30m', '45m', '90m',
    '1H', '2H', '3H', '4H', '6H', '12H',
    '1D', '7D', '30D', '1W', '2W'
  ];

  // Calculate API usage
  const apiUsage = apiCalls.filter(time => Date.now() - time < 300000).length * 3;
  const apiColor = apiUsage < 5000 ? '#4CAF50' : apiUsage < 8000 ? '#FF9800' : '#F44336';

  // Add log entry
  const addLog = (message) => {
    const time = new Date().toLocaleTimeString();
    setLogs(prev => [{ time, message }, ...prev].slice(0, 50));
  };

  // Fetch price from API
  const fetchPrice = async (symbol) => {
    try {
      setApiCalls(prev => [...prev, Date.now()]);
      const response = await axios.get('https://api.india.delta.exchange/v2/tickers', {
        timeout: 5000
      });

      if (response.data.success) {
        const ticker = response.data.result.find(t => t.symbol === symbol);
        if (ticker && ticker.mark_price) {
          return parseFloat(ticker.mark_price);
        }
      }
      return null;
    } catch (error) {
      addLog(`Error: ${error.message}`);
      return null;
    }
  };

  // Calculate progress percentage
  const calculateProgress = (currentPrice, triggerPrice) => {
    if (!currentPrice || !triggerPrice || triggerPrice <= 0) return 0;
    if (currentPrice >= triggerPrice) {
      const percentage = ((currentPrice - triggerPrice) / triggerPrice) * 100;
      return Math.min(100, 100 - percentage);
    }
    return 100; // Reached trigger
  };

  // Get progress color
  const getProgressColor = (currentPrice, triggerPrice) => {
    if (!currentPrice || !triggerPrice) return '#E0E0E0';
    const percentage = ((currentPrice - triggerPrice) / triggerPrice) * 100;
    if (percentage > 10) return '#4CAF50';
    if (percentage > 5) return '#FF9800';
    return '#F44336';
  };

  // Open Delta Exchange link
  const openDeltaLink = (symbol) => {
    if (!symbol) return;
    
    let baseSymbol = symbol;
    if (symbol.endsWith('USDT')) {
      baseSymbol = symbol.slice(0, -4);
    } else if (symbol.endsWith('USD')) {
      baseSymbol = symbol.slice(0, -3);
    }
    
    const url = `https://www.delta.exchange/app/futures/trade/${baseSymbol}/${symbol}`;
    Linking.openURL(url).catch(err => addLog(`Error opening link: ${err}`));
  };

  // Start monitoring
  const startMonitoring = (tabIndex) => {
    const tab = tabs[tabIndex];
    
    if (!tab.symbol || !tab.triggerPrice) {
      Alert.alert('Error', 'Please enter symbol and trigger price');
      return;
    }

    const triggerPrice = parseFloat(tab.triggerPrice);
    if (isNaN(triggerPrice)) {
      Alert.alert('Error', 'Invalid trigger price');
      return;
    }

    const newTabs = [...tabs];
    newTabs[tabIndex].monitoring = true;
    setTabs(newTabs);

    addLog(`Started monitoring ${tab.symbol} @ $${triggerPrice} [${tab.timeframe}]`);

    const intervalMs = Math.max(1, parseFloat(tab.interval) || 3) * 1000;
    
    const intervalId = setInterval(async () => {
      const price = await fetchPrice(tab.symbol);
      
      if (price !== null && tabIndex === activeTab) {
        setCurrentPrice(price);
        setLastUpdate(new Date().toLocaleTimeString());

        const updatedTabs = [...tabs];
        updatedTabs[tabIndex].lastPrice = price;
        setTabs(updatedTabs);

        if (price <= triggerPrice && !tabs[tabIndex].alertActive) {
          const alertTabs = [...tabs];
          alertTabs[tabIndex].alertActive = true;
          setTabs(alertTabs);
          
          addLog(`🔔 ALERT! ${tab.symbol} price $${price} <= $${triggerPrice}`);
          startAlert(tabIndex);
        }
      }
    }, intervalMs);

    monitoringIntervals.current[tabIndex] = intervalId;
  };

  // Stop monitoring
  const stopMonitoring = (tabIndex) => {
    if (monitoringIntervals.current[tabIndex]) {
      clearInterval(monitoringIntervals.current[tabIndex]);
      delete monitoringIntervals.current[tabIndex];
    }

    const newTabs = [...tabs];
    newTabs[tabIndex].monitoring = false;
    setTabs(newTabs);

    addLog(`Stopped monitoring ${tabs[tabIndex].symbol}`);
  };

  // Start alert
  const startAlert = (tabIndex) => {
    const pattern = [0, 500, 500];
    
    const alertId = setInterval(() => {
      Vibration.vibrate(pattern);
    }, 1000);

    alertIntervals.current[tabIndex] = alertId;
  };

  // Stop alert
  const stopAlert = (tabIndex) => {
    if (alertIntervals.current[tabIndex]) {
      clearInterval(alertIntervals.current[tabIndex]);
      delete alertIntervals.current[tabIndex];
    }

    Vibration.cancel();

    const newTabs = [...tabs];
    newTabs[tabIndex].alertActive = false;
    newTabs[tabIndex].triggerPrice = '';
    setTabs(newTabs);

    addLog('Alert stopped by user');
  };

  // Add new tab
  const addTab = () => {
    setTabs([...tabs, {
      id: nextId,
      symbol: 'BTCUSDT',
      triggerPrice: '',
      timeframe: '1H',
      interval: '3',
      monitoring: false,
      alertActive: false,
      lastPrice: null
    }]);
    setNextId(nextId + 1);
    setActiveTab(tabs.length);
  };

  // Close tab
  const closeTab = (index) => {
    if (tabs.length <= 1) {
      Alert.alert('Info', 'Cannot close the last tab');
      return;
    }

    if (tabs[index].monitoring) {
      stopMonitoring(index);
    }
    if (tabs[index].alertActive) {
      stopAlert(index);
    }

    const newTabs = tabs.filter((_, i) => i !== index);
    setTabs(newTabs);
    
    if (activeTab >= newTabs.length) {
      setActiveTab(newTabs.length - 1);
    }
  };

  // Update tab field
  const updateTab = (index, field, value) => {
    const newTabs = [...tabs];
    newTabs[index][field] = value;
    setTabs(newTabs);
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      Object.values(monitoringIntervals.current).forEach(clearInterval);
      Object.values(alertIntervals.current).forEach(clearInterval);
    };
  }, []);

  const currentTab = tabs[activeTab];
  const progress = calculateProgress(currentPrice, parseFloat(currentTab.triggerPrice));
  const progressColor = getProgressColor(currentPrice, parseFloat(currentTab.triggerPrice));

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" />
      
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>Delta Exchange</Text>
          <Text style={styles.headerSubtitle}>Monitor</Text>
        </View>
        <View style={styles.apiUsage}>
          <Text style={styles.apiLabel}>API Usage</Text>
          <Text style={[styles.apiValue, { color: apiColor }]}>
            {apiUsage} / 10000
          </Text>
        </View>
      </View>

      {/* Tabs */}
      <ScrollView horizontal style={styles.tabBar} showsHorizontalScrollIndicator={false}>
        {tabs.map((tab, index) => (
          <View key={tab.id} style={styles.tabContainer}>
            <TouchableOpacity
              style={[styles.tab, activeTab === index && styles.activeTab]}
              onPress={() => setActiveTab(index)}
            >
              <Text style={[styles.tabText, activeTab === index && styles.activeTabText]}>
                {tab.symbol}
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.closeBtn}
              onPress={() => closeTab(index)}
            >
              <Text style={styles.closeBtnText}>×</Text>
            </TouchableOpacity>
          </View>
        ))}
        <TouchableOpacity style={styles.addTab} onPress={addTab}>
          <Text style={styles.addTabText}>+</Text>
        </TouchableOpacity>
      </ScrollView>

      {/* Content */}
      <ScrollView style={styles.content}>
        {/* Input Card */}
        <View style={styles.card}>
          <Text style={styles.label}>Symbol</Text>
          <View style={styles.symbolRow}>
            <TextInput
              style={styles.input}
              value={currentTab.symbol}
              onChangeText={(text) => updateTab(activeTab, 'symbol', text)}
              placeholder="Enter symbol"
              autoCapitalize="characters"
            />
            <TouchableOpacity 
              style={styles.linkButton}
              onPress={() => openDeltaLink(currentTab.symbol)}
            >
              <Text style={styles.linkButtonText}>🔗 Open</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.row}>
            <View style={styles.col}>
              <Text style={styles.label}>Trigger Price</Text>
              <TextInput
                style={styles.inputSmall}
                value={currentTab.triggerPrice}
                onChangeText={(text) => updateTab(activeTab, 'triggerPrice', text)}
                placeholder="Enter trigger"
                keyboardType="decimal-pad"
              />
            </View>

            <View style={styles.col}>
              <Text style={styles.label}>Timeframe</Text>
              <View style={styles.pickerContainer}>
                <Picker
                  selectedValue={currentTab.timeframe}
                  style={styles.picker}
                  onValueChange={(value) => updateTab(activeTab, 'timeframe', value)}
                >
                  {timeframeOptions.map(tf => (
                    <Picker.Item key={tf} label={tf} value={tf} />
                  ))}
                </Picker>
              </View>
            </View>
          </View>

          <Text style={styles.label}>Update Interval (seconds)</Text>
          <TextInput
            style={styles.inputSmall}
            value={currentTab.interval}
            onChangeText={(text) => updateTab(activeTab, 'interval', text)}
            placeholder="3"
            keyboardType="number-pad"
          />
        </View>

        {/* Price Display Card */}
        <View style={styles.card}>
          <Text style={styles.priceLabel}>Current Price</Text>
          <Text style={styles.price}>
            {currentPrice !== null ? `$${currentPrice.toFixed(8)}` : '--'}
          </Text>
          
          {/* Progress Bar */}
          {currentPrice && currentTab.triggerPrice && (
            <View style={styles.progressContainer}>
              <Text style={styles.progressLabel}>Distance to Trigger</Text>
              <View style={styles.progressBar}>
                <View style={[styles.progressFill, { width: `${progress}%`, backgroundColor: progressColor }]} />
              </View>
              <Text style={styles.progressText}>
                {progress === 100 ? '🔔 TRIGGER REACHED!' : 
                 `${(((currentPrice - parseFloat(currentTab.triggerPrice)) / parseFloat(currentTab.triggerPrice)) * 100).toFixed(1)}% above`}
              </Text>
            </View>
          )}
          
          <View style={styles.statusRow}>
            <Text style={[styles.status, { color: currentTab.monitoring ? '#4CAF50' : '#999' }]}>
              ● {currentTab.alertActive ? 'ALERT!' : currentTab.monitoring ? 'Monitoring' : 'Not monitoring'}
            </Text>
            <Text style={styles.lastUpdate}>Last: {lastUpdate}</Text>
          </View>

          {!currentTab.monitoring ? (
            <TouchableOpacity
              style={[styles.button, styles.startButton]}
              onPress={() => startMonitoring(activeTab)}
            >
              <Text style={styles.buttonText}>Start Monitoring</Text>
            </TouchableOpacity>
          ) : (
            <View style={styles.buttonRow}>
              <TouchableOpacity
                style={[styles.button, styles.stopButton]}
                onPress={() => stopMonitoring(activeTab)}
              >
                <Text style={styles.buttonText}>Stop</Text>
              </TouchableOpacity>
              
              {currentTab.alertActive && (
                <TouchableOpacity
                  style={[styles.button, styles.alertButton]}
                  onPress={() => stopAlert(activeTab)}
                >
                  <Text style={styles.buttonText}>Stop Alert</Text>
                </TouchableOpacity>
              )}
            </View>
          )}
        </View>

        {/* Activity Log */}
        <View style={styles.card}>
          <Text style={styles.logTitle}>Activity Log</Text>
          <View style={styles.logContainer}>
            {logs.map((log, index) => (
              <Text key={index} style={styles.logEntry}>
                <Text style={styles.logTime}>{log.time}</Text> {log.message}
              </Text>
            ))}
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FAFAFA',
  },
  header: {
    backgroundColor: 'white',
    padding: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#212121',
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#666',
  },
  apiUsage: {
    alignItems: 'flex-end',
  },
  apiLabel: {
    fontSize: 10,
    color: '#666',
  },
  apiValue: {
    fontSize: 12,
    fontWeight: 'bold',
  },
  tabBar: {
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
    maxHeight: 50,
  },
  tabContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 5,
  },
  tab: {
    paddingHorizontal: 15,
    paddingVertical: 12,
    borderRadius: 8,
  },
  activeTab: {
    backgroundColor: '#E3F2FD',
  },
  tabText: {
    fontSize: 14,
    color: '#666',
  },
  activeTabText: {
    color: '#2196F3',
    fontWeight: 'bold',
  },
  closeBtn: {
    padding: 5,
  },
  closeBtnText: {
    fontSize: 20,
    color: '#999',
  },
  addTab: {
    paddingHorizontal: 15,
    paddingVertical: 12,
    justifyContent: 'center',
  },
  addTabText: {
    fontSize: 20,
    color: '#4CAF50',
    fontWeight: 'bold',
  },
  content: {
    flex: 1,
    padding: 15,
  },
  card: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 20,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  label: {
    fontSize: 12,
    color: '#666',
    marginBottom: 5,
    marginTop: 10,
  },
  symbolRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  input: {
    flex: 1,
    backgroundColor: '#F5F5F5',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
  },
  inputSmall: {
    backgroundColor: '#F5F5F5',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
  },
  linkButton: {
    backgroundColor: '#2196F3',
    borderRadius: 8,
    paddingHorizontal: 15,
    paddingVertical: 12,
  },
  linkButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: 'bold',
  },
  row: {
    flexDirection: 'row',
    gap: 15,
  },
  col: {
    flex: 1,
  },
  pickerContainer: {
    backgroundColor: '#F5F5F5',
    borderRadius: 8,
    overflow: 'hidden',
  },
  picker: {
    height: 45,
  },
  priceLabel: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginBottom: 10,
  },
  price: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#212121',
    textAlign: 'center',
    marginBottom: 15,
  },
  progressContainer: {
    marginBottom: 15,
  },
  progressLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 5,
    textAlign: 'center',
  },
  progressBar: {
    height: 20,
    backgroundColor: '#E0E0E0',
    borderRadius: 10,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 10,
  },
  progressText: {
    fontSize: 11,
    color: '#666',
    textAlign: 'center',
    marginTop: 5,
    fontWeight: 'bold',
  },
  statusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  status: {
    fontSize: 12,
  },
  lastUpdate: {
    fontSize: 10,
    color: '#999',
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 10,
  },
  button: {
    flex: 1,
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
  },
  startButton: {
    backgroundColor: '#4CAF50',
  },
  stopButton: {
    backgroundColor: '#999',
  },
  alertButton: {
    backgroundColor: '#F44336',
  },
  buttonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: 'bold',
  },
  logTitle: {
    fontSize: 14,
    color: '#666',
    marginBottom: 10,
  },
  logContainer: {
    maxHeight: 200,
  },
  logEntry: {
    fontSize: 12,
    color: '#333',
    marginBottom: 5,
    fontFamily: 'monospace',
  },
  logTime: {
    color: '#999',
  },
});
