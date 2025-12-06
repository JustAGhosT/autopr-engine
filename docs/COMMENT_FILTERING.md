# Comment Filtering Feature

## Overview

The Comment Filtering feature allows you to control which GitHub users can have their PR comments processed by AutoPR. By default, comment filtering is enabled in whitelist mode, meaning only explicitly allowed users will have their comments processed.

## Features

- **Whitelist/Blacklist Modes**: Choose to allow only specific users (whitelist) or block specific users (blacklist)
- **Auto-Add**: Automatically add new commenters to the allowed list
- **Auto-Reply**: Send automated welcome messages when adding new commenters
- **Activity Tracking**: Track comment count and last activity for each commenter
- **Dashboard API**: Manage settings and commenters through REST API endpoints

## Configuration

### Comment Filter Settings

The system uses a singleton settings record with the following options:

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable/disable comment filtering |
| `whitelist_mode` | boolean | `true` | Use whitelist (true) or blacklist (false) mode |
| `auto_add_commenters` | boolean | `false` | Automatically add new commenters to allowed list |
| `auto_reply_enabled` | boolean | `true` | Send auto-reply when adding new commenters |
| `auto_reply_message` | string | (template) | Message template for auto-replies |

### Filtering Modes

#### Whitelist Mode (Default)
- Only users in the allowed list can have comments processed
- New users are ignored unless manually added or auto-add is enabled
- Recommended for high-security environments

#### Blacklist Mode
- All users can have comments processed except those explicitly blocked
- Users are blocked by adding them to the list and disabling them
- Recommended for open projects

## API Endpoints

All endpoints require authentication if `AUTOPR_API_KEY` is configured.

### Get Settings

```http
GET /api/comment-filter/settings
```

**Response:**
```json
{
  "enabled": true,
  "whitelist_mode": true,
  "auto_add_commenters": false,
  "auto_reply_enabled": true,
  "auto_reply_message": "Thank you for your comment! User @{username} has been added..."
}
```

### Update Settings

```http
POST /api/comment-filter/settings
Content-Type: application/json

{
  "enabled": true,
  "whitelist_mode": true,
  "auto_add_commenters": false,
  "auto_reply_enabled": true,
  "auto_reply_message": "Welcome @{username}!"
}
```

### List Allowed Commenters

```http
GET /api/comment-filter/commenters?enabled_only=true&limit=100&offset=0
```

**Response:**
```json
[
  {
    "github_username": "octocat",
    "github_user_id": 12345,
    "enabled": true,
    "comment_count": 42,
    "last_comment_at": "2025-12-06T21:30:00Z",
    "created_at": "2025-12-01T10:00:00Z",
    "notes": "Core contributor"
  }
]
```

### Add Allowed Commenter

```http
POST /api/comment-filter/commenters
Content-Type: application/json

{
  "github_username": "octocat",
  "github_user_id": 12345,
  "notes": "Trusted contributor"
}
```

### Remove Allowed Commenter

```http
DELETE /api/comment-filter/commenters/octocat
```

## Usage Examples

### Example 1: Enable Comment Filtering

```bash
curl -X POST http://localhost:8080/api/comment-filter/settings \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "enabled": true,
    "whitelist_mode": true,
    "auto_add_commenters": false,
    "auto_reply_enabled": true,
    "auto_reply_message": "Thank you @{username}! You have been added to the allowed commenters list."
  }'
```

### Example 2: Add a Trusted Commenter

```bash
curl -X POST http://localhost:8080/api/comment-filter/commenters \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "github_username": "trusted-dev",
    "github_user_id": 98765,
    "notes": "Lead developer on the project"
  }'
```

### Example 3: List All Active Commenters

```bash
curl http://localhost:8080/api/comment-filter/commenters?enabled_only=true&limit=50 \
  -H "X-API-Key: your-api-key"
```

### Example 4: Block a User (Blacklist Mode)

```bash
# First, set to blacklist mode
curl -X POST http://localhost:8080/api/comment-filter/settings \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"whitelist_mode": false}'

# Then add the user to block them
curl -X POST http://localhost:8080/api/comment-filter/commenters \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"github_username": "spam-user"}'

# Finally, disable/block them
curl -X DELETE http://localhost:8080/api/comment-filter/commenters/spam-user \
  -H "X-API-Key: your-api-key"
```

## Database Schema

### allowed_commenters Table

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| github_username | VARCHAR(255) | GitHub username (unique) |
| github_user_id | INTEGER | GitHub user ID |
| enabled | BOOLEAN | Whether user is active |
| added_by | VARCHAR(255) | Who added this user |
| notes | TEXT | Optional notes |
| last_comment_at | TIMESTAMP | Last comment timestamp |
| comment_count | INTEGER | Total comment count |
| created_at | TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | Last update time |

### comment_filter_settings Table

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| enabled | BOOLEAN | Filter enabled flag |
| auto_add_commenters | BOOLEAN | Auto-add new users |
| auto_reply_enabled | BOOLEAN | Send auto-replies |
| auto_reply_message | TEXT | Reply message template |
| whitelist_mode | BOOLEAN | Whitelist vs blacklist |
| created_at | TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | Last update time |

## Webhook Integration

The comment filtering is automatically integrated with GitHub webhooks. When a PR comment is received:

1. The system checks if the commenter is allowed
2. If not allowed and auto-add is enabled, the commenter is added
3. If auto-reply is enabled, a welcome message is posted
4. The comment is processed only if the user is allowed

## Migration

To enable this feature in your database:

```bash
# Run the migration
poetry run alembic upgrade head
```

This will create the necessary tables and insert default settings.

## Security Considerations

- **API Authentication**: Always use API key authentication in production
- **Rate Limiting**: The dashboard API endpoints are rate-limited
- **Audit Trail**: All additions/removals are logged with timestamps
- **Soft Deletes**: Removing commenters disables them rather than deleting records

## Troubleshooting

### Comments are not being filtered

1. Check if filtering is enabled:
   ```bash
   curl http://localhost:8080/api/comment-filter/settings
   ```

2. Verify the mode (whitelist vs blacklist)

3. Check if the user is in the allowed list:
   ```bash
   curl http://localhost:8080/api/comment-filter/commenters | grep username
   ```

### Auto-add is not working

1. Verify auto_add_commenters is enabled in settings
2. Check webhook logs for any errors
3. Ensure database connection is working

### Auto-reply is not being sent

1. Verify auto_reply_enabled is true
2. Check that the message template contains `{username}`
3. Currently, auto-reply requires GitHub App credentials (implementation pending)

## Future Enhancements

- [ ] Complete GitHub API integration for auto-reply comments
- [ ] Web UI for managing commenters in the dashboard
- [ ] Import/export commenter lists
- [ ] Bulk operations (add/remove multiple users)
- [ ] Email notifications when users are added
- [ ] Integration with GitHub teams and organizations
- [ ] Comment filtering rules based on patterns or keywords
