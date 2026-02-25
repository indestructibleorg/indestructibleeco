# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: documentation
# @ECO-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
# Coding Standards

## Document Information

- **Version:** 1.0.0
- **Last Updated:** 2026-01-23
- **Author:** MachineNativeOps Engineering Team
- **Review Date:** 2027-01-23

---

## 1. Overview

### 1.1 Purpose

This document establishes comprehensive coding standards for MachineNativeOps, ensuring code quality, maintainability, and consistency across all projects. These standards apply to all programming languages and frameworks used within the organization.

### 1.2 Scope

This document applies to:
- All source code developed by MachineNativeOps
- All programming languages and frameworks
- All internal and open source projects
- All developers, contractors, and contributors
- Code reviews and pull requests

### 1.3 Objectives

The primary objectives of these standards are to:
- Ensure consistent code style across the organization
- Improve code readability and maintainability
- Reduce bugs and technical debt
- Facilitate code reviews and collaboration
- Enable automated code quality checks
- Support knowledge sharing and onboarding

---

## 2. General Principles

### 2.1 Code Quality

#### 2.1.1 Readability
- Write code that is easy to read and understand
- Use clear, descriptive names for variables, functions, and classes
- Keep functions and methods short and focused
- Avoid complex one-liners
- Add comments for complex logic

#### 2.1.2 Simplicity
- Follow the KISS (Keep It Simple, Stupid) principle
- Avoid over-engineering
- Choose simple solutions over clever ones
- Minimize code complexity
- Prefer explicit over implicit

#### 2.1.3 Maintainability
- Write code that is easy to modify and extend
- Follow SOLID principles
- Use design patterns appropriately
- Avoid tight coupling
- Write modular, reusable code

### 2.2 Performance

#### 2.2.1 Efficiency
- Consider performance implications of design decisions
- Optimize critical paths
- Avoid unnecessary computations
- Use appropriate data structures
- Profile and measure before optimizing

#### 2.2.2 Scalability
- Design for horizontal scaling
- Avoid resource leaks
- Use connection pooling
- Implement caching where appropriate
- Consider database query efficiency

### 2.3 Security

#### 2.3.1 Secure Coding
- Validate all input
- Sanitize output
- Use parameterized queries
- Avoid hardcoding secrets
- Implement proper authentication and authorization
- For internal security tooling that must use `eval()`/`exec()`, add explicit security headers and inline warnings documenting trusted input assumptions.
- Record remediation decisions in consolidated archives (for example, see `archive/consolidated-reports/misc/REMAINING_ISSUES_ANALYSIS.md`).
- Avoid creating new root-level status files for remediation updates.

#### 2.3.2 Dependency Management
- Keep dependencies up to date
- Regularly scan for vulnerabilities
- Use dependency locking
- Review third-party code
- Follow supply chain security best practices

---

## 3. Code Structure and Organization

### 3.1 File Organization

#### 3.1.1 Directory Structure
- Follow language-specific conventions
- Separate concerns (models, views, controllers)
- Organize by feature or module
- Keep related files together
- Use consistent naming for directories

#### 3.1.2 File Naming
- Use descriptive, meaningful names
- Follow language conventions (snake_case, PascalCase)
- Avoid abbreviations
- Keep names concise
- Use consistent casing

### 3.2 Code Layout

#### 3.2.1 Line Length
- Maximum line length: 80-100 characters
- Break long lines for readability
- Use meaningful line breaks
- Align related items vertically
- Avoid trailing whitespace

#### 3.2.2 Whitespace
- Use consistent indentation (2 or 4 spaces)
- Use blank lines to separate logical sections
- One space after commas and operators
- No spaces at line endings
- Use tabs only if required by language

---

## 4. Naming Conventions

### 4.1 General Rules

#### 4.1.1 Naming Principles
- Use descriptive, meaningful names
- Be consistent with language conventions
- Avoid abbreviations and acronyms
- Use pronounceable names
- Avoid misleading names

#### 4.1.2 Language-Specific Conventions

**Python**
```python
# Variables and functions: snake_case
user_name = "John Doe"
def calculate_total():
    pass

# Classes: PascalCase
class UserProfile:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRY_COUNT = 3

# Private members: single underscore
def _internal_method():
    pass
```

