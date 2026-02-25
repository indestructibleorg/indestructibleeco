/**
 * @ECO-governed
 * @ECO-layer: server
 * @ECO-semantic: tasks-route
 * @ECO-audit-trail: ../.governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated - Tasks API Routes
 */

import { Router } from 'express';
import { DatabaseService } from '../services/database';
import { ClassificationService } from '../services/classification';
import { OrganizationService } from '../services/organization';
import { Task } from '../types';

const router = Router();
const dbService = new DatabaseService();
const classificationService = new ClassificationService();
const organizationService = new OrganizationService();

/**
 * GET /api/tasks - Get all tasks
 */
router.get('/', async (req, res) => {
  try {
    const tasks = await dbService.getTasks();
    res.json(tasks);
  } catch (error) {
    res.status(500).json({ error: 'Failed to retrieve tasks' });
  }
});

/**
 * GET /api/tasks/:id - Get a specific task
 */
router.get('/:id', async (req, res) => {
  try {
    const tasks = await dbService.getTasks();
    const task = tasks.find(t => t.id === req.params.id);

    if (!task) {
      return res.status(404).json({ error: 'Task not found' });
    }

    res.json(task);
  } catch (error) {
    res.status(500).json({ error: 'Failed to retrieve task' });
  }
});

/**
 * POST /api/tasks - Create a new task
 */
router.post('/', async (req, res) => {
  try {
    const taskData: Task = req.body;
    const tasks = await dbService.getTasks();
    tasks.push(taskData);
    await dbService.saveTasks(tasks);
    
    res.status(201).json(taskData);
  } catch (error) {
    res.status(500).json({ error: 'Failed to create task' });
  }
});

/**
 * POST /api/tasks/:id/execute - Execute a task
 */
router.post('/:id/execute', async (req, res) => {
  try {
    const tasks = await dbService.getTasks();
    const task = tasks.find(t => t.id === req.params.id);

    if (!task) {
      return res.status(404).json({ error: 'Task not found' });
    }

    // Update task status
    task.status = 'running';
    await dbService.saveTasks(tasks);

    // Execute task based on type
    let result: any;
    const files = await dbService.getFiles();
    const taskFiles = files.filter(f => task.files.includes(f.id));

    switch (task.type) {
      case 'classify':
        const classifications = await classificationService.classifyFiles(taskFiles);
        result = Object.fromEntries(classifications);
        break;
      case 'organize':
        const rules = await dbService.getRules();
        const orgResults = await organizationService.organizeFiles(taskFiles, rules);
        result = Object.fromEntries(orgResults);
        break;
      case 'validate':
        const structure = await organizationService.validateStructure('.');
        result = structure;
        break;
      default:
        throw new Error('Unknown task type');
    }

    // Update task status
    task.status = 'completed';
    task.completedAt = new Date();
    task.result = result;
    await dbService.saveTasks(tasks);
    
    res.json(task);
  } catch (error) {
    res.status(500).json({ error: `Failed to execute task: ${error}` });
  }
});

export default router;