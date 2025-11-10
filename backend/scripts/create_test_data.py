#!/usr/bin/env python3
"""
Create production-like test data for DeepAgents Platform.

SECURITY WARNING:
    This script creates test users with default passwords.
    This is for DEVELOPMENT/TESTING ONLY.
    Never use these credentials in production!
"""
import asyncio
import httpx
from typing import Optional

BASE_URL = "http://localhost:8000/api/v1"

class DataCreator:
    def __init__(self):
        self.token: Optional[str] = None
        self.user_id: Optional[int] = None

    async def register_and_login(self, username: str, email: str, password: str) -> bool:
        """Register and login user, return True if successful"""
        async with httpx.AsyncClient(follow_redirects=True) as client:
            # Try to register (returns token automatically)
            try:
                response = await client.post(
                    f"{BASE_URL}/auth/register",
                    json={
                        "username": username,
                        "email": email,
                        "password": password
                    }
                )
                if response.status_code in [200, 201]:
                    data = response.json()
                    self.token = data["access_token"]
                    print(f"✓ Registered and logged in: {username}")

                    # Get user profile
                    response = await client.get(
                        f"{BASE_URL}/users/me",
                        headers={"Authorization": f"Bearer {self.token}"}
                    )
                    if response.status_code == 200:
                        self.user_id = response.json()["id"]
                        print(f"✓ User ID: {self.user_id}")
                    return True
                elif response.status_code == 400:
                    print(f"⚠ User {username} already exists, trying to login...")
                else:
                    print(f"✗ Registration failed: {response.status_code} {response.text}")
            except Exception as e:
                print(f"✗ Registration error: {e}")

            # If registration failed, try to login
            try:
                response = await client.post(
                    f"{BASE_URL}/auth/login",
                    json={
                        "username": username,
                        "password": password
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    self.token = data["access_token"]
                    print(f"✓ Logged in as: {username}")

                    # Get user profile
                    response = await client.get(
                        f"{BASE_URL}/users/me",
                        headers={"Authorization": f"Bearer {self.token}"}
                    )
                    if response.status_code == 200:
                        self.user_id = response.json()["id"]
                        print(f"✓ User ID: {self.user_id}")
                    return True
                else:
                    print(f"✗ Login failed: {response.status_code} {response.text}")
                    return False
            except Exception as e:
                print(f"✗ Login error: {e}")
                return False

    async def create_agent(self, name: str, model_provider: str, model_name: str,
                          system_prompt: str, planning: bool = False,
                          filesystem: bool = False, temperature: float = 0.7) -> Optional[int]:
        """Create an agent and return its ID"""
        if not self.token:
            print("✗ Not authenticated")
            return None

        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{BASE_URL}/agents/",
                    headers={"Authorization": f"Bearer {self.token}"},
                    json={
                        "name": name,
                        "model_provider": model_provider,
                        "model_name": model_name,
                        "system_prompt": system_prompt,
                        "temperature": temperature,
                        "max_tokens": 4096,
                        "planning_enabled": planning,
                        "filesystem_enabled": filesystem,
                        "is_active": True
                    }
                )
                if response.status_code in [200, 201]:
                    agent_id = response.json()["id"]
                    print(f"✓ Created agent: {name} (ID: {agent_id})")
                    return agent_id
                else:
                    try:
                        error_detail = response.json()
                        print(f"✗ Failed to create agent {name}: {response.status_code} - {error_detail}")
                    except:
                        print(f"✗ Failed to create agent {name}: {response.status_code} - {response.text}")
                    return None
            except Exception as e:
                print(f"✗ Error creating agent {name}: {e}")
                import traceback
                traceback.print_exc()
                return None

    async def create_tool(self, name: str, description: str,
                          tool_type: str = "custom") -> Optional[int]:
        """Create a tool and return its ID"""
        if not self.token:
            print("✗ Not authenticated")
            return None

        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{BASE_URL}/tools/",
                    headers={"Authorization": f"Bearer {self.token}"},
                    json={
                        "name": name,
                        "description": description,
                        "tool_type": tool_type,
                        "config": {}
                    }
                )
                if response.status_code in [200, 201]:
                    tool_id = response.json()["id"]
                    print(f"✓ Created tool: {name} (ID: {tool_id})")
                    return tool_id
                else:
                    print(f"✗ Failed to create tool {name}: {response.text}")
                    return None
            except Exception as e:
                print(f"✗ Error creating tool {name}: {e}")
                return None

    async def create_template(self, name: str, description: str, category: str,
                             model_provider: str, model_name: str,
                             system_prompt: str) -> Optional[int]:
        """Create a template and return its ID"""
        if not self.token:
            print("✗ Not authenticated")
            return None

        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{BASE_URL}/templates/",
                    headers={"Authorization": f"Bearer {self.token}"},
                    json={
                        "name": name,
                        "description": description,
                        "category": category,
                        "config_template": {
                            "model_provider": model_provider,
                            "model_name": model_name,
                            "system_prompt": system_prompt,
                            "temperature": 0.7,
                            "max_tokens": 4096,
                            "planning_enabled": False,
                            "filesystem_enabled": False
                        }
                    }
                )
                if response.status_code in [200, 201]:
                    template_id = response.json()["id"]
                    print(f"✓ Created template: {name} (ID: {template_id})")
                    return template_id
                else:
                    print(f"✗ Failed to create template {name}: {response.text}")
                    return None
            except Exception as e:
                print(f"✗ Error creating template {name}: {e}")
                return None


