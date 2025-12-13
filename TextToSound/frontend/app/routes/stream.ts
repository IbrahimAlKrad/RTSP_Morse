import { type LoaderFunctionArgs } from "react-router";
import { Kafka } from "kafkajs";

export async function loader({ request }: LoaderFunctionArgs) {
    const kafka = new Kafka({
        clientId: "frontend-client",
        brokers: [(process.env.KAFKA_BROKERS || "localhost:9095")],
    });

    const consumer = kafka.consumer({ groupId: "frontend-group-" + Date.now() });

    await consumer.connect();
    await consumer.subscribe({ topic: "morse_output", fromBeginning: false });

    const stream = new ReadableStream({
        async start(controller) {
            await consumer.run({
                eachMessage: async ({ topic, partition, message }) => {
                    const rawValue = message.value?.toString();
                    if (rawValue) {
                        let payload = { morse: rawValue, source: 'text' };
                        try {
                            const json = JSON.parse(rawValue);
                            if (json && (json.morse || json.source)) {
                                payload = json;
                            }
                        } catch (e) {
                            // Not JSON, assume raw string
                        }
                        const data = `data: ${JSON.stringify(payload)}\n\n`;
                        controller.enqueue(new TextEncoder().encode(data));
                    }
                },
            });
        },
        async cancel() {
            await consumer.disconnect();
        },
    });

    return new Response(stream, {
        headers: {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    });
}
