// @ECO-governed
// @ECO-layer: GL20-29
// @ECO-semantic: license-analyzer
// @ECO-audit-trail: ../../governance/GL_SEMANTIC_ANCHOR.json

import * as fs from 'fs';
import * as path from 'path';
import { LicenseInfo, AnalysisResult, Recommendation } from '../types';

export class LicenseAnalyzer {
  private licenseDatabase: { [key: string]: LicenseInfo } = {
    'MIT': {
      type: 'MIT',
      compatible: true,
      gplOrCopyleft: false,
      risk: 'low',
      description: 'Permissive license, minimal restrictions'
    },
    'Apache-2.0': {
      type: 'Apache-2.0',
      compatible: true,
      gplOrCopyleft: false,
      risk: 'low',
      description: 'Permissive license with patent grant'
    },
    'BSD-2-Clause': {
      type: 'BSD-2-Clause',
      compatible: true,
      gplOrCopyleft: false,
      risk: 'low',
      description: 'Permissive BSD license'
    },
    'BSD-3-Clause': {
      type: 'BSD-3-Clause',
      compatible: true,
      gplOrCopyleft: false,
      risk: 'low',
      description: 'Permissive BSD license with 3 clauses'
    },
    'ISC': {
      type: 'ISC',
      compatible: true,
      gplOrCopyleft: false,
      risk: 'low',
      description: 'Permissive license similar to MIT'
    },
    'GPL-2.0': {
      type: 'GPL-2.0',
      compatible: false,
      gplOrCopyleft: true,
      risk: 'high',
      description: 'Copyleft license requiring derivative works to be GPL'
    },
    'GPL-3.0': {
      type: 'GPL-3.0',
      compatible: false,
      gplOrCopyleft: true,
      risk: 'high',
      description: 'Strong copyleft license requiring derivative works to be GPL'
    },
    'AGPL-3.0': {
      type: 'AGPL-3.0',
      compatible: false,
      gplOrCopyleft: true,
      risk: 'critical',
      description: 'Strong copyleft with network use provisions'
    },
    'LGPL-2.1': {
      type: 'LGPL-2.1',
      compatible: true,
      gplOrCopyleft: true,
      risk: 'medium',
      description: 'Weak copyleft allowing dynamic linking'
    },
    'LGPL-3.0': {
      type: 'LGPL-3.0',
      compatible: true,
      gplOrCopyleft: true,
      risk: 'medium',
      description: 'Weak copyleft allowing dynamic linking'
    },
    'MPL-2.0': {
      type: 'MPL-2.0',
      compatible: true,
      gplOrCopyleft: true,
      risk: 'medium',
      description: 'Weak copyleft, file-level licensing'
    }
  };

  analyzeLicenses(repoPath: string): AnalysisResult {
    const projectLicense = this.detectProjectLicense(repoPath);
    const dependencyLicenses = this.scanDependencyLicenses(repoPath);
    const incompatibleLicenses = this.checkCompatibility(projectLicense, dependencyLicenses);
    const missingLicenses = this.checkMissingLicenses(repoPath);

    return {
      type: 'licenses',
      summary: `License analysis complete. Project license: ${projectLicense.type || 'None detected'}. ${incompatibleLicenses.length} incompatible dependencies found.`,
      data: {
        projectLicense,
        dependencyLicenses,
        incompatibleLicenses,
        missingLicenses,
        complianceReport: this.generateComplianceReport(projectLicense, dependencyLicenses)
      },
      insights: [
        projectLicense.type ? `Project uses ${projectLicense.type} license` : 'No project license detected',
        `${dependencyLicenses.filter(l => l.gplOrCopyleft).length} copyleft dependencies found`,
        'License compatibility analysis completed',
        'Risk assessment generated for all licenses'
      ],
      recommendations: this.generateRecommendations(projectLicense, dependencyLicenses, incompatibleLicenses),
      generatedAt: new Date()
    };
  }

