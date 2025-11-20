import { type LoaderFunctionArgs } from "react-router";
import { Kafka } from "kafkajs";

export async function loader({ request }: LoaderFunctionArgs) {
    const kafka = new Kafka({
        clientId: "frontend-client",
        brokers: ["localhost:9094"],
    });

    const consumer = kafka.consumer({ groupId: "frontend-group-" + Date.now() });

    await consumer.connect();
    await consumer.subscribe({ topic: "morse_output", fromBeginning: false });

    const stream = new ReadableStream({
        async start(controller) {
            await consumer.run({
                eachMessage: async ({ topic, partition, message }) => {
                    const text = message.value?.toString();
                    if (text) {
                        const data = `data: ${JSON.stringify({ morse: text })}\n\n`;
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
