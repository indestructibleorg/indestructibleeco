const config = {
  nodeEnv: process.env.NODE_ENV || "development",
  port: parseInt(process.env.PORT || "3000", 10),
  logLevel: process.env.LOG_LEVEL || "info",
  logFormat: process.env.LOG_FORMAT || "json",

  // CORS
  corsOrigins: (process.env.CORS_ORIGINS || "http://localhost:5173")
    .split(",")
    .map((s) => s.trim()),

  // Supabase
  supabaseUrl: process.env.SUPABASE_URL || "",
  supabaseKey: process.env.SUPABASE_KEY || "",
  jwtSecret: process.env.JWT_SECRET || "dev-secret-change-in-production",

  // Redis
  redisUrl: process.env.REDIS_URL || "redis://localhost:6379",

  // AI Service
  aiServiceGrpc: process.env.AI_SERVICE_GRPC || "localhost:8000",
  aiServiceHttp: process.env.AI_SERVICE_HTTP || "http://localhost:8001",

  // Rate Limiting
  rateLimitAuthenticated: parseInt(process.env.RATE_LIMIT_AUTHENTICATED || "100", 10),
  rateLimitPublic: parseInt(process.env.RATE_LIMIT_PUBLIC || "10", 10),
  rateLimitWindowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS || "60000", 10),

  // Service Discovery
  consulEndpoint: process.env.CONSUL_ENDPOINT || "http://localhost:8500",

  // Tracing
  jaegerEndpoint: process.env.JAEGER_ENDPOINT || "http://localhost:14268/api/traces",
};

export { config };