**JavaScript/TypeScript**
```javascript
// Variables and functions: camelCase
let userName = "John Doe";
function calculateTotal() {
  // ...
}

// Classes: PascalCase
class UserProfile {
  // ...
}

// Constants: UPPER_SNAKE_CASE
const MAX_RETRY_COUNT = 3;

// Private members: underscore prefix
class MyClass {
  _privateMethod() {
    // ...
  }
}
```

**Go**
```go
// Variables and functions: camelCase (exported), camelCase (private)
var userName = "John Doe"
func CalculateTotal() {  // Exported
  // ...
}
func calculateTotal() {  // Private
  // ...
}

// Constants: camelCase
const MaxRetryCount = 3

// Interfaces: PascalCase
type UserProfile interface {
  // ...
}
```

**Java**
```java
// Variables and methods: camelCase
String userName = "John Doe";
public void calculateTotal() {
  // ...
}

// Classes: PascalCase
public class UserProfile {
  // ...
}

// Constants: UPPER_SNAKE_CASE
public static final int MAX_RETRY_COUNT = 3;
```

### 4.2 Specific Naming Guidelines

#### 4.2.1 Boolean Variables
- Prefix with is, has, can, should
- Use positive naming
- Avoid double negatives

Examples:
```python
is_active = True
has_permission = False
can_edit = True
should_validate = True
```

#### 4.2.2 Function Names
- Use verbs or verb phrases
- Be specific about what the function does
- Use consistent naming patterns
- Avoid vague names like process(), handle()

Examples:
```python
def calculate_total():
    pass

def send_notification():
    pass

def validate_input():
    pass
```

#### 4.2.3 Class Names
- Use nouns or noun phrases
- Represent real-world entities or concepts
- Avoid generic names
- Use descriptive names

Examples:
```python
class UserProfile:
    pass

class OrderProcessor:
    pass

class DataRepository:
    pass
```

---

## 5. Documentation

### 5.1 Code Comments

#### 5.1.1 When to Comment
- Explain complex algorithms
- Document design decisions
- Clarify non-obvious code
- Provide context and rationale
- Add TODO and FIXME markers

#### 5.1.2 Comment Guidelines
- Write clear, concise comments
- Keep comments up to date
- Avoid redundant comments
- Use consistent comment style
- Prefer self-documenting code

#### 5.1.3 Comment Examples

**Good Comments**
```python
# Calculate compound interest using the formula:
# A = P(1 + r/n)^(nt)
# Where P is principal, r is annual rate, n is times compounded per year
def calculate_compound_interest(principal, rate, times_compounded, years):
    pass
```

**Bad Comments**
```python
# Function to calculate
def calculate(x, y, z):
    pass
```

### 5.2 Documentation Strings

#### 5.2.1 Docstring Format
- Use language-specific docstring conventions (PEP 257 for Python, JSDoc for JavaScript)
- Include description, parameters, return values, and examples
- Document public APIs
- Keep docstrings concise

#### 5.2.2 Python Docstrings
```python
def calculate_discount(price: float, discount_percentage: float) -> float:
    """
    Calculate the discounted price.
    
    Args:
        price: Original price of the item.
        discount_percentage: Discount percentage (0-100).
    
    Returns:
        Discounted price.
    
    Raises:
        ValueError: If discount_percentage is not between 0 and 100.
    
    Examples:
        >>> calculate_discount(100.0, 20.0)
        80.0
    """
    if discount_percentage < 0 or discount_percentage > 100:
        raise ValueError("Discount percentage must be between 0 and 100")
    
    return price * (1 - discount_percentage / 100)
```

#### 5.2.3 JavaScript JSDoc
```javascript
/**
 * Calculate the discounted price.
 * 
 * @param {number} price - Original price of the item.
 * @param {number} discountPercentage - Discount percentage (0-100).
 * @returns {number} Discounted price.
 * @throws {Error} If discountPercentage is not between 0 and 100.
 * 
 * @example
 * calculateDiscount(100.0, 20.0); // Returns 80.0
 */
function calculateDiscount(price, discountPercentage) {
  if (discountPercentage < 0 || discountPercentage > 100) {
    throw new Error("Discount percentage must be between 0 and 100");
  }
  
  return price * (1 - discountPercentage / 100);
}
```

