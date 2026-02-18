import { Router, Response, NextFunction } from "express";
import { v1 as uuidv1 } from "uuid";
import { AuthenticatedRequest, adminOnly } from "../middleware/auth";
import { AppError } from "../middleware/error-handler";

const platformRouter = Router();

// In-memory store (production: Supabase)
const platforms = new Map<string, PlatformRecord>();

interface PlatformRecord {
  id: string;
  name: string;
  slug: string;
  status: string;
  uri: string;
  urn: string;
  config: Record<string, unknown>;
  capabilities: string[];
  k8sNamespace: string;
  deployTarget: string;
  ownerId: string;
  createdAt: string;
  updatedAt: string;
}

// GET /api/v1/platforms
platformRouter.get("/", async (req: AuthenticatedRequest, res: Response) => {
  const list = Array.from(platforms.values());
  res.status(200).json({
    platforms: list,
    total: list.length,
  });
});

// POST /api/v1/platforms
platformRouter.post("/", adminOnly, async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  try {
    const { name, slug, config: platformConfig, capabilities, deployTarget } = req.body;
    if (!name || !slug) {
      throw new AppError(400, "validation_error", "Name and slug are required");
    }

    if (Array.from(platforms.values()).some((p) => p.slug === slug)) {
      throw new AppError(409, "conflict", `Platform with slug '${slug}' already exists`);
    }

    const id = uuidv1();
    const record: PlatformRecord = {
      id,
      name,
      slug,
      status: "inactive",
      uri: `indestructibleeco://platform/module/${slug}`,
      urn: `urn:indestructibleeco:platform:module:${slug}:${id}`,
      config: platformConfig || {},
      capabilities: capabilities || [],
      k8sNamespace: "indestructibleeco",
      deployTarget: deployTarget || "",
      ownerId: req.user!.id,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    platforms.set(id, record);

    res.status(201).json({ platform: record });
  } catch (err) {
    next(err);
  }
});

// GET /api/v1/platforms/:id
platformRouter.get("/:id", async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  try {
    const record = platforms.get(req.params.id);
    if (!record) {
      throw new AppError(404, "not_found", "Platform not found");
    }
    res.status(200).json({ platform: record });
  } catch (err) {
    next(err);
  }
});

// PATCH /api/v1/platforms/:id
platformRouter.patch("/:id", adminOnly, async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  try {
    const record = platforms.get(req.params.id);
    if (!record) {
      throw new AppError(404, "not_found", "Platform not found");
    }

    const { name, status, config: platformConfig, capabilities, deployTarget } = req.body;
    if (name !== undefined) record.name = name;
    if (status !== undefined) record.status = status;
    if (platformConfig !== undefined) record.config = platformConfig;
    if (capabilities !== undefined) record.capabilities = capabilities;
    if (deployTarget !== undefined) record.deployTarget = deployTarget;
    record.updatedAt = new Date().toISOString();

    platforms.set(req.params.id, record);

    res.status(200).json({ platform: record });
  } catch (err) {
    next(err);
  }
});

// DELETE /api/v1/platforms/:id
platformRouter.delete("/:id", adminOnly, async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  try {
    const record = platforms.get(req.params.id);
    if (!record) {
      throw new AppError(404, "not_found", "Platform not found");
    }

    platforms.delete(req.params.id);

    res.status(200).json({
      message: "Platform deregistered",
      id: req.params.id,
      urn: record.urn,
    });
  } catch (err) {
    next(err);
  }
});

export { platformRouter };