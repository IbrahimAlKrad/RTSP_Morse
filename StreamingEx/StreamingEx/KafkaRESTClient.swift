//
//  KafkaRESTClient.swift
//  StreamingEx
//
//  Created by Ibrahim Al Krad on 17.11.25.
//

import Foundation

/// Client for connecting to Kafka via REST API (Kafka REST Proxy)
class KafkaRESTClient {
    private let config: KafkaConfig
    private let baseURL: URL
    private var consumerInstance: String?
    private var consumerBaseURL: URL?
    
    init(config: KafkaConfig) {
        self.config = config
        guard let url = URL(string: config.restProxyURL) else {
            fatalError("Invalid Kafka REST Proxy URL: \(config.restProxyURL)")
        }
        self.baseURL = url
    }
    
    // MARK: - Consumer Setup
    
    /// Creates a consumer instance for subscribing to Kafka topics
    func createConsumer() async throws {
        print("🔵 KafkaRESTClient: createConsumer called")
        let url = baseURL.appendingPathComponent("/consumers/\(config.consumerGroup)")
        print("🔵 KafkaRESTClient: URL: \(url)")
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/vnd.kafka.v2+json", forHTTPHeaderField: "Content-Type")
        request.setValue("application/vnd.kafka.v2+json", forHTTPHeaderField: "Accept")
        
        // Consumer configuration - use unique name to avoid conflicts
        let uniqueName = "morse-consumer-\(UUID().uuidString.prefix(8))"
        let consumerConfig: [String: Any] = [
            "name": uniqueName,
            "format": "binary",  // Changed from "json" to "binary" to read plain text
            "auto.offset.reset": "earliest",
            "auto.commit.enable": false
        ]
        
        request.httpBody = try JSONSerialization.data(withJSONObject: consumerConfig)
        
        // Add auth headers if provided
        if let authHeaders = config.authHeaders {
            for (key, value) in authHeaders {
                request.setValue(value, forHTTPHeaderField: key)
            }
        }
        
        let (data, response): (Data, URLResponse)
        do {
            (data, response) = try await URLSession.shared.data(for: request)
        } catch {
            // Check if it's a connection error and provide helpful message
            if let urlError = error as? URLError {
                if urlError.code == .cannotConnectToHost || urlError.code == .networkConnectionLost {
                    throw KafkaError.connectionFailed("Cannot connect to Kafka REST Proxy. Make sure:\n1. Kafka REST Proxy is running (usually on port 8082, not 9092)\n2. The URL is correct: \(config.restProxyURL)\n3. Port 9092 is the Kafka broker port, not REST Proxy")
                }
            }
            throw KafkaError.connectionFailed(error.localizedDescription)
        }
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw KafkaError.invalidResponse
        }
        
        guard (200...299).contains(httpResponse.statusCode) else {
            if httpResponse.statusCode == 404 {
                throw KafkaError.connectionFailed("REST Proxy endpoint not found. Make sure Kafka REST Proxy is running and accessible at \(config.restProxyURL)")
            } else if httpResponse.statusCode == 409 {
                throw KafkaError.connectionFailed("Consumer already exists. Please restart the app or use a different consumer group.")
            }
            let errorMessage = String(data: data, encoding: .utf8) ?? "Unknown error"
            throw KafkaError.connectionFailed("Failed to create consumer (HTTP \(httpResponse.statusCode)): \(errorMessage)")
        }
        