---

## 6. Error Handling

### 6.1 Error Handling Principles

#### 6.1.1 Fail Fast
- Validate input early
- Check for errors immediately
- Fail with meaningful messages
- Avoid silent failures

#### 6.1.2 Graceful Degradation
- Handle expected errors gracefully
- Provide fallback behavior
- Log errors appropriately
- Inform users of issues

#### 6.1.3 Specific Exceptions
- Use specific exception types
- Catch specific exceptions
- Avoid generic catch blocks
- Preserve stack traces

### 6.2 Error Handling Examples

#### 6.2.1 Python Error Handling
```python
try:
    result = process_data(data)
except ValueError as e:
    logger.error(f"Invalid data: {e}")
    raise
except KeyError as e:
    logger.warning(f"Missing key: {e}")
    return None
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    raise
```

#### 6.2.2 JavaScript Error Handling
```javascript
try {
  const result = processData(data);
} catch (error) {
  if (error instanceof ValidationError) {
    logger.error(`Invalid data: ${error.message}`);
    throw error;
  } else if (error instanceof NotFoundError) {
    logger.warn(`Missing resource: ${error.message}`);
    return null;
  } else {
    logger.error(`Unexpected error: ${error}`);
    throw error;
  }
}
```

---

## 7. Testing

### 7.1 Testing Principles

#### 7.1.1 Test Coverage
- Aim for 80%+ code coverage
- Test critical paths thoroughly
- Test edge cases and error conditions
- Maintain test coverage over time

#### 7.1.2 Test Organization
- Organize tests by feature or module
- Use descriptive test names
- Keep tests independent and isolated
- Follow AAA pattern (Arrange, Act, Assert)

#### 7.1.3 Test Quality
- Tests should be fast and reliable
- Tests should be easy to understand
- Tests should be deterministic
- Tests should be maintainable

### 7.2 Unit Testing

#### 7.2.1 Unit Test Guidelines
- Test individual functions and methods
- Mock external dependencies
- Test both success and failure cases
- Use meaningful assertions

#### 7.2.2 Python Unit Tests
```python
import unittest

class TestCalculator(unittest.TestCase):
    def test_add_positive_numbers(self):
        result = add(2, 3)
        self.assertEqual(result, 5)
    
    def test_add_negative_numbers(self):
        result = add(-2, -3)
        self.assertEqual(result, -5)
    
    def test_divide_by_zero(self):
        with self.assertRaises(ValueError):
            divide(10, 0)
```

#### 7.2.3 JavaScript Unit Tests
```javascript
describe('Calculator', () => {
  test('adds positive numbers', () => {
    const result = add(2, 3);
    expect(result).toBe(5);
  });
  
  test('adds negative numbers', () => {
    const result = add(-2, -3);
    expect(result).toBe(-5);
  });
  
  test('throws error when dividing by zero', () => {
    expect(() => divide(10, 0)).toThrow();
  });
});
```

### 7.3 Integration Testing

#### 7.3.1 Integration Test Guidelines
- Test interactions between components
- Use test databases and services
- Test API endpoints
- Validate data flow

### 7.4 End-to-End Testing

#### 7.4.1 E2E Test Guidelines
- Test critical user flows
- Use real browsers and environments
- Test across different browsers
- Keep E2E tests minimal and focused

---

## 8. Code Review

### 8.1 Review Process

#### 8.1.1 Pull Request Guidelines
- Keep PRs small and focused
- Provide clear descriptions
- Link to related issues
- Include tests for new features
- Update documentation

#### 8.1.2 Review Checklist
- Code follows style guidelines
- Code is readable and understandable
- Tests are included and pass
- Documentation is updated
- No security vulnerabilities
- Performance considerations addressed

### 8.2 Review Feedback

#### 8.2.1 Providing Feedback
- Be constructive and respectful
- Explain the reasoning
- Suggest improvements
- Acknowledge good work
- Follow up on discussions

#### 8.2.2 Receiving Feedback
- Remain open to suggestions
- Ask clarifying questions
- Discuss alternatives
- Learn from reviews
- Update code based on feedback

---

## 9. Version Control

### 9.1 Git Workflow

