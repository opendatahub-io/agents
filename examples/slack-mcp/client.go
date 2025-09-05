package main

import (
	"context"
	"log"
	"os"

	"github.com/openai/openai-go"
	"github.com/openai/openai-go/option"
	"github.com/openai/openai-go/responses"
)

func main() {
	model := "vllm/Qwen/Qwen3-0.6B"
	token := os.Getenv("SLACK_MCP_TOKEN")
	// Use OpenAI directly instead of Llama Stack
	client := openai.NewClient(
		option.WithBaseURL("http://127.0.0.1:8321/v1/openai/v1/"),
	)

	ctx := context.TODO()
	params := responses.ResponseNewParams{
		Model: model,
		Tools: []responses.ToolUnionParam{
			{
				OfMcp: &responses.ToolMcpParam{
					ServerLabel: "slack",
					ServerURL:   "http://127.0.0.1:13080/sse",
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
		log.Fatalln(err.Error())
	}
	log.Println(resp.OutputText())
}
