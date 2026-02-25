#!/usr/bin/env node

// @GL-governed
// @GL-layer: GL10-29
// @GL-semantic: naming-suggester-cli
// @GL-audit-trail: ../../governance/GL_SEMANTIC_ANCHOR.json

import { readFileSync, writeFileSync } from 'fs';
import { join } from 'path';
import { createSpinner } from 'nanospinner';

// @ts-ignore
const { program } = await import('commander');
// @ts-ignore
const axios = (await import('axios')).default;

// Configuration
const NAMING_PATTERNS = {
  deployment: /^(dev|staging|prod)-[a-z0-9-]+-deploy-v[0-9]+\.[0-9]+\.[0-9]+(-[A-Za-z0-9]+)?$/,
  service: /^(dev|staging|prod)-[a-z0-9-]+-svc-v[0-9]+\.[0-9]+\.[0-9]+(-[A-Za-z0-9]+)?$/,
  ingress: /^(dev|staging|prod)-[a-z0-9-]+-ing-v[0-9]+\.[0-9]+\.[0-9]+(-[A-Za-z0-9]+)?$/,
  configmap: /^(dev|staging|prod)-[a-z0-9-]+-cm-v[0-9]+\.[0-9]+\.[0-9]+(-[A-Za-z0-9]+)?$/,
  secret: /^(dev|staging|prod)-[a-z0-9-]+-secret-v[0-9]+\.[0-9]+\.[0-9]+(-[A-Za-z0-9]+)?$/
};

// Suggest valid names
function suggestName(type, appName, environment = 'dev', version = '1.0.0', suffix = '') {
  const base = `${environment}-${appName}`;
  const typeSuffix = {
    deployment: 'deploy',
    service: 'svc',
    ingress: 'ing',
    configmap: 'cm',
    secret: 'secret'
  }[type];

  const name = suffix 
    ? `${base}-${typeSuffix}-v${version}-${suffix}`
    : `${base}-${typeSuffix}-v${version}`;

  return name;
}

// Validate name against patterns
function validateName(name, type) {
  const pattern = NAMING_PATTERNS[type];
  if (!pattern) {
    throw new Error(`Unknown resource type: ${type}`);
  }
  return pattern.test(name);
}

// Check if name exists in Kubernetes or Git
async function checkNameExists(name, type) {
  try {
    // Check Kubernetes (if kubeconfig exists)
    // This is a simplified check - in production, use kubectl exec
    const result = await axios.get(`http://localhost:8080/api/v1/namespaces/default/${type}s/${name}`)
      .catch(() => ({ data: { kind: 'Status', status: 'Failure' } }));
    
    return result.data.kind !== 'Status';
  } catch (error) {
    // Assume it doesn't exist if we can't check
    return false;
  }
}

// Generate multiple suggestions
function generateSuggestions(type, appName, environment, count = 5) {
  const suggestions = [];
  for (let i = 0; i < count; i++) {
    const suffix = i > 0 ? `v${i + 1}` : '';
    suggestions.push(suggestName(type, appName, environment, '1.0.0', suffix));
  }
  return suggestions;
}

// CLI setup
program
  .name('suggest-name')
  .description('Suggest and validate Kubernetes resource names according to GL naming conventions')
  .version('1.0.0');

program
  .command('suggest')
  .description('Generate name suggestions')
  .requiredOption('-t, --type <type>', 'Resource type (deployment, service, ingress, configmap, secret)')
  .requiredOption('-a, --app <appName>', 'Application name')
  .option('-e, --environment <env>', 'Environment (dev, staging, prod)', 'dev')
  .option('-v, --version <version>', 'Version (e.g., 1.0.0)', '1.0.0')
  .option('-c, --count <count>', 'Number of suggestions', '5')
  .option('--check-exists', 'Check if names already exist', false)
  .action(async (options) => {
    const spinner = createSpinner('Generating suggestions...').start();
    
    try {
      const suggestions = generateSuggestions(
        options.type,
        options.app,
        options.environment,
        parseInt(options.count)
      );

      if (options.checkExists) {
        spinner.update('Checking name availability...');
        for (const suggestion of suggestions) {
          suggestion.exists = await checkNameExists(suggestion, options.type);
        }
      }

      spinner.success({ text: `Generated ${suggestions.length} suggestions` });

      console.log('\n📋 Suggested Names:\n');
      suggestions.forEach((s, i) => {
        const status = s.exists ? '❌ (exists)' : '✅ (available)';
        console.log(`${i + 1}. ${s} ${status}`);
      });

      console.log(`\n✅ Best available name: ${suggestions.find(s => !s.exists) || suggestions[0]}`);
    } catch (error) {
      spinner.error({ text: `Error: ${error.message}` });
      process.exit(1);
    }
  });

program
  .command('validate')
  .description('Validate a name against naming patterns')
  .requiredOption('-n, --name <name>', 'Name to validate')
  .requiredOption('-t, --type <type>', 'Resource type (deployment, service, ingress, configmap, secret)')
  .action((options) => {
    const isValid = validateName(options.name, options.type);
    
    if (isValid) {
      console.log(`✅ Name "${options.name}" is valid for type "${options.type}"`);
    } else {
      console.error(`❌ Name "${options.name}" is invalid for type "${options.type}"`);
      console.error(`\nExpected pattern: ${NAMING_PATTERNS[options.type]}`);
      process.exit(1);
    }
  });

program
  .command('list-patterns')
  .description('List all naming patterns')
  .action(() => {
    console.log('\n📋 Naming Patterns:\n');
    Object.entries(NAMING_PATTERNS).forEach(([type, pattern]) => {
      console.log(`${type}: ${pattern}`);
    });
  });

program
  .command('generate-labels')
  .description('Generate required labels for a resource')
  .requiredOption('-a, --app <appName>', 'Application name')
  .requiredOption('-e, --environment <env>', 'Environment (dev, staging, prod)')
  .requiredOption('-v, --version <version>', 'Version (e.g., 1.0.0)')
  .option('-o, --output <format>', 'Output format (json, yaml)', 'yaml')
  .action((options) => {
    const labels = {
      app: options.app,
      version: options.version,
      environment: options.environment,
      'managed-by': 'gl-platform',
      'governance-level': 'GL10-29'
    };

    if (options.output === 'json') {
      console.log(JSON.stringify(labels, null, 2));
    } else {
      console.log('labels:');
      Object.entries(labels).forEach(([key, value]) => {
        console.log(`  ${key}: ${value}`);
      });
    }
  });

// REST API server (optional)
if (process.argv.includes('--server')) {
  const express = await import('express');
  const app = express.default();
  
  app.use(express.json());
  
  app.get('/suggest', (req, res) => {
    const { type, app: appName, environment = 'dev', count = 5 } = req.query;
    const suggestions = generateSuggestions(type, appName, environment, parseInt(count));
    res.json({ suggestions });
  });
  
  app.post('/validate', (req, res) => {
    const { name, type } = req.body;
    const isValid = validateName(name, type);
    res.json({ valid: isValid, pattern: NAMING_PATTERNS[type] });
  });
  
  const PORT = process.env.PORT || 3009;
  app.listen(PORT, () => {
    console.log(`Naming Suggester API running on port ${PORT}`);
  });
} else {
  program.parse();
}