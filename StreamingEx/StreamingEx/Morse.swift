//
//  Morse.swift
//  StreamingEx
//
//  Created by Ibrahim Al Krad on 17.11.25.
//

import SwiftUI

struct Morse: View {
    
    @State var text_active = true
    @State var morse_active = false
    @State var subscribed: Bool = false
    @State var streamedText: String = ""
    @StateObject private var streamService = StreamService.shared
    @State private var streamTask: Task<Void, Never>? = nil
    @State private var showTestView = false
    @State private var showKafkaConfig = false
    @State private var connectionError: String?
    @State private var debugInfo: String = "Debug: Waiting..."
    @State private var debugLog: String = "Debug Log:\n"
    
    // Simple Kafka client
    @State private var simpleClient: SimpleKafkaClient?
    
    var body: some View {
        VStack {
            Text("").onAppear {
                print("🟨🟨🟨 MORSE VIEW APPEARED 🟨🟨🟨")
                autoConnectIfNeeded()
            }
            HStack(spacing: 64) {
                Button(action: {
                    switchToText()
                }) {
                    Text("Text")
                        .font(.custom("JetBrainsMono-Regular", size: 24))
                }
                .foregroundStyle(text_active ? .primary : .secondary)
                
                Button(action: {
                    switchToMorse()
                }) {
                    Text("Morse")
                        .font(.custom("JetBrainsMono-Regular", size: 24))
                }
                .foregroundStyle(morse_active ? .primary : .secondary)
            }
            .padding([.top, .bottom], 18)
            
            // Configuration and test buttons
            HStack(spacing: 12) {
                Button(action: {
                    showKafkaConfig = true
                }) {
                    Label("Config", systemImage: "gear")
                        .font(.custom("JetBrainsMono-Regular", size: 12))
                }
                .buttonStyle(.bordered)
                
                Button(action: {
                    showTestView = true
                }) {
                    Label("Send", systemImage: "paperplane")
                        .font(.custom("JetBrainsMono-Regular", size: 12))
                }
                .buttonStyle(.bordered)
                
                Button(action: {
                    streamedText = ""
                    debugLog = "Debug Log:\n✨ Messages cleared!"
                }) {
                    Label("Clear", systemImage: "trash")
                        .font(.custom("JetBrainsMono-Regular", size: 12))
                }
                .buttonStyle(.bordered)
                .foregroundStyle(.red)
            }
            .padding(.bottom, 8)
            
            if let error = connectionError {
                Text(error)
                    .font(.caption)
                    .foregroundStyle(.red)
                    .padding(.horizontal)
            }
            
            // Debug Log (visible on screen)
            ScrollView {
                VStack(alignment: .leading, spacing: 8) {
                    Text("📊 DEBUG INFO:")
                        .font(.caption)
                        .fontWeight(.bold)
                    
                    Text(debugLog)
                        .font(.system(size: 10, design: .monospaced))
                        .foregroundStyle(.blue)
                        .frame(maxWidth: .infinity, alignment: .leading)
                    
                    Divider()
                    
                    Text("📱 MESSAGES:")
                        .font(.caption)
                        .fontWeight(.bold)
                    
                    Text(streamedText.isEmpty ? "Waiting for stream data..." : streamedText)
                        .font(.custom("JetBrainsMono-Regular", size: 18))
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
                .padding([.leading, .trailing], 16)
            }
            
            Spacer()
            
            Button(action: {
                if subscribed {
                    stopSimpleKafka()
                } else {
                    startSimpleKafka()
                }
            }) {
                if subscribed {
                    Label("", systemImage: "pause.fill")
                } else {
                    Label("", systemImage: "play.fill")
                }
            }
            .controlSize(.large)
        }
        .onDisappear {
            stopStreaming()
        }
        .sheet(isPresented: $showTestView) {
            StreamTestView()
        }
        .sheet(isPresented: $showKafkaConfig) {
            KafkaConfigView()
        }
    }
    
    // MARK: - Topic Switching
    
    /// Switches to text topic and clears current text
    func switchToText() {
        text_active = true
        morse_active = false
        
        // Clear the displayed text
        streamedText = ""
        debugLog += "\n\n🔄 SWITCHING TO TEXT TAB"
        debugLog += "\n📌 Now filtering: text_input"
        
        // For WebSocket mode, no need to switch - just change the filter
        // Messages from all topics arrive via WebSocket, we filter client-side
        print("Switched to Text topic (text_input)")
    }
    
    /// Switches to morse topic and clears current text
    func switchToMorse() {
        text_active = false
        morse_active = true
        
        // Clear the displayed text
        streamedText = ""
        debugLog += "\n\n🔄 SWITCHING TO MORSE TAB"
        debugLog += "\n📌 Now filtering: morse_output"
        
        // For WebSocket mode, no need to switch - just change the filter
        // Messages from all topics arrive via WebSocket, we filter client-side
        print("Switched to Morse topic (morse_output)")
    }
    
    // MARK: - Streaming logic
    
    /// Starts listening to the stream
    func startStreaming() {
        print("🚀 Morse.swift: startStreaming() called")
        debugLog += "\n🚀 START: startStreaming() called"
        streamTask?.cancel()
        subscribed = true
        connectionError = nil
        
        print("🚀 Morse.swift: Creating stream task...")
        debugLog += "\n🚀 Creating stream task..."
        streamTask = Task {
            print("🚀 Morse.swift: Inside Task, starting stream setup...")
            await MainActor.run {
                debugLog += "\n🚀 Inside Task, setting up stream..."
            }
            // If using Kafka, ensure we're connected to the correct topic
            // (For fake stream, the stream is already set up)
            do {
                // Determine which topic to connect to based on current mode
                let targetTopic = text_active ? "text_input" : "morse_output"
                print("🚀 Morse.swift: Target topic is: \(targetTopic)")
                await MainActor.run {
                    debugLog += "\n📌 Target topic: \(targetTopic)"
                }
                
                // Try to connect if not already connected (for Kafka)
                // This is safe to call even if already connected
                print("🚀 Morse.swift: Attempting to connect to Kafka...")
                await MainActor.run {
                    debugLog += "\n🔌 Connecting to Kafka..."
                }
                try? await streamService.connectToKafka(topic: targetTopic)
                
                print("🚀 Morse.swift: Checking if stream is available...")
                await MainActor.run {
                    debugLog += "\n🔍 Checking stream..."
                }
                guard let stream = streamService.stream else {
                    print("❌ Morse.swift: Stream is NIL!")
                    await MainActor.run {
                        debugLog += "\n❌ ERROR: Stream is NIL!"
                        connectionError = "Stream not available"
                        subscribed = false
                    }
                    return
                }
                
                print("✅ Morse.swift: Stream is available! Starting to consume messages...")
                await MainActor.run {
                    debugLog += "\n✅ Stream available! Listening..."
                }
                for await message in stream {
                    guard !Task.isCancelled else { break }
                    print("📱 Morse.swift: Received message from stream: \(message)")
                    await MainActor.run {
                        print("📱 Morse.swift: Updating UI with message")
                        debugLog += "\n📨 GOT MESSAGE: \(message.prefix(50))"
                        // Append the message to the existing text
                        if streamedText.isEmpty {
                            streamedText = message
                        } else {
                            streamedText += "\n" + message
                        }
                        print("📱 Morse.swift: UI updated. Total text length: \(streamedText.count)")
                        debugLog += "\n✅ UI updated! Msg count: \(streamedText.split(separator: "\n").count)"
                    }
                }
            } catch {
                await MainActor.run {
                    connectionError = "Connection error: \(error.localizedDescription)"
                    subscribed = false
                }
            }
        }
        
        print("Started listening to stream")
    }
    
    /// Stops listening to the stream
    func stopStreaming() {
        streamTask?.cancel()
        streamTask = nil
        subscribed = false
        
        // Fully disconnect from Kafka if connected
        Task {
            await streamService.fullyDisconnectFromKafka()
        }
        
        print("Stopped listening to stream")
    }
    
    // MARK: - Auto-connect
    
    /// Auto-connect based on saved connection mode
    func autoConnectIfNeeded() {
        let defaults = UserDefaults.standard
        let savedMode = defaults.string(forKey: "connection_mode") ?? ""
        
        // Check if WebSocket mode is saved
        if savedMode == ConnectionMode.websocket.rawValue,
           let wsURL = defaults.string(forKey: "websocket_url"),
           !wsURL.isEmpty {
            print("🔌 Auto-setting WebSocket mode...")
            debugLog += "\n🔌 WebSocket mode detected"
            debugLog += "\n📍 URL: \(wsURL)"
            streamService.useWebSocket(serverURL: wsURL)
            debugLog += "\n✅ WebSocket configured! Tap Play to start."
            return
        }
        
        // Fall back to REST Proxy mode
        guard let savedURL = defaults.string(forKey: "kafka_rest_proxy_url"),
              let savedTopic = defaults.string(forKey: "kafka_topic"),
              let savedGroup = defaults.string(forKey: "kafka_consumer_group"),
              !savedURL.isEmpty else {
            print("⚠️ No saved settings, skipping auto-connect")
            debugLog += "\n⚠️ No saved settings - tap Config to setup"
            return
        }
        
        print("🔌 Auto-connecting to saved Kafka settings...")
        debugLog += "\n🔌 REST Proxy mode detected"
        debugLog += "\n📍 URL: \(savedURL)"
        debugLog += "\n📌 Topic: \(savedTopic)"
        
        let config = KafkaConfig(
            restProxyURL: savedURL,
            topic: savedTopic,
            consumerGroup: savedGroup,
            authHeaders: nil,
            useSSL: savedURL.hasPrefix("https")
        )
        
        streamService.useKafka(config: config)
        debugLog += "\n✅ Kafka configured! Tap Play to start."
    }
    
    // MARK: - Simple Client (WebSocket or REST Proxy)
    
    func startSimpleKafka() {
        let defaults = UserDefaults.standard
        let savedMode = defaults.string(forKey: "connection_mode") ?? ""
        let topic = text_active ? "text_input" : "morse_output"
        
        // Check if WebSocket mode
        if savedMode == ConnectionMode.websocket.rawValue,
           let wsURL = defaults.string(forKey: "websocket_url"),
           !wsURL.isEmpty {
            startWebSocket(url: wsURL, topic: topic)
            return
        }
        
        // Fall back to REST Proxy
        guard let savedURL = defaults.string(forKey: "kafka_rest_proxy_url"),
              !savedURL.isEmpty else {
            debugLog += "\n❌ No connection configured! Tap Config."
            return
        }
        
        debugLog += "\n\n🚀 Starting REST Proxy Client..."
        debugLog += "\n📍 URL: \(savedURL)"
        debugLog += "\n📌 Topic: \(topic)"
        
        // Create simple client
        simpleClient = SimpleKafkaClient(restProxyURL: savedURL)
        
        // Setup callbacks
        simpleClient?.onMessage = { message in
            debugLog += "\n📨 GOT: \(message.prefix(50))"
            if streamedText.isEmpty {
                streamedText = message
            } else {
                streamedText += "\n" + message
            }
        }
        
        simpleClient?.onDebug = { msg in
            debugLog += "\n\(msg)"
        }
        
        // Connect and start polling
        Task {
            do {
                try await simpleClient?.connect(topic: topic)
                simpleClient?.startPolling()
                await MainActor.run {
                    subscribed = true
                    debugLog += "\n✅ Polling started!"
                }
            } catch {
                await MainActor.run {
                    debugLog += "\n❌ Error: \(error.localizedDescription)"
                    connectionError = error.localizedDescription
                }
            }
        }
    }
    
    func startWebSocket(url: String, topic: String) {
        debugLog += "\n\n🚀 Starting WebSocket Client..."
        debugLog += "\n📍 URL: \(url)"
        debugLog += "\n📌 Listening to ALL topics (filter by tab)"
        
        let wsClient = WebSocketClient.shared
        
        // Connect and listen - filter dynamically based on active tab
        wsClient.connect(to: url) { [self] receivedTopic, message in
            // Determine which topic we want based on active tab
            let wantedTopic = text_active ? "text_input" : "morse_output"
            
            // Accept message if it matches wanted topic, or if topic is unknown/empty
            let shouldAccept = receivedTopic == wantedTopic || 
                               receivedTopic == "unknown" || 
                               receivedTopic.isEmpty
            
            if shouldAccept {
                DispatchQueue.main.async {
                    self.debugLog += "\n📨 \(message.prefix(30))..."
                    if self.streamedText.isEmpty {
                        self.streamedText = message
                    } else {
                        self.streamedText += "\n" + message
                    }
                }
            }
            // Silently ignore filtered messages
        }
        
        // Wait a moment for connection
        Task {
            try? await Task.sleep(nanoseconds: 500_000_000) // 0.5s
            await MainActor.run {
                if wsClient.isConnected {
                    subscribed = true
                    debugLog += "\n✅ WebSocket connected! Waiting for messages..."
                } else if let error = wsClient.lastError {
                    debugLog += "\n❌ WebSocket error: \(error)"
                    connectionError = error
                } else {
                    debugLog += "\n⏳ Connecting..."
                    subscribed = true // Assume connecting
                }
            }
        }
    }
    
    func stopSimpleKafka() {
        // Stop WebSocket if connected
        WebSocketClient.shared.disconnect()
        
        // Stop REST Proxy client if any
        Task {
            await simpleClient?.disconnect()
            await MainActor.run {
                simpleClient = nil
                subscribed = false
                debugLog += "\n⏹️ Stopped"
            }
        }
    }
}

#Preview {
    Morse()
}
