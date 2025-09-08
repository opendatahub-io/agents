package main

import (
	"context"
	"log"
	"os"

	"github.com/openai/openai-go/v2"
	"github.com/openai/openai-go/v2/option"
	"github.com/openai/openai-go/v2/responses"
)

func main() {
	log.Println("=== Testing Slack MCP integration with different models ===")

	queryModel("OpenAI GPT-4o-mini", "openai/gpt-4o-mini")
	log.Println() // Add spacing between outputs
	queryModel("Qwen 3-0.6B", "vllm/Qwen/Qwen3-0.6B")
}

// queryModel sends a query to the specified model and prints the response with clear labeling
func queryModel(displayName, modelName string) {
	log.Printf("--- Querying %s (%s) ---", displayName, modelName)

	token := os.Getenv("SLACK_MCP_TOKEN")
	if token == "" {
		log.Fatalf("SLACK_MCP_TOKEN environment variable is required")
	}

	client := openai.NewClient(
		option.WithBaseURL("http://127.0.0.1:8321/v1/openai/v1/"),
	)

	ctx := context.TODO()
	params := responses.ResponseNewParams{
		Model: modelName,
		Tools: []responses.ToolUnionParam{
			{
				OfMcp: &responses.ToolMcpParam{
					ServerLabel: "slack",
					ServerURL:   openai.String("http://127.0.0.1:13080/sse"),
					Headers: map[string]string{
						"Authorization": "Bearer " + token,
					},
				},
			},
		},
		Input: responses.ResponseNewParamsInputUnion{
			OfString: openai.String("Using the slack mcp tool provided, list all the channels you are in."),
		},
	}

	resp, err := client.Responses.New(ctx, params)
	if err != nil {
		log.Fatalf("Error querying %s: %v", displayName, err)
	}

	log.Printf("%s Response:\n%s", displayName, resp.OutputText())
}
