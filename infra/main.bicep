@description('Prefix for resource names')
param namePrefix string = 'newsagent'

@description('Location for resources')
param location string = resourceGroup().location

// NOTE: This is an MVP placeholder.
// In Day 2 you’ll flesh this out to provision:
// - Static Web App
// - Container Apps env + Container App (API)
// - Function App (timer)
// - Cosmos DB
// - Key Vault
// - (Optional) Communication Services Email
// - (Optional) Azure AI Foundry Project + Grounding connection

output info string = 'Fill infra/main.bicep during Day 2'
