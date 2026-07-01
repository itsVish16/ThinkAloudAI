# Scalable User Service API Documentation

This document outlines all available endpoints, their responsibilities, and input/output schemas.

## POST `/api/v1/users/signup`
**Responsibility:** Register a new user

> Creates a new user account and sends a 6-digit OTP for email verification.

### Input Schema
**Type:** `SignupRequest`

### Output Schema
**201** - User created and verification email sent
Returns `MessageResponse`

**409** - Email or username already exists


**429** - Rate limit exceeded


**422** - Validation Error
Returns `HTTPValidationError`

## POST `/api/v1/users/login`
**Responsibility:** Login and obtain access tokens

> Authenticates a user via email and password. Returns JWT access and refresh tokens. Fails if email is unverified.

### Input Schema
**Type:** `LoginRequest`

### Output Schema
**200** - Successfully authenticated
Returns `TokenResponse`

**401** - Invalid email or password


**403** - Email not verified


**429** - Too many failed login attempts


**422** - Validation Error
Returns `HTTPValidationError`

## POST `/api/v1/users/refresh`
**Responsibility:** Refresh access token

> Takes a valid refresh token and issues a new pair of access and refresh tokens. The old refresh token is blacklisted.

### Input Schema
**Type:** `RefreshTokenRequest`

### Output Schema
**200** - Successfully refreshed tokens
Returns `TokenResponse`

**401** - Invalid, expired, or blacklisted refresh token


**429** - Rate limit exceeded


**422** - Validation Error
Returns `HTTPValidationError`

## POST `/api/v1/users/logout`
**Responsibility:** Logout user

> Logs the user out by blacklisting both the current access token and the provided refresh token.

### Input Schema
**Type:** `LogoutRequest`

### Output Schema
**200** - Successfully logged out
Returns `MessageResponse`

**401** - Missing or invalid authorization header


**422** - Validation Error
Returns `HTTPValidationError`

## POST `/api/v1/users/forgot-password`
**Responsibility:** Request password reset

> Initiates the password reset flow. Sends a 6-digit OTP to the user's email if it exists.

### Input Schema
**Type:** `ForgotPasswordRequest`

### Output Schema
**200** - Password reset instructions sent (or email ignored if non-existent)
Returns `MessageResponse`

**429** - Rate limit exceeded


**422** - Validation Error
Returns `HTTPValidationError`

## POST `/api/v1/users/reset-password`
**Responsibility:** Reset password via OTP

> Completes the password reset flow by verifying the 6-digit OTP and setting the new password.

### Input Schema
**Type:** `ResetPasswordRequest`

### Output Schema
**200** - Password successfully reset
Returns `MessageResponse`

**400** - Invalid or expired OTP


**429** - Rate limit exceeded


**422** - Validation Error
Returns `HTTPValidationError`

## GET `/api/v1/users/me`
**Responsibility:** Get current user profile

> Retrieves the profile information for the currently authenticated user. Uses Redis caching for high performance.

### Output Schema
**200** - User profile returned
Returns `UserResponse`

**401** - Not authenticated


## PATCH `/api/v1/users/me`
**Responsibility:** Update current user profile

> Updates the profile information (username, full_name) for the currently authenticated user.

### Input Schema
**Type:** `UpdateUserRequest`

### Output Schema
**200** - User profile successfully updated
Returns `UserResponse`

**401** - Not authenticated


**409** - Username already taken


**422** - Validation Error
Returns `HTTPValidationError`

## POST `/api/v1/users/verify-email`
**Responsibility:** Verify email via OTP

> Verifies a user's email address using the 6-digit OTP sent during registration.

### Input Schema
**Type:** `VerifyEmailRequest`

### Output Schema
**200** - Email successfully verified
Returns `MessageResponse`

**400** - Invalid or expired verification token


**429** - Rate limit exceeded


**422** - Validation Error
Returns `HTTPValidationError`

## POST `/api/v1/users/resend-verification`
**Responsibility:** Resend verification OTP

> Generates and sends a new 6-digit verification OTP to the user's email.

### Input Schema
**Type:** `ResendVerificationRequest`

### Output Schema
**200** - Verification instructions resent
Returns `MessageResponse`

**429** - Rate limit exceeded


**422** - Validation Error
Returns `HTTPValidationError`

## GET `/api/v1/users/me/skills`
**Responsibility:** Get user skills

