/**
 * @ECO-governed
 * @ECO-layer: server
 * @ECO-semantic: rules-route
 * @ECO-audit-trail: ../.governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated - Rules API Routes
 */

import { Router } from 'express';
import { DatabaseService } from '../services/database';
import { Rule } from '../types';

const router = Router();
const dbService = new DatabaseService();

/**
 * GET /api/rules - Get all rules
 */
router.get('/', async (req, res) => {
  try {
    const rules = await dbService.getRules();
    res.json(rules);
  } catch (error) {
    res.status(500).json({ error: 'Failed to retrieve rules' });
  }
});

/**
 * GET /api/rules/:id - Get a specific rule
 */
router.get('/:id', async (req, res) => {
  try {
    const rules = await dbService.getRules();
    const rule = rules.find(r => r.id === req.params.id);

    if (!rule) {
      return res.status(404).json({ error: 'Rule not found' });
    }

    res.json(rule);
  } catch (error) {
    res.status(500).json({ error: 'Failed to retrieve rule' });
  }
});

/**
 * POST /api/rules - Add a new rule
 */
router.post('/', async (req, res) => {
  try {
    const ruleData: Rule = req.body;
    const rules = await dbService.getRules();
    rules.push(ruleData);
    await dbService.saveRules(rules);
    
    res.status(201).json(ruleData);
  } catch (error) {
    res.status(500).json({ error: 'Failed to add rule' });
  }
});

/**
 * PUT /api/rules/:id - Update a rule
 */
router.put('/:id', async (req, res) => {
  try {
    const rules = await dbService.getRules();
    const index = rules.findIndex(r => r.id === req.params.id);

    if (index === -1) {
      return res.status(404).json({ error: 'Rule not found' });
    }

    rules[index] = { ...rules[index], ...req.body };
    await dbService.saveRules(rules);
    
    res.json(rules[index]);
  } catch (error) {
    res.status(500).json({ error: 'Failed to update rule' });
  }
});

/**
 * DELETE /api/rules/:id - Delete a rule
 */
router.delete('/:id', async (req, res) => {
  try {
    const rules = await dbService.getRules();
    const filteredRules = rules.filter(r => r.id !== req.params.id);
    await dbService.saveRules(filteredRules);
    
    res.status(204).send();
  } catch (error) {
    res.status(500).json({ error: 'Failed to delete rule' });
  }
});

export default router;