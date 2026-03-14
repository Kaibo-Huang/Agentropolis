Get started with Claude Code and Neon Postgres MCP Server
Interact with Neon APIs using Claude Code through natural language

Imagine adjusting your database schema simply by describing the change in plain English. This is possible by combining Claude Code with the Neon MCP Server.

This guide demonstrates how to use Claude Code's command-line interface and Neon's MCP server to perform database migrations in your Neon project.

Neon MCP Server Security Considerations
The Neon MCP Server grants powerful database management capabilities through natural language requests. Always review and authorize actions requested by the LLM before execution. Ensure that only authorized users and applications have access to the Neon MCP Server.

The Neon MCP Server is intended for local development and IDE integrations only. We do not recommend using the Neon MCP Server in production environments. It can execute powerful operations that may lead to accidental or unauthorized changes.

For more information, see MCP security guidance.

Key components
Let's break down the key components in this setup:

Claude Code: Claude Code is Anthropic's official CLI tool that supports Model Context Protocol (MCP) for interfacing with external tools (APIs, databases, etc.)

Neon MCP Server: Neon's MCP server acts as a bridge between MCP clients like Claude Code and Neon's API, letting you work with Neon databases using natural language commands.

Model Context Protocol (MCP): MCP is a lightweight communication standard that allows Claude Code and Neon MCP Server to work together.

Setting up Neon MCP Server in Claude Code
You have three options for connecting Claude Code to the Neon MCP Server:

Quick Setup (Recommended): Use the neonctl init command to automatically configure Claude Code with OAuth authentication and API key creation.

Remote MCP Server (OAuth): Manually connect to Neon's managed MCP server using OAuth for authentication. This method is more convenient as it eliminates the need to manage API keys in Claude Code. Additionally, you will automatically receive the latest features and improvements as soon as they are released.

Local MCP Server: Run the Neon MCP server locally on your machine, authenticating with a Neon API key.

Prerequisites
Before you begin, ensure you have the following:

Claude Code: Ensure you have Claude Code installed. Visit docs.anthropic.com/en/docs/claude-code for installation instructions.

Neon API Key (for Local MCP server): After signing up, get your Neon API Key from the Neon console. This API key is needed to authenticate your application with Neon. For instructions, see Manage API keys.

Neon API Key Security
Keep your Neon API key secure, and never share it publicly. It provides access to your Neon projects.

Node.js (>= v18) and npm: Ensure Node.js (version 18 or later) and npm are installed. Download them from nodejs.org.

Quick Setup (Recommended)
The fastest way to get started is with the neonctl init command, which automates OAuth authentication, API key creation, and Claude Code configuration:

npx neonctl@latest init
This command authenticates via OAuth, creates an API key, and configures Claude Code to connect to Neon's remote MCP server. Once complete, ask your AI assistant "Get started with Neon".

Option 1: Setting up the Remote Hosted Neon MCP Server (OAuth)
note
By default, the Remote MCP Server connects to your personal Neon account. To connect to an organization's account, you must authenticate with an API key. For more information, see API key-based authentication.

This method uses Neon's managed server and OAuth authentication.

Open your terminal.
Add the Neon MCP server to Claude Code with the following command:
claude mcp add --transport http neon https://mcp.neon.tech/mcp
Start a new session of claude to trigger the OAuth authentication flow:
claude

You can also trigger authentication with /mcp within Claude Code.
tip
If you prefer to authenticate using a Neon API key, provide the Authorization header to the mcp add command:

claude mcp add --transport http neon https://mcp.neon.tech/mcp \
    --header "Authorization: Bearer <YOUR_NEON_API_KEY>"
Replace <YOUR_NEON_API_KEY> with your actual Neon API key which you obtained from the prerequisites section.

Option 2: Setting up the Local Neon MCP Server
This method runs the Neon MCP server locally on your machine, using a Neon API key for authentication.

Open your terminal.

Add the Neon MCP server to Claude Code with the following command, replacing <YOUR_NEON_API_KEY> with your actual Neon API key:

claude mcp add neon -- npx -y @neondatabase/mcp-server-neon start "<YOUR_NEON_API_KEY>"
Replace <YOUR_NEON_API_KEY> with your actual Neon API key which you obtained from the prerequisites section.

Start a new Claude Code session with the claude command and start using the Neon MCP server:

claude
You've now configured the Neon MCP Server in Claude Code and can manage your Neon Postgres databases using AI.

