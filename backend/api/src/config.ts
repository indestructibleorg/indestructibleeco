// IndestructibleEco API Service Configuration
// URI: indestructibleeco://backend/api/config
// All environment variables use ECO_* prefix for namespace isolation.

const config = {
  nodeEnv: process.env.NODE_ENV || "development",
  port: parseInt(process.env.ECO_API_PORT || process.env.PORT || "3000", 10),
  logLevel: process.env.ECO_LOG_LEVEL || "info",
  logFormat: process.env.ECO_LOG_FORMAT || "json",

  // CORS
  corsOrigins: (process.env.ECO_CORS_ORIGINS || "http://localhost:5173")
    .split(",")
    .map((s: string) => s.trim()),

  // Supabase
  supabaseUrl: process.env.ECO_SUPABASE_URL || "",
  supabaseKey: process.env.ECO_SUPABASE_ANON_KEY || "",
  supabaseServiceRoleKey: process.env.ECO_SUPABASE_SERVICE_ROLE_KEY || "",
  jwtSecret: process.env.ECO_JWT_SECRET || "dev-secret-change-in-production",

  // Redis
  redisUrl: process.env.ECO_REDIS_URL || "redis://localhost:6379",

  // AI Service
  aiServiceGrpc: process.env.ECO_AI_GRPC_PORT
    ? `localhost:${process.env.ECO_AI_GRPC_PORT}`
    : (process.env.ECO_AI_SERVICE_GRPC || "localhost:8000"),
  aiServiceHttp: process.env.ECO_AI_HTTP_PORT
    ? `http://localhost:${process.env.ECO_AI_HTTP_PORT}`
    : (process.env.ECO_AI_SERVICE_HTTP || "http://localhost:8001"),

  // Rate Limiting
  rateLimitAuthenticated: parseInt(process.env.ECO_RATE_LIMIT_AUTHENTICATED || "100", 10),
  rateLimitPublic: parseInt(process.env.ECO_RATE_LIMIT_PUBLIC || "10", 10),
  rateLimitWindowMs: parseInt(process.env.ECO_RATE_LIMIT_WINDOW_MS || "60000", 10),

  // Service Discovery
  consulEndpoint: process.env.ECO_CONSUL_ENDPOINT || "http://localhost:8500",

  // Tracing
  jaegerEndpoint: process.env.ECO_JAEGER_ENDPOINT || "http://localhost:14268/api/traces",
};

export { config };
