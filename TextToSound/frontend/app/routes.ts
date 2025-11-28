import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
    index("routes/home.tsx"),
    route("stream", "routes/stream.ts"),
    route("health", "routes/health.ts"),
] satisfies RouteConfig;