Verification
Now that you have the Neon MCP server set up either remotely or locally, you can verify the connection and test the available tools.

Start Claude Code:

claude
Type /mcp to see the available MCP servers and tools.

Try out a Neon MCP Server tool by typing a query like List my Neon projects to see your projects and verify the connection.

Supported actions (tools)
The Neon MCP Server provides the following actions, which are exposed as "tools" to MCP clients. You can use these tools to interact with your Neon projects and databases using natural language commands.

Project management:

list_projects: Lists the first 10 Neon projects in your account, providing a summary of each project. If you can't find a specific project, increase the limit by passing a higher value to the limit parameter.
list_shared_projects: Lists Neon projects shared with the current user. Supports a search parameter and limiting the number of projects returned (default: 10).
describe_project: Fetches detailed information about a specific Neon project, including its ID, name, and associated branches and databases.
create_project: Creates a new Neon project in your Neon account. A project acts as a container for branches, databases, roles, and computes.
delete_project: Deletes an existing Neon project and all its associated resources.
list_organizations: Lists all organizations that the current user has access to. Optionally filter by organization name or ID using the search parameter.
Branch management:

create_branch: Creates a new branch within a specified Neon project. Leverages Neon's branching feature for development, testing, or migrations.
delete_branch: Deletes an existing branch from a Neon project.
describe_branch: Retrieves details about a specific branch, such as its name, ID, and parent branch.
list_branch_computes: Lists compute endpoints for a project or specific branch, including compute ID, type, size, last active time, and autoscaling information.
compare_database_schema: Shows the schema diff between the child branch and its parent.
reset_from_parent: Resets the current branch to its parent's state, discarding local changes. Automatically preserves to backup if branch has children, or optionally preserve on request with a custom name.
SQL query execution:

get_connection_string: Returns your database connection string.
run_sql: Executes a single SQL query against a specified Neon database. Supports both read and write operations.
run_sql_transaction: Executes a series of SQL queries within a single transaction against a Neon database.
get_database_tables: Lists all tables within a specified Neon database.
describe_table_schema: Retrieves the schema definition of a specific table, detailing columns, data types, and constraints.
Database migrations (schema changes):

prepare_database_migration: Initiates a database migration process. Critically, it creates a temporary branch to apply and test the migration safely before affecting the main branch.
complete_database_migration: Finalizes and applies a prepared database migration to the main branch. This action merges changes from the temporary migration branch and cleans up temporary resources.
Query performance optimization:

list_slow_queries: Identifies performance bottlenecks by finding the slowest queries in a database. Requires the pg_stat_statements extension.
explain_sql_statement: Provides detailed execution plans for SQL queries to help identify performance bottlenecks.
prepare_query_tuning: Analyzes query performance and suggests optimizations, like index creation. Creates a temporary branch for safely testing these optimizations.
complete_query_tuning: Finalizes query tuning by either applying optimizations to the main branch or discarding them. Cleans up the temporary tuning branch.
Neon Auth:

provision_neon_auth: Provisions Neon Auth for a Neon project. It allows developers to easily set up authentication infrastructure by creating an integration with an Auth provider.
Neon Data API:

provision_neon_data_api: Provisions the Neon Data API for a branch, enabling HTTP-based Data API access with optional JWT authentication.
Search and discovery:

search: Searches across organizations, projects, and branches matching a query. Returns IDs, titles, and direct links to the Neon Console.
fetch: Fetches detailed information about a specific organization, project, or branch using an ID (typically from the search tool).
Documentation and resources:

list_docs_resources: Lists all available Neon documentation pages by fetching the docs index. Returns page URLs and titles that can be fetched individually using the get_doc_resource tool.
get_doc_resource: Fetches a specific Neon documentation page as markdown content. Use the list_docs_resources tool first to discover available page slugs, then pass the slug to this tool.
These actions enable any MCP client like Claude Code to interact with various functionalities of the Neon platform via the Neon API. Certain tools, especially database migration ones, are tailored for AI agent and LLM usage, leveraging Neon's branching for safe preview and commit.

Development Workflow: Adding a Column with Claude Code and Neon MCP
Let's walk through a typical development scenario: Quickly adding a column for prototyping using natural language within Claude Code. The following chat log demonstrates a real interaction with Claude Code and the Neon MCP server.

Scenario: During development, you decide to track timestamps for entries in your playing_with_neon table. You want to quickly add a created_at column.