#### 9.1.1 Branching Strategy
- Use feature branches for new features
- Use release branches for releases
- Use hotfix branches for critical fixes
- Keep main branch stable

#### 9.1.2 Commit Messages
- Use conventional commit format
- Write clear, descriptive messages
- Keep commits atomic
- Reference issue numbers

**Commit Message Format**
```
type(scope): subject

body

footer
```

**Examples**
```
feat(api): add user authentication endpoint

Add OAuth 2.0 authentication support for user login.
Includes token generation and refresh functionality.

Closes #123
```

```
fix(database): resolve connection pool leak

Fix issue where database connections were not being
properly released, causing connection pool exhaustion.

Fixes #456
```

### 9.2 Code Style Enforcement

#### 9.2.1 Linting
- Use language-specific linters
- Enforce style rules automatically
- Fix linting errors before committing
- Include linters in CI/CD pipeline

#### 9.2.2 Formatting
- Use automatic formatters
- Consistent formatting across projects
- Format on save when possible
- Configure formatters in IDE

**Common Tools**
- Python: Black, Flake8, Pylint
- JavaScript: ESLint, Prettier
- Go: gofmt, golint
- Java: Checkstyle, Google Java Format

---

## 10. Security Best Practices

### 10.1 Input Validation

#### 10.1.1 Validation Rules
- Validate all user input
- Use allowlist approach
- Validate data types and formats
- Sanitize input to prevent injection

#### 10.1.2 Examples
```python
# Validate email
import re
email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
if not re.match(email_pattern, user_input):
    raise ValueError("Invalid email format")

# SQL injection prevention
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

### 10.2 Secrets Management

#### 10.2.1 Secrets Guidelines
- Never hardcode secrets in code
- Use environment variables or secret managers
- Rotate secrets regularly
- Audit secret access
- Use different secrets for different environments

#### 10.2.2 Examples
```python
# Good: Use environment variables
import os
api_key = os.getenv('API_KEY')

# Bad: Hardcoded secrets
api_key = 'sk-1234567890abcdef'
```

---

## 11. Performance Guidelines

### 11.1 Optimization

#### 11.1.1 Performance Principles
- Measure before optimizing
- Focus on bottlenecks
- Consider trade-offs
- Profile and benchmark
- Document performance decisions

#### 11.1.2 Common Optimizations
- Use appropriate data structures
- Cache expensive operations
- Minimize database queries
- Use asynchronous operations
- Implement lazy loading

### 11.2 Database Queries

#### 11.2.1 Query Optimization
- Use indexes appropriately
- Avoid N+1 queries
- Select only needed columns
- Use query batching
- Monitor query performance

---

## 12. Language-Specific Guidelines

### 12.1 Python

#### 12.1.1 Style Guide
- Follow PEP 8
- Use type hints (PEP 484)
- Use f-strings for string formatting
- Prefer list comprehensions
- Use context managers for resource management

#### 12.1.2 Best Practices
- Use virtual environments
- Follow import order (stdlib, third-party, local)
- Use __main__ guard
- Prefer composition over inheritance
- Use dataclasses for data containers

### 12.2 JavaScript/TypeScript

#### 12.2.1 Style Guide
- Follow ESLint rules
- Use const and let, avoid var
- Use arrow functions appropriately
- Use template literals
- Use async/await for asynchronous code

#### 12.2.2 Best Practices
- Use TypeScript for type safety
- Handle promises properly
- Avoid global variables
- Use modules and imports
- Follow functional programming patterns

### 12.3 Go

#### 12.3.1 Style Guide
- Follow gofmt formatting
- Use short, descriptive names
- Use interfaces for abstraction
- Handle errors explicitly
- Use goroutines carefully

#### 12.3.2 Best Practices
- Use go modules for dependency management
- Follow idiomatic Go patterns
- Use defer for cleanup
- Use channels for communication
- Avoid panics in library code

---

## 13. Contact Information

### 13.1 Engineering Team

- **Email:** engineering@machinenativeops.io
- **Slack:** #engineering
- **Documentation:** [EXTERNAL_URL_REMOVED]

---

## 14. Related Documents

- API Standards
- Security Policy
- Testing Guidelines
- CI/CD Pipeline Documentation
- Architecture Guidelines

---

## 15. Change History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2026-01-23 | Initial creation | Engineering Team |
