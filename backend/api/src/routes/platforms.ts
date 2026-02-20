/**
 * IndestructibleEco — Platform Routes
 * URI: indestructibleeco://backend/api/routes/platforms
 *
 * CRUD for platforms backed by Supabase.
 * Admin-only for create/update/delete; authenticated read for all.
 */

import { Router, Response, NextFunction } from "express";
import { v1 as uuidv1 } from "uuid";
import { AuthenticatedRequest, adminOnly } from "../middleware/auth";
import { AppError } from "../middleware/error-handler";
import * as db from "../services/supabase";

const platformRouter = Router();

// GET /api/v1/platforms
platformRouter.get("/", async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  try {
    const platforms = await db.listPlatforms();
    res.status(200).json({
      platforms,
      total: platforms.length,
    });
  } catch (err) {
    next(err);
  }
});

// POST /api/v1/platforms
platformRouter.post("/", adminOnly, async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  try {
    const { name, slug, type, config: platformConfig, capabilities, deploy_target } = req.body;
    if (!name || !slug) {
      throw new AppError(400, "validation_error", "Name and slug are required");
    }

    const existing = await db.getPlatformById(slug);
    if (existing) {
      throw new AppError(409, "conflict", `Platform with slug '${slug}' already exists`);
    }

    const platform = await db.createPlatform({
      name,
      slug,
      type: type || "custom",
      config: platformConfig || {},
      capabilities: capabilities || [],
      owner_id: req.user!.id,
      k8s_namespace: "indestructibleeco",
      deploy_target: deploy_target || "",
      urn: `urn:indestructibleeco:platform:module:${slug}:${uuidv1()}`,
    });

    res.status(201).json({ platform });
  } catch (err) {
    next(err);
  }
});

// GET /api/v1/platforms/:id
platformRouter.get("/:id", async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  try {
    const platform = await db.getPlatformById(req.params.id as string);
    if (!platform) {
      throw new AppError(404, "not_found", "Platform not found");
    }
    res.status(200).json({ platform });
  } catch (err) {
    next(err);
  }
});

// PATCH /api/v1/platforms/:id
platformRouter.patch("/:id", adminOnly, async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  try {
    const existing = await db.getPlatformById(req.params.id as string);
    if (!existing) {
      throw new AppError(404, "not_found", "Platform not found");
    }

    const { name, status, config: platformConfig, capabilities, deploy_target } = req.body;
    const updates: Record<string, unknown> = {};
    if (name !== undefined) updates.name = name;
    if (status !== undefined) updates.status = status;
    if (platformConfig !== undefined) updates.config = platformConfig;
    if (capabilities !== undefined) updates.capabilities = capabilities;
    if (deploy_target !== undefined) updates.deploy_target = deploy_target;

    const platform = await db.updatePlatform(req.params.id as string, updates);
    res.status(200).json({ platform });
  } catch (err) {
    next(err);
  }
});

// DELETE /api/v1/platforms/:id
platformRouter.delete("/:id", adminOnly, async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  try {
    const existing = await db.getPlatformById(req.params.id as string);
    if (!existing) {
      throw new AppError(404, "not_found", "Platform not found");
    }

    await db.deletePlatform(req.params.id as string);

    res.status(200).json({
      message: "Platform deregistered",
      id: req.params.id as string,
      urn: existing.urn,
    });
  } catch (err) {
    next(err);
  }
});

export { platformRouter };