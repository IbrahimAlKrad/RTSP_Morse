//
//  KafkaConfigView.swift
//  StreamingEx
//
//  Created by Ibrahim Al Krad on 17.11.25.
//

import SwiftUI

enum ConnectionMode: String, CaseIterable {
    case websocket = "WebSocket (Recommended)"
    case restProxy = "REST Proxy"
    case fake = "Fake Stream (Testing)"
}

/// View for configuring Kafka connection settings
struct KafkaConfigView: View {
    @Environment(\.dismiss) var dismiss
    @StateObject private var streamService = StreamService.shared
    @ObservedObject private var wsClient = WebSocketClient.shared
    
    @State private var connectionMode: ConnectionMode = .websocket
    @State private var websocketURL: String = ""
    @State private var restProxyURL: String = ""
    @State private var topic: String = ""
    @State private var consumerGroup: String = ""
    @State private var isConnecting = false
    @State private var connectionError: String?
    @State private var isConnected = false
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Connection Mode")) {
                    Picker("Mode", selection: $connectionMode) {
                        ForEach(ConnectionMode.allCases, id: \.self) { mode in
                            Text(mode.rawValue).tag(mode)
                        }
                    }
                    .pickerStyle(.segmented)
                }
                
                if connectionMode == .websocket {
                    Section(header: Text("WebSocket Bridge")) {
                        TextField("WebSocket URL", text: $websocketURL)
                            .textContentType(.URL)
                            .autocapitalization(.none)
                            .disableAutocorrection(true)
                        
                        VStack(alignment: .leading, spacing: 4) {
                            Text("✅ Recommended: Real-time, no polling!")
                                .font(.caption)
                                .foregroundStyle(.green)
                                .fontWeight(.semibold)
                            
                            Text("• Run websocket_bridge.py on your Mac")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            
                            Text("• Default port: 8765")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            
                            Text("• Example: ws://192.168.188.32:8765")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                    
                    Section(header: Text("Topic Filter (Optional)")) {
                        TextField("Topic (leave empty for all)", text: $topic)
                            .autocapitalization(.none)
                            .disableAutocorrection(true)
                        
                        Text("Bridge listens to: morse_output, text_input, backend_health")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    
                } else if connectionMode == .restProxy {
                    Section(header: Text("Kafka REST Proxy")) {
                        TextField("REST Proxy URL", text: $restProxyURL)
                            .textContentType(.URL)
                            .autocapitalization(.none)
                            .disableAutocorrection(true)
                        
                        VStack(alignment: .leading, spacing: 4) {
                            Text("⚠️ Less reliable - uses polling")
                                .font(.caption)
                                .foregroundStyle(.orange)
                                .fontWeight(.semibold)
                            
                            Text("• REST Proxy usually runs on port 8082")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            
                            Text("• Example: http://192.168.188.32:8082")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                    
                    Section(header: Text("Topic Configuration")) {
                        TextField("Topic Name", text: $topic)
                            .autocapitalization(.none)
                            .disableAutocorrection(true)
                        
                        TextField("Consumer Group", text: $consumerGroup)
                            .autocapitalization(.none)
                            .disableAutocorrection(true)
                    }
                }
                
                Section {
                    if isConnected || wsClient.isConnected {
                        HStack {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundStyle(.green)
                            Text("Connected!")
                        }
                    }
                    
                    Button(action: connect) {
                        HStack {
                            if isConnecting {
                                ProgressView()
                                    .scaleEffect(0.8)
                            }
                            Text(isConnecting ? "Connecting..." : (isConnected ? "Reconnect" : "Connect"))
                        }
                        .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(isConnecting || !canConnect)
                    
                    if let error = connectionError {
                        Text(error)
                            .font(.caption)
                            .foregroundStyle(.red)
                    }
                    
                    if let wsError = wsClient.lastError {
                        Text("WebSocket: \(wsError)")
                            .font(.caption)
                            .foregroundStyle(.red)
                    }
                }
            }
            .navigationTitle("Stream Configuration")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
            .onAppear {
                loadSavedSettings()
            }
        }
    }
    
    private var canConnect: Bool {
        switch connectionMode {
        case .websocket:
            return !websocketURL.isEmpty
        case .restProxy:
            return !restProxyURL.isEmpty && !topic.isEmpty
        case .fake:
            return true
        }
    }
    
    // MARK: - Persistence
    
    private func loadSavedSettings() {
        let defaults = UserDefaults.standard
        websocketURL = defaults.string(forKey: "websocket_url") ?? "ws://192.168.188.32:8765"
        restProxyURL = defaults.string(forKey: "kafka_rest_proxy_url") ?? "http://192.168.188.32:8082"
        topic = defaults.string(forKey: "kafka_topic") ?? "morse_output"
        consumerGroup = defaults.string(forKey: "kafka_consumer_group") ?? "morse-app-consumer"
        
        // Load connection mode
        if let savedMode = defaults.string(forKey: "connection_mode"),
           let mode = ConnectionMode(rawValue: savedMode) {
            connectionMode = mode
        }
        
        print("📥 Loaded saved settings: ws=\(websocketURL), rest=\(restProxyURL)")
    }
    
    private func saveSettings() {
        let defaults = UserDefaults.standard
        defaults.set(websocketURL, forKey: "websocket_url")
        defaults.set(restProxyURL, forKey: "kafka_rest_proxy_url")
        defaults.set(topic, forKey: "kafka_topic")
        defaults.set(consumerGroup, forKey: "kafka_consumer_group")
        defaults.set(connectionMode.rawValue, forKey: "connection_mode")
        print("💾 Saved settings")
    }
    
    private func connect() {
        isConnecting = true
        connectionError = nil
        
        Task {
            do {
                switch connectionMode {
                case .websocket:
                    streamService.useWebSocket(serverURL: websocketURL)
                    try await streamService.connectToWebSocket(topic: topic.isEmpty ? nil : topic)
                    
                case .restProxy:
                    let config = KafkaConfig(
                        restProxyURL: restProxyURL,
                        topic: topic,
                        consumerGroup: consumerGroup,
                        authHeaders: nil,
                        useSSL: restProxyURL.hasPrefix("https")
                    )
                    streamService.useKafka(config: config)
                    try await streamService.connectToKafka()
                    
                case .fake:
                    await streamService.fullyDisconnectFromKafka()
                    streamService.useFakeStream()
                }
                
                await MainActor.run {
                    isConnected = true
                    isConnecting = false
                    saveSettings()
                }
            } catch {
                await MainActor.run {
                    connectionError = error.localizedDescription
                    isConnecting = false
                    isConnected = false
                }
            }
        }
    }
}

#Preview {
    KafkaConfigView()
}
