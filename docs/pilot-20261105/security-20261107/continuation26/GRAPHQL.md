# GraphQL — bounded live evidence

Test project fsvrsvqfknogwmhccera only. Catalog inspection found pg_graphql extension absent; graphql_public.graphql exists as a placeholder returning “pg_graphql extension is not enabled.” Public HTTP POST with harmless { __typename } returned that same error (HTTP200), not a schema. See graphql-definition.json and graphql-http.json. No introspection or load test performed.

V4.3.1 remains incomplete because its official wording also covers data-layer expression cost, not just GraphQL. V4.3.2 explicitly concerns production introspection; production was not inspected under this test-only scope. Test-project disabled GraphQL is bounded evidence, not blanket production acceptance or an inferred N/A. Official reference: https://supabase.com/docs/guides/graphql/security .
