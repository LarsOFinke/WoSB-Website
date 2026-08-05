#!/usr/bin/env python3
"""Synchronize documentation templates from the language-neutral webhook catalog."""
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; SOURCE=ROOT/'contracts/webhook-events.json'
def main():
    payload=json.loads(SOURCE.read_text()); events=payload.get('events')
    if payload.get('schema_version')!=1 or not isinstance(events,list):raise SystemExit('Invalid webhook contract')
    keys=[row.get('key') for row in events]
    if any(not key for key in keys) or len(keys)!=len(set(keys)):raise SystemExit('Webhook keys must be unique')
    directory=ROOT/'docs/integrations/webhook-templates/message-templates'; directory.mkdir(parents=True,exist_ok=True)
    expected={f'{key}.txt' for key in keys}
    for stale in directory.glob('*.txt'):
        if stale.name not in expected:stale.unlink()
    sections=['# Discord webhook message templates','','Generated from `contracts/webhook-events.json`.']
    for row in sorted(events,key=lambda item:item['key']):
        message=str(row['default_message']).strip(); (directory/f"{row['key']}.txt").write_text(message+'\n')
        sections += ['',f"## `{row['key']}`",'',str(row.get('description') or ''),'','```text',message,'```']
    target=ROOT/'docs/integrations/webhook-templates/all-message-templates.md'; content='\n'.join(sections)+'\n'
    if '--check' in sys.argv:
        if not target.is_file() or target.read_text()!=content:raise SystemExit('Webhook templates are stale')
    else:target.parent.mkdir(parents=True,exist_ok=True);target.write_text(content)
if __name__=='__main__':main()
