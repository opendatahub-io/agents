#!/usr/bin/env python3

import asyncio
import os
import sys
import traceback
from urllib.parse import urlparse
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp import types

async def test_mcp_server():
    """Test the MCP server directly using the Anthropic MCP library"""
    
    print("🧪 Testing MCP Server with Anthropic MCP Client")
    print("=" * 50)
    
    # Get token from environment or prompt
    token = os.getenv("MCP_TOKEN")
    if not token:
        token = input("Enter your MCP token: ").strip()
    
    server_url = os.getenv("MCP_SERVER_URL")
    if not server_url:
        server_url = input("Enter your MCP server URL: ").strip()

    headers = {"Authorization": f"Bearer {token}"}

    print(f"📍 Connecting to: {server_url}")
    print(f"🔑 Using token: {token[:20]}..." if token else "❌ No token provided")
    print()
    
    # Determine transport type from URL
    parsed_url = urlparse(server_url)
    path = parsed_url.path.lower()
    
    # Auto-detect transport type
    if path.endswith('/sse') or 'sse' in path:
        transport_type = "SSE"
        client_func = sse_client
    elif path.endswith('/mcp') or 'mcp' in path or path.endswith('/http'):
        transport_type = "HTTP"
        client_func = streamablehttp_client
    else:
        # Default to HTTP for unknown endpoints
        transport_type = "HTTP (auto-detected)"
        client_func = streamablehttp_client
    
    print(f"🔍 Detected transport: {transport_type}")
    
    try:
        print(f"1️⃣ Establishing {transport_type} connection...")
        async with client_func(server_url, headers=headers) as streams:
            print(f"✅ {transport_type} connection established")
            
            print("\n2️⃣ Creating MCP client session...")
            async with ClientSession(streams[0], streams[1]) as session:
                print("✅ MCP session created")
                
                print("\n3️⃣ Initializing MCP protocol...")
                init_result = await session.initialize()
                print("✅ MCP protocol initialized")
                print(f"   Server: {init_result.serverInfo.name} v{init_result.serverInfo.version}")
                print(f"   Protocol: {init_result.protocolVersion}")
                
                print("\n4️⃣ Listing available tools...")
                tools_result = await session.list_tools()
                print(f"✅ Found {len(tools_result.tools)} tools:")
                
                if tools_result.tools:
                    for i, tool in enumerate(tools_result.tools, 1):
                        print(f"   {i}. {tool.name}")
                        print(f"      Description: {tool.description}")
                        if hasattr(tool, 'inputSchema') and tool.inputSchema:
                            print(f"      Schema: {tool.inputSchema}")
                        print()
                else:
                    print("   ⚠️  No tools found")
                
                # Try to call a tool if available
                if tools_result.tools:
                    first_tool = tools_result.tools[0]
                    print(f"5️⃣ Testing tool call: {first_tool.name}...")
                    try:
                        call_result = await session.call_tool(
                            name=first_tool.name,
                            arguments={}
                        )
                        print("✅ Tool call successful!")
                        if hasattr(call_result, 'content') and call_result.content:
                            for content in call_result.content:
                                if hasattr(content, 'type') and content.type == 'text' and hasattr(content, 'text'):
                                    print(f"   Result: {content.text}")
                        print()
                    except Exception as e:
                        print(f"❌ Tool call failed: {e}")
                        print(f"   This may indicate an issue with the tool implementation or arguments")
                
                print("🎉 MCP server test completed successfully!")
                return True
                
    except ConnectionRefusedError as e:
        print(f"❌ Connection refused: {e}")
        print(f"   🔧 Possible causes:")
        print(f"      • MCP server is not running")
        print(f"      • Server is not listening on {parsed_url.hostname}:{parsed_url.port or 'default port'}")
        print(f"      • Firewall or network blocking the connection")
        print(f"   💡 Try: Check if server is running with 'netstat -an | grep {parsed_url.port or '80/443'}'")
        return False
    except ConnectionError as e:
        print(f"❌ Connection failed: {e}")
        print(f"   🔧 Possible causes:")
        print(f"      • Wrong transport type (tried {transport_type})")
        print(f"      • Server expects different endpoint path")
        print(f"      • Network connectivity issues")
        print(f"   💡 Try: Verify server URL and transport type")
        return False
    except Exception as e:
        print(f"❌ MCP test failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        
        # Show detailed error information
        if hasattr(e, 'args') and e.args:
            print(f"   Args: {e.args}")
        
        # Show cause and context if available
        if hasattr(e, '__cause__') and e.__cause__:
            print(f"   Caused by: {type(e.__cause__).__name__}: {e.__cause__}")
        
        if hasattr(e, '__context__') and e.__context__:
            print(f"   Context: {type(e.__context__).__name__}: {e.__context__}")
        
        # Show traceback for debugging (limit to last 15 lines to keep output manageable)
        print(f"   📋 Full traceback:")
        tb_lines = traceback.format_exception(type(e), e, e.__traceback__)
        all_lines = []
        for line in tb_lines:
            for sub_line in line.rstrip().split('\n'):
                if sub_line.strip():
                    all_lines.append(f"      {sub_line}")
        
        # Show full traceback if it's short, or last 15 lines if too long
        if len(all_lines) <= 20:
            for line in all_lines:
                print(line)
        else:
            print(f"      ... (showing last 15 lines of {len(all_lines)} total lines)")
            for line in all_lines[-15:]:
                print(line)
        
        print()  # Empty line for readability
        
        # Provide specific guidance based on error type
        error_name = type(e).__name__
        if "ReadError" in error_name or "httpcore" in str(e).lower():
            print(f"   🔧 Network/HTTP error details:")
            print(f"      • Server may have closed connection unexpectedly")
            print(f"      • Transport mismatch (server expects different protocol)")
            print(f"      • Server may not support {transport_type} transport")
            print(f"   💡 Try: Use different endpoint (e.g., /mcp instead of /sse)")
        elif "401" in str(e) or "Unauthorized" in str(e):
            print(f"   🔧 Authentication error:")
            print(f"      • Invalid or missing token")
            print(f"      • Token may have expired")
            print(f"      • Server expects different authentication format")
            print(f"   💡 Try: Verify your MCP_TOKEN is correct and valid")
        elif "ExceptionGroup" in error_name:
            print(f"   🔧 Multiple errors occurred:")
            try:
                # Try to access exceptions attribute (available in ExceptionGroup)
                exceptions = getattr(e, 'exceptions', [])
                for i, exc in enumerate(exceptions, 1):
                    print(f"      {i}. {type(exc).__name__}: {exc}")
                    
                    # Show more detailed error information
                    if hasattr(exc, 'args') and exc.args:
                        print(f"         Args: {exc.args}")
                    
                    # For specific exception types, show additional details
                    if hasattr(exc, '__cause__') and exc.__cause__:
                        print(f"         Caused by: {type(exc.__cause__).__name__}: {exc.__cause__}")
                    
                    if hasattr(exc, '__context__') and exc.__context__:
                        print(f"         Context: {type(exc.__context__).__name__}: {exc.__context__}")
                    
                    # Show attributes that might contain useful info
                    if hasattr(exc, 'response'):
                        print(f"         Response: {exc.response}")
                    if hasattr(exc, 'request'):
                        print(f"         Request: {exc.request}")
                    if hasattr(exc, 'status_code'):
                        print(f"         Status Code: {exc.status_code}")
                    
                    print()  # Empty line for readability
            except AttributeError:
                print(f"      Unable to extract individual exceptions")
            except Exception as nested_exc:
                print(f"      Error while processing exceptions: {nested_exc}")
        else:
            print(f"   🔧 General troubleshooting:")
            print(f"      • Check server logs for errors")
            print(f"      • Verify MCP server is properly configured")
            print(f"      • Ensure all required dependencies are installed")
        
        return False

if __name__ == "__main__":
    print("Testing MCP server with Anthropic MCP client library...\n")
    
    try:
        success = asyncio.run(test_mcp_server())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\n📦 Install with: pip install mcp")
        sys.exit(1)
