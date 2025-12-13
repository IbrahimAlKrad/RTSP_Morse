//
//  SimpleKafkaClient.swift
//  StreamingEx
//
//  Simplified Kafka REST client with reliable polling
//

import Foundation

/// Simple and reliable Kafka REST client
class SimpleKafkaClient {
    private let baseURL: URL
    private let consumerGroup: String
    private var consumerInstanceURL: URL?
    private var isPolling = false
    private var pollTask: Task<Void, Never>?
    
    var onMessage: ((String) -> Void)?
    var onError: ((String) -> Void)?
    var onDebug: ((String) -> Void)?
    
    init(restProxyURL: String, consumerGroup: String = "morse-consumer-group") {
        self.baseURL = URL(string: restProxyURL)!
        self.consumerGroup = consumerGroup
    }
    
    // MARK: - Public API
    
    /// Connect and subscribe to a topic
    func connect(topic: String) async throws {
        debug("🔌 Connecting to Kafka REST Proxy...")
        debug("📍 URL: \(baseURL)")
        debug("📌 Topic: \(topic)")
        
        // Step 1: Create consumer
        try await createConsumer()
        
        // Step 2: Subscribe to topic
        try await subscribe(to: topic)
        
        debug("✅ Connected and subscribed!")
    }
    
    /// Start polling for messages
    func startPolling() {
        guard !isPolling else {
            debug("⚠️ Already polling")
            return
        }
        
        isPolling = true
        debug("🔄 Starting message polling...")
        
        pollTask = Task {
            while isPolling && !Task.isCancelled {
                await pollMessages()
                // Small delay between polls
                try? await Task.sleep(nanoseconds: 500_000_000) // 0.5 second
            }
        }
    }
    
    /// Stop polling
    func stopPolling() {
        debug("⏹️ Stopping polling...")
        isPolling = false
        pollTask?.cancel()
        pollTask = nil
    }
    
    /// Disconnect and cleanup
    func disconnect() async {
        stopPolling()
        
        if let instanceURL = consumerInstanceURL {
            debug("🗑️ Deleting consumer instance...")
            var request = URLRequest(url: instanceURL)
            request.httpMethod = "DELETE"
            _ = try? await URLSession.shared.data(for: request)
        }
        
        consumerInstanceURL = nil
        debug("✅ Disconnected")
    }
    
    // MARK: - Private Methods
    
    private func createConsumer() async throws {
        // Use unique consumer name
        let uniqueName = "consumer-\(UUID().uuidString.prefix(8))"
        let url = baseURL.appendingPathComponent("consumers/\(consumerGroup)")
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/vnd.kafka.v2+json", forHTTPHeaderField: "Content-Type")
        request.setValue("application/vnd.kafka.v2+json", forHTTPHeaderField: "Accept")
        
        let body: [String: Any] = [
            "name": uniqueName,
            "format": "binary",
            "auto.offset.reset": "latest",  // Only get NEW messages
            "auto.commit.enable": true
        ]
        
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        
        debug("📤 Creating consumer: \(uniqueName)")
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw SimpleKafkaError.invalidResponse
        }
        
        debug("📥 Response status: \(httpResponse.statusCode)")
        
        if httpResponse.statusCode == 409 {
            // Consumer already exists, try to delete and recreate
            debug("⚠️ Consumer exists, trying to recreate...")
            throw SimpleKafkaError.consumerExists
        }
        
        guard (200...299).contains(httpResponse.statusCode) else {
            let errorText = String(data: data, encoding: .utf8) ?? "Unknown error"
            debug("❌ Error: \(errorText)")
            throw SimpleKafkaError.createFailed(errorText)
        }
        
        // Parse response to get instance URL
        if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
           let instanceId = json["instance_id"] as? String {
            consumerInstanceURL = baseURL.appendingPathComponent("consumers/\(consumerGroup)/instances/\(instanceId)")
            debug("✅ Consumer created: \(instanceId)")
        }
    }
    
    private func subscribe(to topic: String) async throws {
        guard let instanceURL = consumerInstanceURL else {
            throw SimpleKafkaError.notConnected
        }
        
        let url = instanceURL.appendingPathComponent("subscription")
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/vnd.kafka.v2+json", forHTTPHeaderField: "Content-Type")
        
        let body: [String: Any] = ["topics": [topic]]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        
        debug("📤 Subscribing to: \(topic)")
        
        let (_, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              (200...204).contains(httpResponse.statusCode) else {
            throw SimpleKafkaError.subscribeFailed
        }
        
        debug("✅ Subscribed to: \(topic)")
    }
    
    private func pollMessages() async {
        guard let instanceURL = consumerInstanceURL else {
            debug("❌ No consumer instance")
            return
        }
        
        let url = instanceURL.appendingPathComponent("records")
        
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("application/vnd.kafka.binary.v2+json", forHTTPHeaderField: "Accept")
        request.timeoutInterval = 15
        
        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else { return }
            
            if httpResponse.statusCode == 200 && !data.isEmpty {
                // Parse messages
                if let messages = try? JSONSerialization.jsonObject(with: data) as? [[String: Any]] {
                    for message in messages {
                        if let base64Value = message["value"] as? String,
                           let decodedData = Data(base64Encoded: base64Value),
                           let text = String(data: decodedData, encoding: .utf8) {
                            debug("📨 Message: \(text)")
                            await MainActor.run {
                                onMessage?(text)
                            }
                        }
                    }
                }
            }
        } catch {
            // Ignore timeout errors during polling
            if (error as NSError).code != NSURLErrorTimedOut {
                debug("⚠️ Poll error: \(error.localizedDescription)")
            }
        }
    }
    
    private func debug(_ message: String) {
        print(message)
        onDebug?(message)
    }
}

// MARK: - Errors

enum SimpleKafkaError: LocalizedError {
    case invalidResponse
    case consumerExists
    case createFailed(String)
    case notConnected
    case subscribeFailed
    
    var errorDescription: String? {
        switch self {
        case .invalidResponse: return "Invalid response from server"
        case .consumerExists: return "Consumer already exists"
        case .createFailed(let msg): return "Create failed: \(msg)"
        case .notConnected: return "Not connected"
        case .subscribeFailed: return "Subscribe failed"
        }
    }
}

