package main

import (
	"context"
	"log"
	"os"
	"strings"

	"github.com/openai/openai-go"
	"github.com/openai/openai-go/responses"
)

func main() {
	token := strings.TrimSpace(os.Getenv("KUBE_TOKEN"))
	if token == "" {
		log.Fatalln("Please set KUBE_TOKEN in env")
	}
	model := "Qwen/Qwen3-0.6B"
	log.Printf("Using model %s", model)
	client := openai.NewClient()
	ctx := context.TODO()

	params := responses.ResponseNewParams{
		Model: model,
		Tools: []responses.ToolUnionParam{
			{
				OfMcp: &responses.ToolMcpParam{
					ServerLabel: "kubernetes",
					ServerURL:   "http://localhost:8080/sse",
					Headers: map[string]string{
						"Authorization": "Bearer " + token,
					},
				},
			},
		},
		Input: responses.ResponseNewParamsInputUnion{
			OfString: openai.String("Using the tool provided, list all pods in the demo-auth namespace"),
			// OfString: openai.String("Using the tool provided, list all pods in the kube-system namespace"),
		},
	}

	resp, err := client.Responses.New(ctx, params)
	if err != nil {
		log.Fatalln(err.Error())
	}
	log.Println(resp.OutputText())
}
