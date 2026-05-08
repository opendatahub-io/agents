# Contributing

## Developing plugins

Plugins live in `agent-plugins/<plugin-name>/`. To work on one:

```bash
export PLUGIN=<your-plugin>
```

and then:

```bash
claude --plugin-dir ./agent-plugins/$PLUGIN
```

Edits go live. Run `/reload-plugins` inside Claude Code to pick them up.

### Adding a new plugin

1. Create `agent-plugins/<new-plugin>/.claude-plugin/plugin.json` with `name`, `description`, `version`.
2. Add `skills/`, `agents/`, etc. at the plugin root (not inside `.claude-plugin/`).
3. Add an entry to `agent-plugins/.claude-plugin/marketplace.json` with `"source": "./<new-plugin>"`.

### Notes

- Use a regular terminal. Claude Code UIs such as the VS Code plugin do not support `--plugin-dir`.
- Don't try to load via `.claude/settings.json` and `enabledPlugins`. That path uses the plugin cache and your edits won't propagate.

## Releasing

Bump `version` in the plugin's `plugin.json`, push, and tell consumers to run `/plugin marketplace update` then `/plugin update <plugin>@<marketplace>`.