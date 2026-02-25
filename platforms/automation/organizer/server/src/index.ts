/**
 * @ECO-governed
 * @ECO-layer: server
 * @ECO-semantic: main-entry
 * @ECO-audit-trail: ../.governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated - File Organizer Server Main Entry
 */

import express from 'express';
import filesRouter from './routes/files';
import rulesRouter from './routes/rules';
import tasksRouter from './routes/tasks';

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());
app.use('/api/files', filesRouter);
app.use('/api/rules', rulesRouter);
app.use('/api/tasks', tasksRouter);

app.listen(PORT, () => {
  console.log(`File Organizer Server running on port ${PORT}`);
});

export default app;