//
//  WebSocketClient.swift
//  StreamingEx
//
//  WebSocket client for receiving Kafka messages in real-time
//

import Foundation
import Combine

/// Message received from the WebSocket bridge
struct KafkaWebSocketMessage: Codable {
    let topic: String?
    let message: String?
    let type: String?
    let timestamp: Double?
}

/// WebSocket client that connects to the Kafka bridge
@MainActor
class WebSocketClient: NSObject, ObservableObject {
    static let shared = WebSocketClient()
    
    @Published var isConnected = false
    @Published var lastError: String?
    @Published var receivedMessages: [String] = []
    
    private var webSocketTask: URLSessionWebSocketTask?
    private var urlSession: URLSession?
    private var serverURL: URL?
    private var messageHandler: ((String, String) -> Void)?
    
    // Connection settings (saved to UserDefaults)
    var savedServerURL: String {
        get { UserDefaults.standard.string(forKey: "websocket_server_url") ?? "ws://192.168.188.32:8765" }
        set { UserDefaults.standard.set(newValue, forKey: "websocket_server_url") }
    }
    
    private override init() {
        super.init()
    }
    
    /// Connect to the WebSocket server
    nonisolated func connect(to urlString: String? = nil, onMessage: @escaping (String, String) -> Void) {
        Task { @MainActor in
            await connectAsync(to: urlString, onMessage: onMessage)
        }
    }
    
    private func connectAsync(to urlString: String? = nil, onMessage: @escaping (String, String) -> Void) async {
        let serverURLString = urlString ?? savedServerURL
        
        guard let url = URL(string: serverURLString) else {
            print("❌ WebSocketClient: Invalid URL: \(serverURLString)")
            lastError = "Invalid URL"
            return
        }
        
        // Save the URL for next time
        if urlString != nil {
            savedServerURL = serverURLString
        }
        
        serverURL = url
        messageHandler = onMessage
        
        // Disconnect existing connection
        disconnectInternal()
        
        print("🔌 WebSocketClient: Connecting to \(serverURLString)...")
        
        // Create URL session with delegate on main queue
        let config = URLSessionConfiguration.default
        config.waitsForConnectivity = true
        
        // Create a non-isolated delegate wrapper
        let delegateWrapper = WebSocketDelegateWrapper { [weak self] connected, error in
            Task { @MainActor in
                self?.isConnected = connected
                self?.lastError = error
            }
        }
        
        urlSession = URLSession(configuration: config, delegate: delegateWrapper, delegateQueue: OperationQueue.main)
        
        // Create WebSocket task
        webSocketTask = urlSession?.webSocketTask(with: url)
        webSocketTask?.resume()
        
        // Start receiving messages
        startReceiving()
    }
    
    private func disconnectInternal() {
        webSocketTask?.cancel(with: .normalClosure, reason: nil)
        webSocketTask = nil
        isConnected = false
    }
    
    /// Disconnect from the WebSocket server
    nonisolated func disconnect() {
        Task { @MainActor in
            disconnectInternal()
            print("🔌 WebSocketClient: Disconnected")
        }
    }
    
    /// Send a message to the server
    nonisolated func send(_ message: String) {
        Task { @MainActor in
            guard let webSocketTask = webSocketTask else {
                print("❌ WebSocketClient: Not connected")
                return
            }
            
            let wsMessage = URLSessionWebSocketTask.Message.string(message)
            do {
                try await webSocketTask.send(wsMessage)
                print("📤 WebSocketClient: Sent: \(message)")
            } catch {
                print("❌ WebSocketClient: Send error: \(error)")
            }
        }
    }
    
    /// Start receiving messages
    private func startReceiving() {
        Task {
            await receiveLoop()
        }
    }
    
    /// Receive messages in a loop
    private func receiveLoop() async {
        guard let webSocketTask = webSocketTask else { return }
        
        do {
            while !Task.isCancelled {
                let message = try await webSocketTask.receive()
                
                switch message {
                case .string(let text):
                    handleMessage(text)
                case .data(let data):
                    if let text = String(data: data, encoding: .utf8) {
                        handleMessage(text)
                    }
                @unknown default:
                    break
                }
            }
        } catch {
            print("❌ WebSocketClient: Receive error: \(error)")
            isConnected = false
            lastError = error.localizedDescription
        }
    }
    
    /// Handle incoming message
    private func handleMessage(_ text: String) {
        print("📨 WebSocketClient: Received: \(text.prefix(100))...")
        
        // Try to parse as JSON
        if let data = text.data(using: .utf8),
           let wsMessage = try? JSONDecoder().decode(KafkaWebSocketMessage.self, from: data) {
            
            // Handle connection confirmation
            if wsMessage.type == "connected" {
                print("✅ WebSocketClient: Connected to bridge!")
                isConnected = true
                lastError = nil
                return
            }
            
            // Handle Kafka message
            if let topic = wsMessage.topic, let message = wsMessage.message {
                print("✅ WebSocketClient: Message from topic '\(topic)': \(message.prefix(50))...")
                receivedMessages.append(message)
                messageHandler?(topic, message)
            }
        } else {
            // Raw message
            receivedMessages.append(text)
            messageHandler?("unknown", text)
        }
    }
    
    /// Create an AsyncStream of messages
    nonisolated func messages(forTopic topic: String? = nil) -> AsyncStream<String> {
        return AsyncStream { continuation in
            Task { @MainActor in
                self.messageHandler = { receivedTopic, message in
                    // Filter by topic if specified
                    if topic == nil || receivedTopic == topic {
                        continuation.yield(message)
                    }
                }
            }
            
            continuation.onTermination = { _ in
                Task { @MainActor in
                    self.disconnectInternal()
                }
            }
        }
    }
}

// MARK: - WebSocket Delegate Wrapper (non-isolated)

class WebSocketDelegateWrapper: NSObject, URLSessionWebSocketDelegate {
    private let onConnectionChange: (Bool, String?) -> Void
    
    init(onConnectionChange: @escaping (Bool, String?) -> Void) {
        self.onConnectionChange = onConnectionChange
        super.init()
    }
    
    func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask, didOpenWithProtocol protocol: String?) {
        print("✅ WebSocketClient: Connection opened")
        onConnectionChange(true, nil)
    }
    
    func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask, didCloseWith closeCode: URLSessionWebSocketTask.CloseCode, reason: Data?) {
        print("🔌 WebSocketClient: Connection closed with code: \(closeCode)")
        onConnectionChange(false, nil)
    }
    
    func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: Error?) {
        if let error = error {
            print("❌ WebSocketClient: Task error: \(error)")
            onConnectionChange(false, error.localizedDescription)
        }
    }
}
