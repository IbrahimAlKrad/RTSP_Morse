//
//  StreamTestView.swift
//  StreamingEx
//
//  Created by Ibrahim Al Krad on 17.11.25.
//

import SwiftUI

/// A simple view to manually send test data to the stream (works with both fake and real Kafka)
struct StreamTestView: View {
    @StateObject private var streamService = StreamService.shared
    @State private var testMessage: String = ""
    @State private var isSending = false
    @State private var sendError: String?
    
    var body: some View {
        VStack(spacing: 20) {
            Text("Stream Test (Kafka Producer)")
                .font(.headline)
                .padding()
            
            TextField("Enter message to send", text: $testMessage)
                .textFieldStyle(.roundedBorder)
                .padding(.horizontal)
            
            Button(action: {
                sendMessage(testMessage)
            }) {
                HStack {
                    if isSending {
                        ProgressView()
                            .scaleEffect(0.8)
                    }
                    Label("Send to Stream", systemImage: "paperplane.fill")
                }
                .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .padding(.horizontal)
            .disabled(testMessage.isEmpty || isSending)
            
            if let error = sendError {
                Text(error)
                    .font(.caption)
                    .foregroundStyle(.red)
                    .padding(.horizontal)
            }
            
            // Quick test buttons
            VStack(spacing: 10) {
                Text("Quick Test Messages:")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                
                HStack(spacing: 10) {
                    Button("Hello") {
                        sendMessage("Hello ")
                    }
                    .buttonStyle(.bordered)
                    .disabled(isSending)
                    
                    Button("World") {
                        sendMessage("World ")
                    }
                    .buttonStyle(.bordered)
                    .disabled(isSending)
                    
                    Button("Morse") {
                        sendMessage("Morse ")
                    }
                    .buttonStyle(.bordered)
                    .disabled(isSending)
                }
                
                HStack(spacing: 10) {
                    Button("Test") {
                        sendMessage("Test ")
                    }
                    .buttonStyle(.bordered)
                    .disabled(isSending)
                    
                    Button("Data") {
                        sendMessage("Data ")
                    }
                    .buttonStyle(.bordered)
                    .disabled(isSending)
                    
                    Button("Stream") {
                        sendMessage("Stream ")
                    }
                    .buttonStyle(.bordered)
                    .disabled(isSending)
                }
            }
            .padding()
            
            Spacer()
        }
        .padding()
    }
    
    private func sendMessage(_ message: String) {
        guard !message.isEmpty else { return }
        
        isSending = true
        sendError = nil
        
        Task {
            do {
                try await streamService.send(message)
                await MainActor.run {
                    if message == testMessage {
                        testMessage = ""
                    }
                    isSending = false
                }
            } catch {
                await MainActor.run {
                    sendError = "Failed to send: \(error.localizedDescription)"
                    isSending = false
                }
            }
        }
    }
}

#Preview {
    StreamTestView()
}