async def main():
    print("=" * 60)
    print("Creating Production-Like Test Data")
    print("=" * 60)

    creator = DataCreator()

    # 1. Create and login test users
    print("\n[1/4] Creating test users...")
    success = await creator.register_and_login("testadmin", "admin@test.com", "Admin123!")
    if not success:
        print("Failed to create admin user, exiting...")
        return

    # Create regular user
    regular_creator = DataCreator()
    await regular_creator.register_and_login("testuser", "user@test.com", "User123!")

    # 2. Create diverse agents
    print("\n[2/4] Creating test agents...")

    agents = [
        {
            "name": "Research Assistant Pro",
            "model_provider": "anthropic",
            "model_name": "claude-3-5-sonnet-20241022",
            "system_prompt": "You are an expert research assistant. Help users conduct thorough research by breaking down complex topics, finding relevant information, and synthesizing insights. Use planning to organize your research process.",
            "planning": True,
            "filesystem": False,
            "temperature": 0.7
        },
        {
            "name": "Code Reviewer",
            "model_provider": "anthropic",
            "model_name": "claude-3-5-sonnet-20241022",
            "system_prompt": "You are a senior code reviewer. Analyze code for bugs, security issues, performance problems, and style violations. Provide constructive feedback and improvement suggestions.",
            "planning": True,
            "filesystem": True,
            "temperature": 0.3
        },
        {
            "name": "Creative Writer",
            "model_provider": "anthropic",
            "model_name": "claude-3-opus-20240229",
            "system_prompt": "You are a creative writing assistant. Help users craft engaging stories, articles, and content. Focus on narrative flow, character development, and compelling prose.",
            "planning": False,
            "filesystem": False,
            "temperature": 0.9
        },
        {
            "name": "Data Analyst",
            "model_provider": "openai",
            "model_name": "gpt-4-turbo-preview",
            "system_prompt": "You are a data analyst expert. Analyze datasets, identify patterns, create visualizations, and provide actionable insights. Use systematic planning for complex analyses.",
            "planning": True,
            "filesystem": True,
            "temperature": 0.5
        },
        {
            "name": "Technical Writer",
            "model_provider": "openai",
            "model_name": "gpt-4",
            "system_prompt": "You are a technical documentation specialist. Create clear, comprehensive documentation for APIs, software, and technical processes. Focus on clarity and completeness.",
            "planning": True,
            "filesystem": True,
            "temperature": 0.4
        },
        {
            "name": "Customer Support Bot",
            "model_provider": "openai",
            "model_name": "gpt-3.5-turbo",
            "system_prompt": "You are a friendly customer support agent. Help customers with their questions, troubleshoot issues, and provide excellent service. Be empathetic and solution-oriented.",
            "planning": False,
            "filesystem": False,
            "temperature": 0.6
        },
        {
            "name": "Product Manager",
            "model_provider": "anthropic",
            "model_name": "claude-3-5-sonnet-20241022",
            "system_prompt": "You are an experienced product manager. Help with product strategy, roadmap planning, feature prioritization, and stakeholder communication. Use structured planning.",
            "planning": True,
            "filesystem": False,
            "temperature": 0.7
        },
        {
            "name": "DevOps Engineer",
            "model_provider": "anthropic",
            "model_name": "claude-3-5-sonnet-20241022",
            "system_prompt": "You are a DevOps engineer. Help with infrastructure automation, CI/CD pipelines, deployment strategies, and system reliability. Use filesystem tools to work with configs.",
            "planning": True,
            "filesystem": True,
            "temperature": 0.5
        }
    ]

    agent_ids = []
    for agent_data in agents:
        agent_id = await creator.create_agent(**agent_data)
        if agent_id:
            agent_ids.append(agent_id)

    # 3. Create custom tools
    print("\n[3/4] Creating custom tools...")

    tools = [
        {
            "name": "web_search",
            "description": "Search the web for current information using a search engine API",
            "tool_type": "api"
        },
        {
            "name": "calculator",
            "description": "Perform complex mathematical calculations and equations",
            "tool_type": "builtin"
        },
        {
            "name": "database_query",
            "description": "Query databases using SQL for data retrieval and analysis",
            "tool_type": "custom"
        },
        {
            "name": "code_executor",
            "description": "Execute code in a sandboxed environment and return results",
            "tool_type": "custom"
        },
        {
            "name": "api_caller",
            "description": "Make HTTP requests to external APIs with authentication",
            "tool_type": "api"
        }
    ]

    tool_ids = []
    for tool_data in tools:
        tool_id = await creator.create_tool(**tool_data)
        if tool_id:
            tool_ids.append(tool_id)

    # 4. Create templates
    print("\n[4/4] Creating agent templates...")

    templates = [
        {
            "name": "Research Agent Template",
            "description": "Pre-configured research agent with planning capabilities",
            "category": "research",
            "model_provider": "anthropic",
            "model_name": "claude-3-5-sonnet-20241022",
            "system_prompt": "You are a research assistant. Use planning to organize research tasks systematically."
        },
        {
            "name": "Code Review Template",
            "description": "Agent specialized in code review with filesystem access",
            "category": "code_review",
            "model_provider": "anthropic",
            "model_name": "claude-3-5-sonnet-20241022",
            "system_prompt": "You are a code reviewer. Analyze code quality, security, and best practices."
        },
        {
            "name": "Content Writer Template",
            "description": "Creative writing agent for articles and stories",
            "category": "content_writing",
            "model_provider": "anthropic",
            "model_name": "claude-3-opus-20240229",
            "system_prompt": "You are a creative writer. Craft engaging and compelling content."
        },
        {
            "name": "Data Analysis Template",
            "description": "Agent for data analysis and visualization",
            "category": "data_analysis",
            "model_provider": "openai",
            "model_name": "gpt-4-turbo-preview",
            "system_prompt": "You are a data analyst. Analyze data and provide insights."
        },
        {
            "name": "Documentation Template",
            "description": "Technical documentation specialist",
            "category": "documentation",
            "model_provider": "openai",
            "model_name": "gpt-4",
            "system_prompt": "You are a technical writer. Create clear documentation."
        },
        {
            "name": "Support Bot Template",
            "description": "Customer support agent template",
            "category": "customer_support",
            "model_provider": "openai",
            "model_name": "gpt-3.5-turbo",
            "system_prompt": "You are a support agent. Help customers with their issues."
        }
    ]

    template_ids = []
    for template_data in templates:
        template_id = await creator.create_template(**template_data)
        if template_id:
            template_ids.append(template_id)

    # Summary
    print("\n" + "=" * 60)
    print("Test Data Creation Complete!")
    print("=" * 60)
    print(f"✓ Users created: 2 (testadmin, testuser)")
    print(f"✓ Agents created: {len(agent_ids)}")
    print(f"✓ Tools created: {len(tool_ids)}")
    print(f"✓ Templates created: {len(template_ids)}")
    print("\nYou can now:")
    print("  - Login as: testadmin / Admin123!")
    print("  - Login as: testuser / User123!")
    print("  - Access API docs: http://localhost:8000/docs")
    print("  - Access Frontend: http://localhost:3000")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
