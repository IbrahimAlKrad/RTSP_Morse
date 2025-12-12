//
//  KafkaConfig.swift
//  StreamingEx
//
//  Created by Ibrahim Al Krad on 17.11.25.
//

import Foundation

/// Configuration for Kafka connection
struct KafkaConfig {
    // Kafka REST Proxy endpoint (e.g., "http://localhost:8082" or "https://your-kafka-rest-proxy.com")
    let restProxyURL: String
    
    // Kafka topic name
    let topic: String
    
    // Consumer group ID
    let consumerGroup: String
    
    // Optional: Authentication headers if needed
    let authHeaders: [String: String]?
    
    // Optional: SSL/TLS configuration
    let useSSL: Bool
    
    static let `default` = KafkaConfig(
        restProxyURL: "http://localhost:8082",
        topic: "morse-stream",
        consumerGroup: "morse-app-consumer",
        authHeaders: nil,
        useSSL: false
    )
}