        if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
           let instanceId = json["instance_id"] as? String {
            self.consumerInstance = instanceId
            self.consumerBaseURL = baseURL.appendingPathComponent("/consumers/\(config.consumerGroup)/instances/\(instanceId)")
            print("KafkaRESTClient: Created consumer instance: \(instanceId)")
        } else {
            throw KafkaError.invalidResponse
        }
    }
    
    /// Subscribes the consumer to the configured topic
    func subscribe() async throws {
        try await subscribe(to: config.topic)
    }
    
    /// Subscribes the consumer to a specific topic
    func subscribe(to topic: String) async throws {
        print("🔵 KafkaRESTClient: subscribe called for topic: \(topic)")
        guard let consumerBaseURL = consumerBaseURL else {
            print("❌ KafkaRESTClient: Consumer not created!")
            throw KafkaError.consumerNotCreated
        }
        
        let url = consumerBaseURL.appendingPathComponent("/subscription")
        print("🔵 KafkaRESTClient: Subscription URL: \(url)")
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/vnd.kafka.v2+json", forHTTPHeaderField: "Content-Type")
        
        let subscription: [String: Any] = [
            "topics": [topic]
        ]
        
        request.httpBody = try JSONSerialization.data(withJSONObject: subscription)
        
        if let authHeaders = config.authHeaders {
            for (key, value) in authHeaders {
                request.setValue(value, forHTTPHeaderField: key)
            }
        }
        
        let (_, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              (200...204).contains(httpResponse.statusCode) else {
            throw KafkaError.subscriptionFailed
        }
        
        print("KafkaRESTClient: Subscribed to topic: \(topic)")
    }
    
    // MARK: - Message Consumption
    
    /// Creates an AsyncStream that yields messages from Kafka
    func consumeMessages() -> AsyncStream<String> {
        return AsyncStream { continuation in
            Task {
                print("🔄 KafkaRESTClient: Starting message consumption loop...")
                while !Task.isCancelled {
                    do {
                        guard let consumerBaseURL = consumerBaseURL else {
                            throw KafkaError.consumerNotCreated
                        }
                        
                        let url = consumerBaseURL.appendingPathComponent("/records")
                        
                        var request = URLRequest(url: url)
                        request.httpMethod = "GET"
                        request.setValue("application/vnd.kafka.binary.v2+json", forHTTPHeaderField: "Accept")
                        request.timeoutInterval = 10 // Balanced polling (10 seconds)
                        
                        if let authHeaders = config.authHeaders {
                            for (key, value) in authHeaders {
                                request.setValue(value, forHTTPHeaderField: key)
                            }
                        }
                        
                        let (data, response) = try await URLSession.shared.data(for: request)
                        
                        guard let httpResponse = response as? HTTPURLResponse else {
                            continue
                        }
                        
                        if httpResponse.statusCode == 200, !data.isEmpty {
                            print("🟢 KafkaRESTClient: Received data from Kafka")
                            // Parse Kafka messages (binary format returns base64 encoded values)
                            if let messages = try? JSONSerialization.jsonObject(with: data) as? [[String: Any]] {
                                print("🟢 KafkaRESTClient: Parsed \(messages.count) message(s)")
                                for (index, message) in messages.enumerated() {
                                    print("🟢 KafkaRESTClient: Message \(index): \(message)")
                                    if let base64Value = message["value"] as? String {
                                        print("🟢 KafkaRESTClient: Base64 value: \(base64Value)")
                                        if let decodedData = Data(base64Encoded: base64Value),
                                           let text = String(data: decodedData, encoding: .utf8) {
                                            print("✅ KafkaRESTClient: DECODED MESSAGE: \(text)")
                                            continuation.yield(text)
                                        } else {
                                            print("❌ KafkaRESTClient: Failed to decode base64 or convert to string")
                                        }
                                    } else {
                                        print("❌ KafkaRESTClient: No 'value' field in message")
                                    }
                                }
                            } else {
                                print("❌ KafkaRESTClient: Failed to parse JSON response")
                                if let responseString = String(data: data, encoding: .utf8) {
                                    print("❌ KafkaRESTClient: Raw response: \(responseString)")
                                }
                            }
                        } else if httpResponse.statusCode == 204 {
                            // No messages available, continue polling
                            print("⏳ KafkaRESTClient: No messages (204), continuing to poll...")
                            continue
                        } else {
                            print("⚠️ KafkaRESTClient: HTTP \(httpResponse.statusCode), data size: \(data.count)")
                            if let responseText = String(data: data, encoding: .utf8) {
                                print("⚠️ Response: \(responseText)")
                            }
                        }
                        
                        // Small delay to avoid overwhelming the server
                        try? await Task.sleep(nanoseconds: 100_000_000) // 0.1 seconds
                        
                    } catch {
                        print("KafkaRESTClient: Error consuming messages: \(error)")
                        // Continue trying even on error
                        try? await Task.sleep(nanoseconds: 1_000_000_000) // 1 second delay on error
                    }
                }
                continuation.finish()
            }
        }
    }
    
    // MARK: - Producer (for sending messages)
    
    /// Sends a message to Kafka topic
    func produce(message: String) async throws {
        try await produce(message: message, to: config.topic)
    }
    
    /// Sends a message to a specific Kafka topic
    func produce(message: String, to topic: String) async throws {
        let url = baseURL.appendingPathComponent("/topics/\(topic)")
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/vnd.kafka.json.v2+json", forHTTPHeaderField: "Content-Type")
        
        let records: [String: Any] = [
            "records": [
                [
                    "value": [
                        "text": message
                    ]
                ]
            ]
        ]
        
        request.httpBody = try JSONSerialization.data(withJSONObject: records)
        
        if let authHeaders = config.authHeaders {
            for (key, value) in authHeaders {
                request.setValue(value, forHTTPHeaderField: key)
            }
        }
        
        let (_, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw KafkaError.productionFailed
        }
        
        print("KafkaRESTClient: Produced message to topic: \(topic)")
    }
    
    // MARK: - Cleanup
    
    /// Deletes the consumer instance
    func deleteConsumer() async throws {
        guard let consumerBaseURL = consumerBaseURL else {
            return
        }
        
        var request = URLRequest(url: consumerBaseURL)
        request.httpMethod = "DELETE"
        
        if let authHeaders = config.authHeaders {
            for (key, value) in authHeaders {
                request.setValue(value, forHTTPHeaderField: key)
            }
        }
        
        _ = try await URLSession.shared.data(for: request)
        self.consumerInstance = nil
        self.consumerBaseURL = nil
        print("KafkaRESTClient: Deleted consumer instance")
    }
}

// MARK: - Errors

enum KafkaError: LocalizedError {
    case consumerCreationFailed
    case consumerNotCreated
    case subscriptionFailed
    case productionFailed
    case invalidResponse
    case connectionFailed(String)
    
    var errorDescription: String? {
        switch self {
        case .consumerCreationFailed:
            return "Failed to create Kafka consumer. Check if REST Proxy is running."
        case .consumerNotCreated:
            return "Consumer not created. Call createConsumer() first"
        case .subscriptionFailed:
            return "Failed to subscribe to Kafka topic"
        case .productionFailed:
            return "Failed to produce message to Kafka"
        case .invalidResponse:
            return "Invalid response from Kafka REST Proxy"
        case .connectionFailed(let message):
            return message
        }
    }
}

