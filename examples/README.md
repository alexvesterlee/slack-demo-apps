# Examples

Starter files you **copy and edit** for your own demo — reference patterns, not
production tools.

| File | What it is |
|---|---|
| `send_messages.example.json` | A sample message config: a list of DMs/messages to send as different personas. Copy it to your own file (e.g. `my_demo.json` at the repo root) and edit the `sender_email` / `channel` / `text` fields. |

The scripts that consume these configs live in [`../scripts/`](../scripts):
`send_dms_as_users.py` (send), `send_thread.py` (threaded conversations), and
`delete_dms.py` (clean up from a manifest).

## Usage

```bash
# 1. Copy the example config and edit it for your demo
cp examples/send_messages.example.json my_demo.json

# 2. Send (writes a sent.json manifest for later cleanup)
python scripts/send_dms_as_users.py --config my_demo.json --manifest sent.json

# 3. Later, tear it down
python scripts/delete_dms.py --manifest sent.json
```

## The probe-and-delete trick (background)

Worth knowing if you write your own delete logic. A persona's user token has
`chat:write` but **not** `im:read` or `im:write`, so it cannot call
`conversations.open` / `im.list` to find a DM channel ID — yet `chat.delete`
needs both `channel` and `ts`.

Workaround: post a one-character throwaway message via `chat.postMessage` with
`channel=<recipient_user_id>`. Slack auto-resolves the DM channel and returns its
ID, then you `chat.delete` both the throwaway and the real target. See
`scripts/delete_dms.py` for the implementation.