  private detectProjectLicense(repoPath: string): LicenseInfo {
    const licenseFiles = ['LICENSE', 'LICENSE.txt', 'LICENSE.md', 'LICENSE-MIT', 'COPYING'];
    const licenseFile = licenseFiles.find(f => fs.existsSync(path.join(repoPath, f)));

    if (!licenseFile) {
      return {
        type: 'None',
        compatible: true,
        gplOrCopyleft: false,
        risk: 'high',
        description: 'No license file detected - code is not licensed for use'
      };
    }

    const content = fs.readFileSync(path.join(repoPath, licenseFile), 'utf-8').toLowerCase();
    
    for (const [key, info] of Object.entries(this.licenseDatabase)) {
      if (content.includes(key.toLowerCase()) || 
          content.includes(info.description.toLowerCase())) {
        return info;
      }
    }

    return {
      type: 'Unknown',
      compatible: false,
      gplOrCopyleft: false,
      risk: 'medium',
      description: 'License detected but type could not be identified'
    };
  }

  private scanDependencyLicenses(repoPath: string): any[] {
    const licenses: any[] = [];

    // Scan npm package.json licenses
    const packageJsonPath = path.join(repoPath, 'package.json');
    if (fs.existsSync(packageJsonPath)) {
      try {
        const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf-8'));
        const allDeps = {
          ...packageJson.dependencies,
          ...packageJson.devDependencies
        };

        // Check node_modules for actual licenses
        const nodeModulesPath = path.join(repoPath, 'node_modules');
        if (fs.existsSync(nodeModulesPath)) {
          for (const depName of Object.keys(allDeps)) {
            const depPath = path.join(nodeModulesPath, depName);
            const depPackagePath = path.join(depPath, 'package.json');
            
            if (fs.existsSync(depPackagePath)) {
              try {
                const depPackage = JSON.parse(fs.readFileSync(depPackagePath, 'utf-8'));
                const licenseInfo = this.parseLicenseString(depPackage.license || depPackage.licenses);
                
                licenses.push({
                  package: depName,
                  version: allDeps[depName],
                  ...licenseInfo
                });
              } catch (error) {
                // Ignore parse errors
              }
            }
          }
        }
      } catch (error) {
        // Ignore parse errors
      }
    }

    return licenses;
  }

  private parseLicenseString(license: any): LicenseInfo {
    if (typeof license === 'string') {
      const licenseKey = Object.keys(this.licenseDatabase).find(key => 
        license.toLowerCase().includes(key.toLowerCase())
      );
      
      return licenseKey 
        ? this.licenseDatabase[licenseKey]
        : {
            type: license,
            compatible: true,
            gplOrCopyleft: false,
            risk: 'low',
            description: 'License detected but not in database'
          };
    }

    if (Array.isArray(license)) {
      // Multiple licenses - take the most restrictive
      const infos = license.map(l => this.parseLicenseString(l));
      const hasGpl = infos.some(i => i.gplOrCopyleft);
      
      return {
        type: license.join(', '),
        compatible: !hasGpl,
        gplOrCopyleft: hasGpl,
        risk: hasGpl ? 'high' : 'low',
        description: 'Multiple licenses detected'
      };
    }

    if (typeof license === 'object' && license.type) {
      return this.parseLicenseString(license.type);
    }

    return {
      type: 'Unknown',
      compatible: true,
      gplOrCopyleft: false,
      risk: 'medium',
      description: 'License information not available'
    };
  }

  private checkCompatibility(projectLicense: LicenseInfo, dependencyLicenses: any[]): any[] {
    const incompatible: any[] = [];

    // If project is MIT/Apache/BSD (permissive), GPL dependencies may be incompatible
    const isPermissive = ['MIT', 'Apache-2.0', 'BSD-2-Clause', 'BSD-3-Clause', 'ISC'].includes(projectLicense.type);
    
    if (isPermissive) {
      for (const dep of dependencyLicenses) {
        if (dep.gplOrCopyleft) {
          incompatible.push({
            package: dep.package,
            license: dep.type,
            reason: 'Copyleft license may require project to be GPL',
            severity: 'high',
            recommendation: 'Replace with permissive alternative or consult legal counsel'
          });
        }
      }
    }

    return incompatible;
  }

