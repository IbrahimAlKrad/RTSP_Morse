//
//  StreamingExApp.swift
//  StreamingEx
//
//  Created by Ibrahim Al Krad on 10.11.25.
//

import SwiftUI

@main
struct StreamingExApp: App {
    init() {
        print("🟥🟥🟥 APP STARTED - If you see this, console is working! 🟥🟥🟥")
        print("========================================")
    }
    
    var body: some Scene {
        WindowGroup {
            Morse()
        }
    }
}
