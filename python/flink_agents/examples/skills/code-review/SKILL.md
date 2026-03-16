---
name: code-review
description: Review and improve code quality. Use when the user asks for code review, wants to improve code quality, or mentions best practices.
license: Apache-2.0
---

# Code Review Skill

This skill provides guidelines for reviewing code and suggesting improvements.

## When to Use

Use this skill when:
- Reviewing pull requests
- Improving code quality
- Checking for best practices
- Identifying potential bugs

## Review Checklist

### Code Style
- [ ] Follows language-specific naming conventions
- [ ] Proper indentation and formatting
- [ ] No magic numbers or hardcoded values
- [ ] DRY (Don't Repeat Yourself) principle followed

### Code Quality
- [ ] Functions are small and focused
- [ ] Clear and descriptive variable names
- [ ] Proper error handling
- [ ] No unnecessary comments (code should be self-documenting)

### Security
- [ ] No sensitive data exposed
- [ ] Input validation present
- [ ] SQL injection prevention
- [ ] XSS prevention for web applications

### Performance
- [ ] No obvious performance bottlenecks
- [ ] Efficient data structures used
- [ ] Caching applied where appropriate

### Testing
- [ ] Unit tests present
- [ ] Edge cases covered
- [ ] Test coverage is adequate

## Review Comments Format

When providing feedback, use:

```
**Issue**: Description of the issue
**Location**: File:line
**Severity**: Critical/High/Medium/Low
**Suggestion**: How to fix the issue
```

## Best Practices by Language

### Python
- Follow PEP 8 style guide
- Use type hints
- Write docstrings for public functions
- Use context managers for resource handling

### Java
- Follow Java naming conventions
- Use Optional instead of null
- Prefer immutability
- Use try-with-resources

### JavaScript/TypeScript
- Use const/let instead of var
- Prefer arrow functions
- Use async/await over callbacks
- Enable strict mode
