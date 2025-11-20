import { useState, useEffect } from "react";

export function useConnectionStatus() {
    const [connectionError, setConnectionError] = useState(true);

    useEffect(() => {
        console.log("[Heartbeat] Connecting to /health...");
        const healthStream = new EventSource("/health");
        let heartbeatTimeout: NodeJS.Timeout;

        const resetHeartbeatTimeout = () => {
            clearTimeout(heartbeatTimeout);
            // If no heartbeat received in 5 seconds, mark as disconnected
            heartbeatTimeout = setTimeout(() => {
                console.error("[Heartbeat] Timeout - backend not responding");
                setConnectionError(true);
            }, 5000);
        };

        healthStream.onopen = () => {
            console.log("[Heartbeat] Health stream opened");
            resetHeartbeatTimeout();
        };

        healthStream.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.status === "alive") {
                console.log("[Heartbeat] Received - backend connected");
                setConnectionError(false);
                resetHeartbeatTimeout();
            }
        };

        healthStream.onerror = (err) => {
            console.error("[Heartbeat] Connection error:", err);
            setConnectionError(true);
            clearTimeout(heartbeatTimeout);
            healthStream.close();
        };

        return () => {
            console.log("[Heartbeat] Closing health stream");
            clearTimeout(heartbeatTimeout);
            healthStream.close();
        };
    }, []);

    return { connectionError };
}