  private checkMissingLicenses(repoPath: string): string[] {
    const missing: string[] = [];

    // Check for LICENSE file
    const licenseFiles = ['LICENSE', 'LICENSE.txt', 'LICENSE.md', 'COPYING'];
    const hasLicense = licenseFiles.some(f => fs.existsSync(path.join(repoPath, f)));

    if (!hasLicense) {
      missing.push('Project LICENSE file');
    }

    // Check for license in package.json
    const packageJsonPath = path.join(repoPath, 'package.json');
    if (fs.existsSync(packageJsonPath)) {
      try {
        const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf-8'));
        if (!packageJson.license && !packageJson.licenses) {
          missing.push('License field in package.json');
        }
      } catch (error) {
        // Ignore parse errors
      }
    }

    return missing;
  }

  private generateComplianceReport(projectLicense: LicenseInfo, dependencyLicenses: any[]): any {
    const report = {
      overallCompliance: 'compliant' as string,
      riskLevel: 'low' as string,
      copyleftDependencies: dependencyLicenses.filter(l => l.gplOrCopyleft).length,
      totalDependencies: dependencyLicenses.length,
      licenseBreakdown: this.getLicenseBreakdown(dependencyLicenses),
      actionItems: [] as string[]
    };

    const incompatible = this.checkCompatibility(projectLicense, dependencyLicenses);
    if (incompatible.length > 0) {
      report.overallCompliance = 'non-compliant';
      report.riskLevel = 'high';
      report.actionItems.push('Review and address incompatible copyleft dependencies');
    }

    if (!projectLicense.type || projectLicense.type === 'None') {
      report.overallCompliance = 'non-compliant';
      report.riskLevel = 'high';
      report.actionItems.push('Add a license file to the project');
    }

    if (report.copyleftDependencies > 0) {
      report.riskLevel = report.riskLevel === 'high' ? 'high' : 'medium';
      report.actionItems.push('Document usage of copyleft licenses');
    }

    return report;
  }

  private getLicenseBreakdown(dependencyLicenses: any[]): any {
    const breakdown: { [key: string]: number } = {};

    for (const dep of dependencyLicenses) {
      const license = dep.type || 'Unknown';
      breakdown[license] = (breakdown[license] || 0) + 1;
    }

    return breakdown;
  }

  private generateRecommendations(projectLicense: LicenseInfo, dependencyLicenses: any[], incompatible: any[]): Recommendation[] {
    const recommendations: Recommendation[] = [];

    // Project license recommendations
    if (!projectLicense.type || projectLicense.type === 'None') {
      recommendations.push({
        category: 'licensing',
        priority: 'critical',
        description: 'Add a LICENSE file to clearly define usage terms',
        actionable: true,
        estimatedEffort: '30 minutes'
      });
    }

    // Incompatible license recommendations
    for (const inc of incompatible) {
      recommendations.push({
        category: 'licensing',
        priority: 'high',
        description: `Address incompatible license for ${inc.package}: ${inc.reason}`,
        actionable: true,
        estimatedEffort: '2-4 hours'
      });
    }

    // Copyleft license recommendations
    const copyleftDeps = dependencyLicenses.filter(l => l.gplOrCopyleft);
    if (copyleftDeps.length > 0) {
      recommendations.push({
        category: 'licensing',
        priority: 'medium',
        description: `Document ${copyleftDeps.length} copyleft dependencies and their implications`,
        actionable: true,
        estimatedEffort: '1-2 hours'
      });
    }

    // General recommendations
    recommendations.push({
      category: 'process',
      priority: 'low',
      description: 'Implement automated license scanning in CI/CD pipeline',
      actionable: true,
      estimatedEffort: '2-4 hours'
    });

    return recommendations;
  }
}