//
//  StreamService.swift
//  StreamingEx
//
//  Created by Ibrahim Al Krad on 17.11.25.
//

import Foundation
import Combine

/// Stream mode: fake (for testing), REST Proxy, or WebSocket
enum StreamMode {
    case fake
    case kafka(KafkaConfig)
    case websocket(String)  // WebSocket URL
}

/// A stream service that can work with fake streams or real Kafka
class StreamService: ObservableObject {
    static let shared = StreamService()
    
    // Published property for stream messages
    @Published var messages: [String] = []
    
    // Current mode (readable from outside, but only settable internally)
    private(set) var mode: StreamMode = .fake
    
    // Fake stream continuation
    private var continuation: AsyncStream<String>.Continuation?
    
    // The async stream that clients can subscribe to
    private(set) var stream: AsyncStream<String>?
    
    // Kafka client (when using real Kafka)
    private var kafkaClient: KafkaRESTClient?
    
    private init() {
        setupFakeStream()
    }
    
    // MARK: - Configuration
    
    /// Configure the service to use fake stream (default)
    func useFakeStream() {
        // Clean up Kafka client when switching to fake mode
        kafkaClient = nil
        mode = .fake
        setupFakeStream()
        print("StreamService: Using fake stream")
    }
    
    /// Configure the service to use real Kafka (REST Proxy)
    func useKafka(config: KafkaConfig) {
        mode = .kafka(config)
        kafkaClient = KafkaRESTClient(config: config)
        print("✅ StreamService: Using Kafka REST Proxy at \(config.restProxyURL)")
        print("✅ StreamService: Kafka client initialized")
    }
    
    /// Configure the service to use WebSocket (recommended!)
    func useWebSocket(serverURL: String) {
        mode = .websocket(serverURL)
        kafkaClient = nil
        print("✅ StreamService: Using WebSocket at \(serverURL)")
    }
    
    /// Connect to WebSocket and create message stream
    func connectToWebSocket(topic: String?) async throws {
        guard case .websocket(let serverURL) = mode else {
            throw StreamError.notConfiguredForKafka
        }
        
        let wsClient = WebSocketClient.shared
        
        // Create stream from WebSocket messages
        // We yield JSON strings so the consumer can parse and filter by topic dynamically
        stream = AsyncStream<String> { continuation in
            wsClient.connect(to: serverURL) { receivedTopic, message in
                // Create a JSON string with topic and message info
                // This allows the consumer to filter by topic dynamically when tabs switch
                let jsonString: String
                if let jsonData = try? JSONSerialization.data(withJSONObject: [
                    "topic": receivedTopic,
                    "message": message,
                    "type": "kafka_message"
                ]),
                   let jsonStr = String(data: jsonData, encoding: .utf8) {
                    jsonString = jsonStr
                } else {
                    // Fallback: just send the message
                    jsonString = message
                }
                
                // Always yield all messages - filtering happens in Morse.swift based on active tab
                continuation.yield(jsonString)
            }
            
            continuation.onTermination = { _ in
                wsClient.disconnect()
            }
        }
        
        print("✅ StreamService: WebSocket connected, listening for topic: \(topic ?? "all")")
    }
    
    // MARK: - Stream Setup
    
    /// Sets up the fake async stream
    private func setupFakeStream() {
        stream = AsyncStream<String> { continuation in
            self.continuation = continuation
        }
    }
    
    /// Sets up connection to real Kafka and creates the stream
    func connectToKafka() async throws {
        try await connectToKafka(topic: nil)
    }
    
    /// Sets up connection to real Kafka and subscribes to a specific topic
    func connectToKafka(topic: String?) async throws {
        print("🔌 StreamService: connectToKafka called with topic: \(topic ?? "nil")")
        guard case .kafka(let config) = mode else {
            print("❌ StreamService: Not in Kafka mode!")
            throw StreamError.notConfiguredForKafka
        }
        
        guard let client = kafkaClient else {
            print("❌ StreamService: Kafka client is nil!")
            throw StreamError.kafkaClientNotInitialized
        }
        
        let targetTopic = topic ?? config.topic
        print("🔌 StreamService: Target topic resolved to: \(targetTopic)")
        
        // Create consumer if not already created, or just subscribe to new topic
        // For simplicity, we'll recreate the consumer each time we switch topics
        // In production, you might want to keep the consumer and just update subscription
        print("🔌 StreamService: Creating consumer...")
        try await client.createConsumer()
        print("🔌 StreamService: Subscribing to topic: \(targetTopic)")
        try await client.subscribe(to: targetTopic)
        
        // Create stream from Kafka messages
        print("🔌 StreamService: Creating message stream...")
        stream = client.consumeMessages()
        
        print("✅ StreamService: Connected to Kafka topic: \(targetTopic)")
    }
    
    /// Switches to a different topic (reconnects if needed)
    func switchTopic(to topic: String) async throws {
        print("🔄 StreamService: switchTopic called for topic: \(topic)")
        guard case .kafka(let config) = mode else {
            print("❌ StreamService: Not in Kafka mode!")
            throw StreamError.notConfiguredForKafka
        }
        
        // Re-initialize client if it's nil
        if kafkaClient == nil {
            print("⚠️ StreamService: Kafka client is nil, re-initializing...")
            kafkaClient = KafkaRESTClient(config: config)
        }
        
        print("🔄 StreamService: Disconnecting from current consumer...")
        // Disconnect current consumer (but keep client alive)
        await disconnectFromKafka()
        
        print("🔄 StreamService: Reconnecting to new topic: \(topic)")
        // Reconnect to new topic
        try await connectToKafka(topic: topic)
        print("✅ StreamService: Successfully switched to topic: \(topic)")
    }
    
    /// Disconnects from Kafka consumer (but keeps client for reconnection)
    func disconnectFromKafka() async {
        if let client = kafkaClient {
            try? await client.deleteConsumer()
        }
        // Don't set kafkaClient to nil - we need it for reconnecting
        print("StreamService: Disconnected from Kafka consumer")
    }
    
    /// Fully disconnects and removes Kafka client (use when switching modes)
    func fullyDisconnectFromKafka() async {
        if let client = kafkaClient {
            try? await client.deleteConsumer()
        }
        kafkaClient = nil
        print("StreamService: Fully disconnected from Kafka")
    }
    
    // MARK: - Message Sending
    
    /// Manually send data to the stream (works for both fake and real Kafka)
    func send(_ message: String) async throws {
        switch mode {
        case .fake:
            continuation?.yield(message)
            messages.append(message)
            print("StreamService: Sent message to fake stream - \(message)")
            
        case .kafka:
            guard let client = kafkaClient else {
                throw StreamError.kafkaClientNotInitialized
            }
            try await client.produce(message: message)
            messages.append(message)
            print("StreamService: Sent message to Kafka - \(message)")
            
        case .websocket:
            // WebSocket mode - send via WebSocket client
            let wsClient = WebSocketClient.shared
            wsClient.send(message)
            messages.append(message)
            print("StreamService: Sent message via WebSocket - \(message)")
        }
    }
    
    /// Reset the stream (useful for testing)
    func reset() {
        continuation?.finish()
        setupFakeStream()
        messages.removeAll()
    }
}

// MARK: - Errors

enum StreamError: LocalizedError {
    case notConfiguredForKafka
    case kafkaClientNotInitialized
    
    var errorDescription: String? {
        switch self {
        case .notConfiguredForKafka:
            return "Stream service is not configured for Kafka. Call useKafka(config:) first."
        case .kafkaClientNotInitialized:
            return "Kafka client is not initialized"
        }
    }
}

