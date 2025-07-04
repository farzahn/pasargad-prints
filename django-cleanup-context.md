# Django Backend Cleanup and Frontend Alignment Context

## Task Description
Clean up the Django backend by removing unnecessary feature flags, deprecated code, and redundant functionality while ensuring the React frontend remains fully aligned with the backend changes. This involves coordinated work between backend and frontend specialists to maintain system integrity.

## Requirements
### Functional Requirements
- Audit and remove unused Django feature flags and settings
- Clean up deprecated API endpoints and serializers
- Remove redundant database models and migrations
- Update frontend API calls to match cleaned backend endpoints
- Ensure all frontend features continue working after backend cleanup
- Maintain backward compatibility for critical features during transition

### Non-Functional Requirements
- Performance: Reduce API response time by removing unnecessary middleware/processing
- Security: Remove any deprecated authentication methods or exposed debug endpoints
- Scalability: Streamline database queries and reduce unnecessary joins
- Maintainability: Improve code organization and remove technical debt

## Success Criteria
1. All unused feature flags removed from Django settings and codebase
2. Backend API surface area reduced by at least 30% (removing deprecated endpoints)
3. Frontend continues to function without errors after backend cleanup
4. All tests pass for both backend and frontend
5. API documentation updated to reflect current endpoints only
6. Database migrations consolidated where possible
7. No regression in existing functionality

## Configuration
```yaml
# Simple, focused configuration
workflow:
  specialists: 2          # Backend and Frontend specialists
  max_iterations: 3       # Allow for iterative cleanup
  target_quality: HIGH    # Must ensure no regressions

task:
  complexity: high        # Requires careful coordination
  domain: full_stack      # Django + React
  estimated_time: 6h      # Comprehensive cleanup

output:
  format: markdown        # Document all changes
  include_tests: true     # Update/add tests for changes
  documentation: inline   # Update inline documentation
```

## Constraints
- Cannot break existing user sessions or active orders
- Must maintain data integrity during migration consolidation
- Frontend must remain functional throughout the cleanup process
- Changes must be reversible in case of issues
- API versioning strategy must be considered for breaking changes

## Context and Background
The Pasargad Prints e-commerce platform has accumulated technical debt over time, including:
- Multiple authentication methods (JWT, session, social auth)
- Redundant feature flags for A/B testing that are no longer used
- Deprecated API endpoints from previous versions
- Duplicate serializers and viewsets
- Unnecessary middleware layers
- Frontend code that references deprecated or unused backend features

The goal is to streamline both codebases while maintaining full functionality.

## Current State Analysis
### Backend Issues to Address:
- Feature flags in settings: ENABLE_SOCIAL_SHARING, ENABLE_REVIEWS, ENABLE_WISHLIST, etc.
- Duplicate apps: reviews/review_system, referrals/referral_system
- Unused payment providers configurations
- Debug middleware in production settings
- Redundant caching layers

### Frontend Issues to Address:
- API calls to deprecated endpoints
- Unused Redux slices and actions
- Feature toggles that always return true
- Hardcoded configuration that should come from backend
- Unused component variations based on old feature flags

## Technical Specifications
- Language: Python 3.11+, TypeScript
- Framework: Django 4.2, React 18
- Database: PostgreSQL 15
- State Management: Redux Toolkit
- API: Django REST Framework
- Dependencies: See requirements.txt and package.json

## Specialist Responsibilities

### Backend Specialist (Mercury-1):
1. Audit Django settings for unused flags
2. Identify and remove deprecated API endpoints
3. Clean up redundant models and serializers
4. Consolidate duplicate apps
5. Optimize middleware stack
6. Update API documentation

### Frontend Specialist (Mercury-2):
1. Map all API calls to backend endpoints
2. Update API calls to use only active endpoints
3. Remove feature flag checks from components
4. Clean up unused Redux slices
5. Update TypeScript types to match new API
6. Ensure all features remain functional

## Coordination Points
1. Backend specialist provides list of endpoints to be removed
2. Frontend specialist confirms which are in use
3. Backend specialist provides new endpoint mappings
4. Frontend specialist updates API calls
5. Both specialists test integration points
6. Iterative testing and fixes as needed

## Notes
- Priority is on maintaining functionality over aggressive cleanup
- Create a rollback plan for each major change
- Document all removed features for future reference
- Consider creating a deprecation timeline for gradual removal
- Ensure proper communication between specialists at each phase