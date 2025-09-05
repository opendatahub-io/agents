#!/bin/bash

echo "=== Testing Slack OAuth Token for MCP Server ==="
echo "Required scopes: channels:read, groups:read, mpim:read, im:read, users:read"
echo ""

if [ -z "$SLACK_MCP_TOKEN" ]; then
    echo "Enter your Slack MCP Token: "
    read -s SLACK_MCP_TOKEN
fi

SLACK_TOKEN=$SLACK_MCP_TOKEN

echo ""
echo "1. Testing token validity..."
auth_response=$(curl -s -H "Authorization: Bearer $SLACK_TOKEN" \
    "https://slack.com/api/auth.test")

echo "Auth test response:"
echo $auth_response | jq '{ok: .ok, user: .user, team: .team}' 2>/dev/null || echo $auth_response

echo ""
echo "2. Testing MCP Server's exact API call (all conversation types)..."
mcp_response=$(curl -s -H "Authorization: Bearer $SLACK_TOKEN" \
    "https://slack.com/api/conversations.list?types=public_channel,private_channel,mpim,im")

echo "MCP Server API response:"
echo $mcp_response | jq '{ok: .ok, error: .error, count: (.channels | length // 0)}' 2>/dev/null || echo $mcp_response

echo ""
echo "3. Testing individual conversation types:"

echo "   3a. Public channels (scope: channels:read):"
public_response=$(curl -s -H "Authorization: Bearer $SLACK_TOKEN" \
    "https://slack.com/api/conversations.list?types=public_channel")
echo $public_response | jq '{ok: .ok, error: .error, count: (.channels | length // 0)}' 2>/dev/null

echo "   3b. Private channels (scope: groups:read):"
private_response=$(curl -s -H "Authorization: Bearer $SLACK_TOKEN" \
    "https://slack.com/api/conversations.list?types=private_channel")
echo $private_response | jq '{ok: .ok, error: .error, count: (.channels | length // 0)}' 2>/dev/null

echo "   3c. Group DMs (scope: mpim:read):"
mpim_response=$(curl -s -H "Authorization: Bearer $SLACK_TOKEN" \
    "https://slack.com/api/conversations.list?types=mpim")
echo $mpim_response | jq '{ok: .ok, error: .error, count: (.channels | length // 0)}' 2>/dev/null

echo "   3d. Direct messages (scope: im:read):"
im_response=$(curl -s -H "Authorization: Bearer $SLACK_TOKEN" \
    "https://slack.com/api/conversations.list?types=im")
echo $im_response | jq '{ok: .ok, error: .error, count: (.channels | length // 0)}' 2>/dev/null

echo ""
echo "4. Testing user list access (scope: users:read)..."
users_response=$(curl -s -H "Authorization: Bearer $SLACK_TOKEN" \
    "https://slack.com/api/users.list")
echo $users_response | jq '{ok: .ok, error: .error, count: (.members | length // 0)}' 2>/dev/null

echo ""
echo "=== SUMMARY FOR MCP SERVER ==="

if echo $auth_response | grep -q '"ok":true'; then
    echo "✅ OAuth token is valid"
else
    echo "❌ OAuth token is invalid or expired"
    exit 1
fi

# Test the exact call MCP server makes
if echo $mcp_response | grep -q '"ok":true'; then
    echo "✅ MCP Server API call will succeed - all required scopes present"
    echo "   Channels accessible: $(echo $mcp_response | jq '.channels | length // 0' 2>/dev/null || echo 'unknown')"
else
    echo "❌ MCP Server API call will FAIL - missing scopes detected"
    echo "   Error: $(echo $mcp_response | jq -r '.error // "unknown"' 2>/dev/null)"
fi

# Individual scope checks
echo ""
echo "Individual scope verification:"

if echo $public_response | grep -q '"ok":true'; then
    echo "✅ channels:read - Can access public channels"
else
    echo "❌ channels:read - MISSING scope for public channels"
fi

if echo $private_response | grep -q '"ok":true'; then
    echo "✅ groups:read - Can access private channels"
else
    echo "❌ groups:read - MISSING scope for private channels"
fi

if echo $mpim_response | grep -q '"ok":true'; then
    echo "✅ mpim:read - Can access group DMs"
else
    echo "❌ mpim:read - MISSING scope for group DMs"
fi

if echo $im_response | grep -q '"ok":true'; then
    echo "✅ im:read - Can access direct messages"
else
    echo "❌ im:read - MISSING scope for direct messages"
fi

if echo $users_response | grep -q '"ok":true'; then
    echo "✅ users:read - Can access user list"
else
    echo "❌ users:read - MISSING scope for user list"
fi

echo ""
if echo $mcp_response | grep -q '"ok":true'; then
    echo "🎉 Your token has all required scopes! The MCP server should work."
else
    echo "⚠️  Add missing scopes to your Slack app, reinstall, and generate a new token."
    echo "   Required scopes: channels:read, groups:read, mpim:read, im:read, users:read"
fi