Security Reminder
For your security, review the tool's purpose before permitting the operation to proceed. Remember that LLMs can sometimes produce unexpected results, so careful monitoring is always recommended.

Here's the conversation log between the user and Claude Code:

User: In my neon project id: round-salad-44063611 list all the tables
Claude Code: I'll help you list all the tables in your Neon project. I'll use the default database name 'neondb' since none was specified.
> Called MCP Tool (get_database_tables)
> I found one table in your database:
> playing_with_neon (in the public schema)
> Would you like to see more details about this table's structure or perform any other operations with it?
User: Can you show me first 5 rows?
Claude Code: I'll query the first 5 rows from the playing_with_neon table.
> Called MCP Tool (run_sql)
> Here are the first 5 rows from the table. The table has three columns:
> id (sequential numbers)
> name (string values)
> value (decimal numbers)
> Would you like to perform any other operations with this data?
User: can you add a created_at column?
Claude Code: I'll help you add a created_at column to the playing_with_neon table. I'll set it up with a timestamp data type and set it to automatically record the creation time of new rows.
> Called MCP Tool (prepare_database_migration)
> Let me verify the change in the temporary branch to make sure it was applied correctly.
> Called MCP Tool (run_sql)
> I've added the created_at column to the playing_with_neon table in a temporary branch. Would you like to commit this migration to the production branch?
> Migration Details:
> Migration ID: a65babcd-d1cc-401f-89b5-762570570102
> Temporary Branch Name: br-silent-cherry-a1eqrl6i
> Temporary Branch ID: br-silent-cherry-a1eqrl6i
> Migration Result: Success
> Please let me know if you'd like to proceed with applying this change to the production branch.
User: yeah do it
Claude Code: I'll complete the migration and apply the changes to the production branch.
> Called MCP Tool (complete_database_migration)
> The migration has been successfully completed! The created_at column has been added to your table in the production branch, and the temporary branch has been cleaned up.
Key takeaways:

Natural language interaction: You can use simple, conversational English to interact with your database.
Step-by-step guidance: Claude Code confirms each step and provides details like branch names and migration IDs.
MCP Tools in Action: The underlying MCP tools (get_database_tables, run_sql, prepare_database_migration, complete_database_migration) illustrate the automated process.
Branching for safety: The agent automatically creates a temporary branch for schema changes. The user will be prompted to confirm the migration before applying it to the production branch.
You can verify the changes in your Neon Console or by querying the database directly.

note
While the Neon MCP server allows you to utilize all of Neon's functionalities, you can also use a generic Postgres MCP server to connect to Neon.

Bonus: Creating a project and branch
Beyond schema changes, you can also manage your Neon projects and branches directly within Claude Code using natural language commands. This can be useful for quickly setting up a new development or test environment.

Creating a new project
Let's say you want to create a new Neon project named "my-new-project". You can simply tell Claude Code:

User: Create a Neon project named "my-new-project"
Claude Code: I'll help you create a new Neon project with the specified name.
> Called MCP Tool (create_project)
> Great! I've created a new Neon project for you with the name "my-new-project". Here are the important details:
> Project ID: orange-dawn-33739962
> Default branch: main
> Default database: neondb
> The project is ready to use. You can start creating tables and working with your database right away.
Claude Code will then use the create_project MCP tool to initiate the project creation. It will provide you with a project ID and name.

Creating a New Branch
Once you have a project, you can easily create new branches for development or experimentation. For example, to create a branch named "feature-x" in your "my-new-project" project:

User: Create a branch named "feature-x"
Claude Code: Perfect! I've created a new branch named "feature-x". Here are the details:
> Branch ID: br-cold-mountain-a523ka2w
> Branch name: feature-x
> Parent branch ID: br-odd-pine-a5y53krm
> The branch has been created successfully and is ready for use.
Claude Code will use the create_branch MCP tool to create the branch and provide you with the branch name and ID. Notice how we don't need to specify the project ID, as Claude Code remembers the active project context.

Conclusion
Claude Code combined with the Neon MCP Server, whether using the Remote Hosted option or the Local Server setup, lets you use natural language to interact with your database and take advantage of Neon's branching capabilities for fast iteration. This approach is ideal for quickly testing database ideas and making schema changes during development.

Resources
MCP Protocol
Claude Code Documentation
Neon Docs
Neon API Keys
Neon MCP server GitHub
Need help?
Join our Discord Server to ask questions or see what others are doing with Neon. For paid plan support options, see Support.