> Retrieves the current user's learning skills and scores.

### Output Schema
**200** - List of user skills
```json
{
  "items": {
    "$ref": "#/components/schemas/SkillResponse"
  },
  "type": "array",
  "title": "Response Get Me Skills Api V1 Users Me Skills Get"
}
```

**401** - Not authenticated


## GET `/api/v1/users/me/events`
**Responsibility:** Get user learning events

> Retrieves the current user's recent learning events (max 100).

### Output Schema
**200** - List of learning events
```json
{
  "items": {
    "$ref": "#/components/schemas/LearningEventResponse"
  },
  "type": "array",
  "title": "Response Get Me Events Api V1 Users Me Events Get"
}
```

**401** - Not authenticated


## GET `/health/live`
**Responsibility:** Get Health Live

### Output Schema
**200** - Successful Response


## GET `/health/ready`
**Responsibility:** Get Health Ready

### Output Schema
**200** - Successful Response


## Data Models (Schemas)

### ForgotPasswordRequest
| Field | Type | Description |
|---|---|---|
| `email` | `string` | Email address associated with the account |


### HTTPValidationError
| Field | Type | Description |
|---|---|---|
| `detail` | `array` |  |


### LearningEventResponse
| Field | Type | Description |
|---|---|---|
| `event_type` | `string` | The type of event (e.g., ProblemSolved) |
| `reference_id` | `string, null` | External reference ID (e.g., problem ID or interview ID) |
| `score_change` | `integer` | How much the score changed |
| `created_at` | `string` | When the event occurred |


### LoginRequest
| Field | Type | Description |
|---|---|---|
| `email` | `string` | Registered email address |
| `password` | `string` | Account password |


### LogoutRequest
| Field | Type | Description |
|---|---|---|
| `refresh_token` | `string` | The refresh token to be blacklisted along with the access token |


### MessageResponse
| Field | Type | Description |
|---|---|---|
| `message` | `string` | A human-readable status message |


### RefreshTokenRequest
| Field | Type | Description |
|---|---|---|
| `refresh_token` | `string` | A valid JWT refresh token |


### ResendVerificationRequest
| Field | Type | Description |
|---|---|---|
| `email` | `string` | Registered email address |


### ResetPasswordRequest
| Field | Type | Description |
|---|---|---|
| `email` | `string` | Registered email address |
| `otp` | `string` | 6-digit OTP sent to the email |
| `new_password` | `string` | New strong password |


### SignupRequest
| Field | Type | Description |
|---|---|---|
| `username` | `string` | Unique alphanumeric username (3-30 chars) |
| `email` | `string` | Valid email address |
| `full_name` | `string` | User's full name |
| `password` | `string` | Strong password (min 8 chars, 1 uppercase, 1 number) |


### SkillResponse
| Field | Type | Description |
|---|---|---|
| `domain` | `string` | The learning domain (e.g., python, frontend) |
| `score` | `integer` | Current score/proficiency in the domain |
| `updated_at` | `string` | When the skill was last updated |


### TokenResponse
| Field | Type | Description |
|---|---|---|
| `access_token` | `string` | JWT access token (expires quickly) |
| `refresh_token` | `string` | JWT refresh token (lasts longer) |
| `token_type` | `string` | Token type, usually 'bearer' |


### UpdateUserRequest
| Field | Type | Description |
|---|---|---|
| `username` | `string, null` | New unique username (3-30 chars) |
| `full_name` | `string, null` | New full name |


### UserResponse
| Field | Type | Description |
|---|---|---|
| `id` | `integer` | Unique internal user ID |
| `username` | `string` | Unique username |
| `email` | `string` | User's email address |
| `full_name` | `string` | User's full name |
| `is_verified` | `boolean` | Whether the user has verified their email |
| `created_at` | `string` | Account creation timestamp |
| `updated_at` | `string` | Last account update timestamp |
| `last_login_at` | `string, null` | Timestamp of last successful login |


### ValidationError
| Field | Type | Description |
|---|---|---|
| `loc` | `array` |  |
| `msg` | `string` |  |
| `type` | `string` |  |
| `input` | `any` |  |
| `ctx` | `object` |  |


### VerifyEmailRequest
| Field | Type | Description |
|---|---|---|
| `email` | `string` | Registered email address |
| `token` | `string` | 6-digit verification OTP |

